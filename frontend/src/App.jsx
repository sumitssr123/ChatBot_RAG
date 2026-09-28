import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const [messages, setMessages] = useState([]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [isLoadingAnswer, setIsLoadingAnswer] = useState(false);

  const messagesEndRef = useRef(null);

  // Auto-scroll chat area to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoadingAnswer]);

  // Handle PDF file selection & upload
  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      alert('Please upload a PDF file.');
      return;
    }

    setFile(selectedFile);
    setIsUploading(true);
    setUploadStatus('Uploading and indexing document...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setUploadStatus(`Ready: "${data.filename}" (${data.chunks_count} chunks indexed)`);
        setMessages((prev) => [
          ...prev,
          {
            sender: 'bot',
            text: `Document "${data.filename}" is ready! Ask me anything about it.`,
          },
        ]);
      } else {
        setUploadStatus(`Upload failed: ${data.detail || 'Error uploading file'}`);
      }
    } catch (err) {
      setUploadStatus(`Error: ${err.message}. Is the backend running?`);
    } finally {
      setIsUploading(false);
    }
  };

  // Handle sending a question
  const handleSendMessage = async (e) => {
    e.preventDefault();
    const question = inputQuestion.trim();
    if (!question || isLoadingAnswer) return;

    // Add user message to chat
    setMessages((prev) => [...prev, { sender: 'user', text: question }]);
    setInputQuestion('');
    setIsLoadingAnswer(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessages((prev) => [...prev, { sender: 'bot', text: data.answer }]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'bot',
            text: `Error: ${data.detail || 'Could not fetch answer.'}`,
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: `Connection error: ${err.message}. Please check if the backend is running.`,
        },
      ]);
    } finally {
      setIsLoadingAnswer(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <h1>Simple RAG Chatbot</h1>
      </header>

      {/* PDF Upload Section */}
      <section className="upload-section">
        <label className="file-input-label">
          {isUploading ? 'Indexing PDF...' : 'Choose PDF'}
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            disabled={isUploading}
          />
        </label>
        <span className="upload-status">
          {uploadStatus || 'No PDF uploaded yet.'}
        </span>
      </section>

      {/* Chat Area */}
      <section className="chat-window">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <p>Upload a PDF above, then ask questions about its content here.</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.sender}`}>
              <div className="message-bubble">{msg.text}</div>
            </div>
          ))
        )}

        {isLoadingAnswer && (
          <div className="message-row bot">
            <div className="message-bubble thinking">Thinking...</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </section>

      {/* Chat Input Box */}
      <form className="input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          placeholder="Ask a question about the document..."
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          disabled={isLoadingAnswer}
        />
        <button type="submit" disabled={isLoadingAnswer || !inputQuestion.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;

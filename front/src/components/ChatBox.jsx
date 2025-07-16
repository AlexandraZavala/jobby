import React, { useState, useEffect, useRef } from 'react';
import JobCard from './JobCard';
import LoadingSpinner from './LoadingSpinner';
import SuggestedQueries from './SuggestedQueries';
import { searchJobs, chatWithBot } from '../services/api';
import config from '../config/config.js';
import './ChatBox.css';


const ChatBox = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: config.CHAT_CONFIG.welcomeMessage,
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll al final de los mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInputText('');

    try {
      // Primero intentar usar el chatbot inteligente
      if (!config.USE_MOCK_DATA) {
        const chatResponse = await chatWithBot(inputText);
        
        if (chatResponse.success) {
          const botMessage = {
            id: Date.now() + 1,
            type: 'bot',
            content: chatResponse.respuesta,
            jobs: chatResponse.empleos || null, // Incluir empleos si están disponibles
            timestamp: new Date()
          };
          setMessages(prev => [...prev, botMessage]);
          setIsLoading(false);
          return;
        }
      }
      
      // Fallback: usar búsqueda directa de empleos
      const response = await searchJobs(inputText);
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.message,
        jobs: response.jobs,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: config.CHAT_CONFIG.errorMessage,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuerySelect = (query) => {
    setInputText(query);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('es-PE', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Mostrar sugerencias solo si hay pocos mensajes y no está cargando
  const showSuggestions = messages.length <= 2 && !isLoading;

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title">
          <span className="bot-avatar">🤖</span>
          <h2>Jobly - Asistente de Empleos</h2>
        </div>
        <div className="chat-status">En línea</div>
      </div>

      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              <p>{message.content}</p>
              {message.jobs && (
                <div className="jobs-container">
                  {message.jobs.map((job) => (
                    <JobCard key={job.id} job={job} />
                  ))}
                </div>
              )}
            </div>
            <div className="message-time">
              {formatTime(message.timestamp)}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message bot loading-message">
            <div className="message-content">
              <LoadingSpinner />
              <p>{config.CHAT_CONFIG.loadingMessage}</p>
            </div>
          </div>
        )}
        
        <SuggestedQueries 
          onQuerySelect={handleQuerySelect} 
          isVisible={showSuggestions} 
        />
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="input-group">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Escribe qué tipo de trabajo buscas (ej: 'quiero un trabajo de desarrollador frontend')"
            className="chat-input"
            rows="1"
            disabled={isLoading}
            maxLength={config.UI_CONFIG.maxMessageLength}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
        <div className="input-hint">
          Presiona Enter para enviar • {inputText.length}/{config.UI_CONFIG.maxMessageLength} caracteres
        </div>
      </div>
    </div>
  );
};

export default ChatBox;

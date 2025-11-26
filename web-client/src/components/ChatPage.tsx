import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import '../App.css'

interface Message {
  role: 'user' | 'agent' | 'system'
  content: string
  timestamp: string
}

interface ChatResponse {
  session_id: string
  response: string
  timestamp: string
}

const API_URL = '/api'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'system',
      content: 'Welcome to the Pregnancy Companion Agent! Start a conversation by typing below.',
      timestamp: new Date().toISOString()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [userId, setUserId] = useState('test_user_' + Date.now())
  const [error, setError] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    try {
      const response = await axios.post<ChatResponse>(`${API_URL}/chat`, {
        user_id: userId,
        session_id: sessionId || undefined,
        message: input
      })

      if (!sessionId) {
        setSessionId(response.data.session_id)
      }

      const agentMessage: Message = {
        role: 'agent',
        content: response.data.response,
        timestamp: response.data.timestamp
      }

      setMessages(prev => [...prev, agentMessage])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to send message')
      const errorMessage: Message = {
        role: 'system',
        content: `Error: ${err.response?.data?.detail || err.message || 'Failed to send message'}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([{
      role: 'system',
      content: 'Chat cleared. Starting new conversation.',
      timestamp: new Date().toISOString()
    }])
    setSessionId('')
    setUserId('test_user_' + Date.now())
    setError('')
  }

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_URL}/health`)
      const healthMessage: Message = {
        role: 'system',
        content: `API Health Check: ${response.data.status} (v${response.data.version})`,
        timestamp: response.data.timestamp
      }
      setMessages(prev => [...prev, healthMessage])
      setError('')
    } catch (err: any) {
      setError('Health check failed: ' + (err.message || 'Unknown error'))
    }
  }

  return (
    <div className="page-content">
      <div className="chat-container">
        <div className="chat-header">
          <h1>🤰 Pregnancy Companion Agent</h1>
          <div className="session-info">
            <span className="user-id">User: {userId.substring(0, 20)}...</span>
            {sessionId && <span className="session-id">Session: {sessionId.substring(0, 20)}...</span>}
          </div>
          <div className="header-actions">
            <button onClick={checkHealth} className="btn-secondary">
              Check Health
            </button>
            <button onClick={clearChat} className="btn-secondary">
              Clear Chat
            </button>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message message-${msg.role}`}>
              <div className="message-header">
                <span className="message-role">
                  {msg.role === 'user' ? '👤 You' : msg.role === 'agent' ? '🤖 Agent' : 'ℹ️ System'}
                </span>
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="message message-agent">
              <div className="message-header">
                <span className="message-role">🤖 Agent</span>
              </div>
              <div className="message-content typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send)"
            disabled={loading}
            rows={3}
          />
          <button 
            onClick={sendMessage} 
            disabled={loading || !input.trim()}
            className="btn-primary"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>

        <div className="footer">
          <p>🧪 Test Client for Pregnancy Companion Agent API</p>
          <p>API Endpoint: {API_URL}</p>
        </div>
      </div>
    </div>
  )
}

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
  // Load persisted state from localStorage
  const loadPersistedState = () => {
    try {
      const savedMessages = localStorage.getItem('chatMessages')
      const savedSessionId = localStorage.getItem('chatSessionId')
      const savedUserId = localStorage.getItem('chatUserId')
      
      return {
        messages: savedMessages ? JSON.parse(savedMessages) : [
          {
            role: 'system',
            content: 'Welcome to the Pregnancy Companion Agent! Start a conversation by typing below.',
            timestamp: new Date().toISOString()
          }
        ],
        sessionId: savedSessionId || '',
        userId: savedUserId || 'test_user_' + Date.now()
      }
    } catch {
      return {
        messages: [
          {
            role: 'system',
            content: 'Welcome to the Pregnancy Companion Agent! Start a conversation by typing below.',
            timestamp: new Date().toISOString()
          }
        ],
        sessionId: '',
        userId: 'test_user_' + Date.now()
      }
    }
  }

  const persistedState = loadPersistedState()
  const [messages, setMessages] = useState<Message[]>(persistedState.messages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string>(persistedState.sessionId)
  const [userId, setUserId] = useState(persistedState.userId)
  const [error, setError] = useState<string>('')
  const [evaluating, setEvaluating] = useState(false)
  const [evalSuccess, setEvalSuccess] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('chatMessages', JSON.stringify(messages))
  }, [messages])

  useEffect(() => {
    localStorage.setItem('chatSessionId', sessionId)
  }, [sessionId])

  useEffect(() => {
    localStorage.setItem('chatUserId', userId)
  }, [userId])

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
    const newMessages = [{
      role: 'system',
      content: 'Chat cleared. Starting new conversation.',
      timestamp: new Date().toISOString()
    }]
    const newUserId = 'test_user_' + Date.now()
    
    setMessages(newMessages)
    setSessionId('')
    setUserId(newUserId)
    setError('')
    
    // Clear localStorage
    localStorage.setItem('chatMessages', JSON.stringify(newMessages))
    localStorage.setItem('chatSessionId', '')
    localStorage.setItem('chatUserId', newUserId)
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

  const runLiveEvaluation = async () => {
    if (messages.length <= 1) {
      setError('No conversation to evaluate. Send at least one message first.')
      return
    }

    setEvaluating(true)
    setError('')
    setEvalSuccess('')

    try {
      // Extract user-agent conversation pairs (exclude system messages)
      const conversationPairs = []
      for (let i = 0; i < messages.length; i++) {
        if (messages[i].role === 'user' && i + 1 < messages.length && messages[i + 1].role === 'agent') {
          conversationPairs.push({
            user_content: messages[i].content,
            agent_response: messages[i + 1].content
          })
        }
      }

      if (conversationPairs.length === 0) {
        setError('No complete user-agent conversation pairs found to evaluate.')
        return
      }

      const response = await axios.post(`${API_URL}/evaluation/run-live`, {
        session_id: sessionId,
        user_id: userId,
        conversation: conversationPairs
      })
      
      setEvalSuccess(`✅ Evaluation completed! Check the Evaluation page for results.`)
      
      const evalMessage: Message = {
        role: 'system',
        content: `📊 Live Evaluation Completed\n${response.data.message || 'Results available on Evaluation page'}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, evalMessage])
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Evaluation failed'
      setError('Evaluation failed: ' + errorMsg)
      
      const evalMessage: Message = {
        role: 'system',
        content: `❌ Evaluation Failed: ${errorMsg}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, evalMessage])
    } finally {
      setEvaluating(false)
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
            <button 
              onClick={runLiveEvaluation} 
              disabled={evaluating || messages.length <= 1}
              className="btn-secondary"
              style={{ backgroundColor: evaluating ? '#ccc' : '#667eea', color: '#fff' }}
            >
              {evaluating ? '⏳ Evaluating...' : '📊 Run Live Evaluation'}
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

        {evalSuccess && (
          <div className="error-banner" style={{ background: '#d4edda', borderColor: '#c3e6cb', color: '#155724' }}>
            {evalSuccess}
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
          <p>
            <a 
              href="http://localhost:3000/test_eval_api.html" 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ color: '#667eea', textDecoration: 'underline' }}
            >
              🔍 View Live Evaluation API Test (No Cache)
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

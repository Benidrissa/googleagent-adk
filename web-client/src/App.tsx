import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import ChatPage from './components/ChatPage'
import LogsPage from './components/LogsPage'
import EvaluationPage from './components/EvaluationPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/evaluation" element={<EvaluationPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App

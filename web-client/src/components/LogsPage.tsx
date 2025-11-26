import { useState, useEffect } from 'react'
import axios from 'axios'
import '../App.css'

interface LogEntry {
  timestamp: string
  level: string
  message: string
  trace_id?: string
  span_id?: string
  tool_name?: string
  tool_args?: any
  tool_response?: any
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [autoRefresh, setAutoRefresh] = useState(false)

  const fetchLogs = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.get('/api/logs', {
        params: {
          level: levelFilter !== 'all' ? levelFilter : undefined,
          limit: 100
        }
      })
      setLogs(response.data.logs || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch logs')
      setLogs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [levelFilter])

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchLogs, 5000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, levelFilter])

  const filteredLogs = logs.filter(log => 
    filter === '' || 
    log.message.toLowerCase().includes(filter.toLowerCase()) ||
    log.tool_name?.toLowerCase().includes(filter.toLowerCase())
  )

  const getLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR': return '#ff4444'
      case 'WARNING': return '#ffaa00'
      case 'INFO': return '#4CAF50'
      case 'DEBUG': return '#2196F3'
      default: return '#888'
    }
  }

  return (
    <div className="page-content">
      <div className="logs-container">
        <div className="logs-header">
          <h1>📋 Agent Logs</h1>
          <div className="logs-controls">
            <input
              type="text"
              placeholder="Filter logs..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="filter-input"
            />
            <select 
              value={levelFilter} 
              onChange={(e) => setLevelFilter(e.target.value)}
              className="level-select"
            >
              <option value="all">All Levels</option>
              <option value="ERROR">Errors</option>
              <option value="WARNING">Warnings</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>
            <label className="auto-refresh-label">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto-refresh (5s)
            </label>
            <button onClick={fetchLogs} disabled={loading} className="btn-primary">
              {loading ? 'Loading...' : '🔄 Refresh'}
            </button>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        <div className="logs-stats">
          <span>Total Logs: {filteredLogs.length}</span>
          <span>Errors: {filteredLogs.filter(l => l.level === 'ERROR').length}</span>
          <span>Warnings: {filteredLogs.filter(l => l.level === 'WARNING').length}</span>
        </div>

        <div className="logs-list">
          {filteredLogs.length === 0 ? (
            <div className="no-logs">
              <p>No logs found. {filter && 'Try adjusting your filter.'}</p>
            </div>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className="log-entry">
                <div className="log-header">
                  <span 
                    className="log-level" 
                    style={{ backgroundColor: getLevelColor(log.level) }}
                  >
                    {log.level}
                  </span>
                  <span className="log-timestamp">
                    {new Date(log.timestamp).toLocaleString()}
                  </span>
                  {log.trace_id && (
                    <span className="log-trace" title="Trace ID">
                      🔍 {log.trace_id.substring(0, 16)}...
                    </span>
                  )}
                </div>
                <div className="log-message">{log.message}</div>
                {log.tool_name && (
                  <div className="log-tool">
                    <strong>🔧 Tool:</strong> {log.tool_name}
                  </div>
                )}
                {log.tool_args && (
                  <details className="log-details">
                    <summary>Tool Arguments</summary>
                    <pre>{JSON.stringify(log.tool_args, null, 2)}</pre>
                  </details>
                )}
                {log.tool_response && (
                  <details className="log-details">
                    <summary>Tool Response</summary>
                    <pre>{JSON.stringify(log.tool_response, null, 2)}</pre>
                  </details>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

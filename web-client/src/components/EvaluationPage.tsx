import { useState, useEffect } from 'react'
import axios from 'axios'
import '../App.css'

interface EvalCase {
  eval_id: string
  status: 'PASSED' | 'FAILED' | 'NOT_EVALUATED'
  conversation: any[]
  metrics?: {
    tool_trajectory_avg_score?: number
    response_match_score?: number
    rubric_based_tool_use_quality_v1?: number
  }
}

interface EvalResult {
  eval_set_id: string
  timestamp: string
  total_cases: number
  passed: number
  failed: number
  eval_cases: EvalCase[]
}

export default function EvaluationPage() {
  const [evalResults, setEvalResults] = useState<EvalResult[]>([])
  const [expandedRunId, setExpandedRunId] = useState<number | null>(null)
  const [expandedCaseId, setExpandedCaseId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchEvaluationResults = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.get('/api/evaluation/results')
      const results = response.data.results || []
      setEvalResults(results)
      
      // Auto-expand first result if available
      if (results.length > 0) {
        setExpandedRunId(0)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch evaluation results')
      setEvalResults([])
      console.error('Error fetching evaluation results:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvaluationResults()
  }, [])

  const toggleRun = (idx: number) => {
    setExpandedRunId(expandedRunId === idx ? null : idx)
    setExpandedCaseId(null)
  }

  const toggleCase = (caseId: string) => {
    setExpandedCaseId(expandedCaseId === caseId ? null : caseId)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PASSED': return '#4CAF50'
      case 'FAILED': return '#ff4444'
      case 'NOT_EVALUATED': return '#888'
      default: return '#888'
    }
  }

  const getScoreColor = (score: number, threshold: number) => {
    if (score >= threshold) return '#4CAF50'
    if (score >= threshold * 0.8) return '#ffaa00'
    return '#ff4444'
  }

  return (
    <div className="page-content">
      <div className="evaluation-container">
        <div className="evaluation-header">
          <h1>📊 Evaluation Results</h1>
          <div className="evaluation-controls">
            <button onClick={fetchEvaluationResults} disabled={loading} className="btn-primary">
              {loading ? 'Loading...' : '🔄 Refresh'}
            </button>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="no-results">
            <p>⏳ Loading evaluation results...</p>
          </div>
        ) : evalResults.length === 0 ? (
          <div className="no-results">
            <h2>📭 No Evaluations Available</h2>
            <p>No evaluation results have been generated yet.</p>
          </div>
        ) : (
          <div className="accordion-container">
            {evalResults.map((result, idx) => (
              <div key={idx} className="accordion-item">
                <div 
                  className={`accordion-header ${expandedRunId === idx ? 'expanded' : ''}`}
                  onClick={() => toggleRun(idx)}
                >
                  <div className="accordion-title">
                    <span className="accordion-icon">{expandedRunId === idx ? '▼' : '▶'}</span>
                    <strong>{result.eval_set_id}</strong>
                  </div>
                  <div className="accordion-meta">
                    <span className="timestamp">{new Date(result.timestamp).toLocaleString()}</span>
                    <span className="stats">
                      <span className="stat-passed">✓ {result.passed}</span>
                      <span className="stat-failed">✗ {result.failed}</span>
                      <span className="stat-total">Total: {result.total_cases}</span>
                    </span>
                  </div>
                  <div className="progress-bar-container">
                    <div 
                      className="progress-bar"
                      style={{ 
                        width: `${(result.passed / result.total_cases) * 100}%`,
                        backgroundColor: result.passed === result.total_cases ? '#4CAF50' : '#ff4444'
                      }}
                    />
                  </div>
                </div>

                {expandedRunId === idx && (
                  <div className="accordion-content">
                    {result.eval_cases.map((evalCase, caseIdx) => (
                      <div key={caseIdx} className="case-accordion-item">
                        <div 
                          className={`case-accordion-header ${expandedCaseId === evalCase.eval_id ? 'expanded' : ''}`}
                          onClick={() => toggleCase(evalCase.eval_id)}
                        >
                          <div className="case-title">
                            <span className="accordion-icon">{expandedCaseId === evalCase.eval_id ? '▼' : '▶'}</span>
                            <span 
                              className="case-status"
                              style={{ backgroundColor: getStatusColor(evalCase.status) }}
                            >
                              {evalCase.status}
                            </span>
                            <strong>{evalCase.eval_id}</strong>
                          </div>
                          {evalCase.metrics && (
                            <div className="case-metrics-preview">
                              <span 
                                className="metric-preview"
                                style={{ 
                                  color: getScoreColor(
                                    evalCase.metrics.tool_trajectory_avg_score || 0, 
                                    0.9
                                  )
                                }}
                              >
                                Tool: {((evalCase.metrics.tool_trajectory_avg_score || 0) * 100).toFixed(0)}%
                              </span>
                              <span 
                                className="metric-preview"
                                style={{ 
                                  color: getScoreColor(
                                    evalCase.metrics.response_match_score || 0, 
                                    0.75
                                  )
                                }}
                              >
                                Response: {((evalCase.metrics.response_match_score || 0) * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                        </div>

                        {expandedCaseId === evalCase.eval_id && (
                          <div className="case-accordion-content">
                            {evalCase.metrics && (
                              <div className="metrics-section">
                                <h4>📊 Metrics</h4>
                                <div className="metrics-grid">
                                  <div className="metric-card">
                                    <div className="metric-name">Tool Trajectory</div>
                                    <div 
                                      className="metric-score"
                                      style={{ 
                                        color: getScoreColor(
                                          evalCase.metrics.tool_trajectory_avg_score || 0, 
                                          0.9
                                        )
                                      }}
                                    >
                                      {((evalCase.metrics.tool_trajectory_avg_score || 0) * 100).toFixed(1)}%
                                    </div>
                                    <div className="metric-threshold">Threshold: 90%</div>
                                  </div>
                                  <div className="metric-card">
                                    <div className="metric-name">Response Match</div>
                                    <div 
                                      className="metric-score"
                                      style={{ 
                                        color: getScoreColor(
                                          evalCase.metrics.response_match_score || 0, 
                                          0.75
                                        )
                                      }}
                                    >
                                      {((evalCase.metrics.response_match_score || 0) * 100).toFixed(1)}%
                                    </div>
                                    <div className="metric-threshold">Threshold: 75%</div>
                                  </div>
                                  {evalCase.metrics.rubric_based_tool_use_quality_v1 !== undefined && (
                                    <div className="metric-card">
                                      <div className="metric-name">Rubric Quality</div>
                                      <div 
                                        className="metric-score"
                                        style={{ 
                                          color: getScoreColor(
                                            evalCase.metrics.rubric_based_tool_use_quality_v1, 
                                            0.8
                                          )
                                        }}
                                      >
                                        {(evalCase.metrics.rubric_based_tool_use_quality_v1 * 100).toFixed(1)}%
                                      </div>
                                      <div className="metric-threshold">Threshold: 80%</div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {evalCase.conversation.length > 0 && (
                              <div className="conversation-section">
                                <h4>💬 Conversation</h4>
                                <div className="conversation-viewer">
                                  {evalCase.conversation.map((turn: any, turnIdx: number) => (
                                    <div key={turnIdx} className="conversation-turn">
                                      {turn.user_content && (
                                        <div className="turn-message user-turn">
                                          <div className="turn-label">👤 User</div>
                                          <div className="turn-content">{turn.user_content}</div>
                                        </div>
                                      )}
                                      {turn.final_response !== undefined && (
                                        <div className="turn-message agent-turn">
                                          <div className="turn-label">🤖 Agent</div>
                                          <div className="turn-content">
                                            {turn.final_response || <em style={{color: '#888'}}>No response generated</em>}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

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
  const [selectedResult, setSelectedResult] = useState<EvalResult | null>(null)
  const [selectedCase, setSelectedCase] = useState<EvalCase | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchEvaluationResults = async () => {
    setLoading(true)
    setError('')
    try {
      // Try to fetch evaluation results from API
      const response = await axios.get('/api/evaluation/results')
      setEvalResults(response.data.results || [])
    } catch (err: any) {
      // If API endpoint doesn't exist, show sample data
      setError('Evaluation endpoint not yet implemented. Showing sample data.')
      setEvalResults([
        {
          eval_set_id: 'pregnancy_companion_integration_suite',
          timestamp: new Date().toISOString(),
          total_cases: 2,
          passed: 0,
          failed: 2,
          eval_cases: [
            {
              eval_id: 'new_patient_registration',
              status: 'FAILED',
              conversation: [
                {
                  user_content: 'Hello! My name is Amina, phone +221 77 888 9999.',
                  final_response: 'Hello Amina! Your estimated due date is March 22, 2026.'
                }
              ],
              metrics: {
                tool_trajectory_avg_score: 0.0,
                response_match_score: 0.34
              }
            },
            {
              eval_id: 'nutrition_guidance_request',
              status: 'FAILED',
              conversation: [
                {
                  user_content: 'What foods are rich in iron?',
                  final_response: 'Iron-rich foods include leafy greens, beans, and lean meats.'
                }
              ],
              metrics: {
                tool_trajectory_avg_score: 0.0,
                response_match_score: 0.25
              }
            }
          ]
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvaluationResults()
  }, [])

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

        <div className="evaluation-layout">
          {/* Left Panel: Evaluation Runs List */}
          <div className="evaluation-runs">
            <h2>Evaluation Runs</h2>
            {evalResults.length === 0 ? (
              <div className="no-results">
                <p>No evaluation results found.</p>
                <p className="hint">Run: adk eval agent_eval tests/pregnancy_agent_integration.evalset.json</p>
              </div>
            ) : (
              evalResults.map((result, idx) => (
                <div 
                  key={idx} 
                  className={`eval-run-card ${selectedResult === result ? 'selected' : ''}`}
                  onClick={() => setSelectedResult(result)}
                >
                  <div className="eval-run-header">
                    <strong>{result.eval_set_id}</strong>
                    <span className="eval-timestamp">
                      {new Date(result.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="eval-run-stats">
                    <span className="stat-passed">✓ {result.passed}</span>
                    <span className="stat-failed">✗ {result.failed}</span>
                    <span className="stat-total">Total: {result.total_cases}</span>
                  </div>
                  <div className="eval-run-progress">
                    <div 
                      className="progress-bar"
                      style={{ 
                        width: `${(result.passed / result.total_cases) * 100}%`,
                        backgroundColor: result.passed === result.total_cases ? '#4CAF50' : '#ff4444'
                      }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Middle Panel: Test Cases */}
          {selectedResult && (
            <div className="evaluation-cases">
              <h2>Test Cases</h2>
              {selectedResult.eval_cases.map((evalCase, idx) => (
                <div 
                  key={idx} 
                  className={`eval-case-card ${selectedCase === evalCase ? 'selected' : ''}`}
                  onClick={() => setSelectedCase(evalCase)}
                >
                  <div className="eval-case-header">
                    <span 
                      className="eval-status"
                      style={{ backgroundColor: getStatusColor(evalCase.status) }}
                    >
                      {evalCase.status}
                    </span>
                    <strong>{evalCase.eval_id}</strong>
                  </div>
                  {evalCase.metrics && (
                    <div className="eval-metrics-summary">
                      <div className="metric-badge">
                        <span className="metric-label">Tool Score:</span>
                        <span 
                          className="metric-value"
                          style={{ 
                            color: getScoreColor(
                              evalCase.metrics.tool_trajectory_avg_score || 0, 
                              0.9
                            )
                          }}
                        >
                          {((evalCase.metrics.tool_trajectory_avg_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="metric-badge">
                        <span className="metric-label">Response:</span>
                        <span 
                          className="metric-value"
                          style={{ 
                            color: getScoreColor(
                              evalCase.metrics.response_match_score || 0, 
                              0.75
                            )
                          }}
                        >
                          {((evalCase.metrics.response_match_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Right Panel: Case Details */}
          {selectedCase && (
            <div className="evaluation-details">
              <h2>Case Details: {selectedCase.eval_id}</h2>
              
              <div className="detail-section">
                <h3>Status</h3>
                <div 
                  className="status-badge-large"
                  style={{ backgroundColor: getStatusColor(selectedCase.status) }}
                >
                  {selectedCase.status}
                </div>
              </div>

              {selectedCase.metrics && (
                <div className="detail-section">
                  <h3>Metrics</h3>
                  <div className="metrics-grid">
                    <div className="metric-card">
                      <div className="metric-name">Tool Trajectory</div>
                      <div 
                        className="metric-score"
                        style={{ 
                          color: getScoreColor(
                            selectedCase.metrics.tool_trajectory_avg_score || 0, 
                            0.9
                          )
                        }}
                      >
                        {((selectedCase.metrics.tool_trajectory_avg_score || 0) * 100).toFixed(1)}%
                      </div>
                      <div className="metric-threshold">Threshold: 90%</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-name">Response Match</div>
                      <div 
                        className="metric-score"
                        style={{ 
                          color: getScoreColor(
                            selectedCase.metrics.response_match_score || 0, 
                            0.75
                          )
                        }}
                      >
                        {((selectedCase.metrics.response_match_score || 0) * 100).toFixed(1)}%
                      </div>
                      <div className="metric-threshold">Threshold: 75%</div>
                    </div>
                    {selectedCase.metrics.rubric_based_tool_use_quality_v1 !== undefined && (
                      <div className="metric-card">
                        <div className="metric-name">Rubric Quality</div>
                        <div 
                          className="metric-score"
                          style={{ 
                            color: getScoreColor(
                              selectedCase.metrics.rubric_based_tool_use_quality_v1, 
                              0.8
                            )
                          }}
                        >
                          {(selectedCase.metrics.rubric_based_tool_use_quality_v1 * 100).toFixed(1)}%
                        </div>
                        <div className="metric-threshold">Threshold: 80%</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="detail-section">
                <h3>Conversation</h3>
                <div className="conversation-viewer">
                  {selectedCase.conversation.map((turn: any, idx: number) => (
                    <div key={idx} className="conversation-turn">
                      {turn.user_content && (
                        <div className="turn-message user-turn">
                          <div className="turn-label">👤 User</div>
                          <div className="turn-content">{turn.user_content}</div>
                        </div>
                      )}
                      {turn.final_response && (
                        <div className="turn-message agent-turn">
                          <div className="turn-label">🤖 Agent</div>
                          <div className="turn-content">{turn.final_response}</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

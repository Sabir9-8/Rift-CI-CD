import React, { createContext, useContext, useState, useCallback, useRef } from 'react'
import axios from 'axios'

const AgentContext = createContext(null)

export const useAgent = () => {
  const context = useContext(AgentContext)
  if (!context) {
    throw new Error('useAgent must be used within an AgentProvider')
  }
  return context
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3002',
  timeout: 600000,
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED') console.error('Request timeout')
    return Promise.reject(error)
  }
)

const AgentProvider = ({ children }) => {
  // Token is optional - will use gh CLI if not provided
  // OpenAI / Gemini key is optional - deterministic AST fixes used if not provided

  const [config, setConfig] = useState({
    repoUrl: '',
    teamName: '',
    leaderName: '',
    token: '',       // Optional
    openaiKey: '',   // Optional
    geminiKey: ''    // Optional (Free Google AI Studio key)
  })

  const [status, setStatus] = useState('idle')
  const [currentStep, setCurrentStep] = useState('')
  const [results, setResults] = useState(null)
  const [errors, setErrors] = useState([])
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)
  const [startTime, setStartTime] = useState(null)
  const [endTime, setEndTime] = useState(null)
  const [branchName, setBranchName] = useState('')
  const [cicdRuns, setCicdRuns] = useState([])

  const updateConfig = useCallback((updates) => {
    setConfig(prev => ({ ...prev, ...updates }))
  }, [])

  /** Sanitise name strictly according to RIFT specifications */
  const sanitiseName = (s) =>
    s.trim().toUpperCase().replace(/\s+/g, '_').replace(/[^A-Z0-9_]/g, '')

  const runAgent = useCallback(async () => {
    if (!config.repoUrl || !config.teamName || !config.leaderName) {
      setError('Please fill in all required fields')
      return
    }

    const t = sanitiseName(config.teamName)
    const l = sanitiseName(config.leaderName)
    const expectedBranch = `${t}_${l}_AI_Fix`
    setBranchName(expectedBranch)

    const now = Date.now()
    setStartTime(now)
    setEndTime(null)
    setStatus('running')
    setError(null)
    setResults(null)
    setErrors([])
    setCicdRuns([])
    setCurrentStep('Multi-Agent Orchestrator initialized...')

    try {
      const response = await api.post('/api/run-agent', {
        repoUrl: config.repoUrl,
        teamName: config.teamName,
        leaderName: config.leaderName,
        token: config.token,
        openaiKey: config.openaiKey,
        geminiKey: config.geminiKey
      })

      const finished = Date.now()
      setEndTime(finished)
      setResults(response.data)

      const appliedFixes = response.data.fixes || []
      setErrors(appliedFixes)
      if (response.data.branchName) {
        setBranchName(response.data.branchName)
      }

      // Populate real CI/CD timeline runs from backend
      const rawTimeline = response.data.ciCdTimeline || []
      if (rawTimeline.length > 0) {
        setCicdRuns(rawTimeline.map((item, idx) => ({
          id: item.iteration || idx + 1,
          timestamp: item.timestamp || new Date().toLocaleTimeString(),
          status: item.status || 'passed',
          iteration: item.iteration || idx + 1,
          maxIterations: item.max_iterations || 5
        })))
      } else {
        // Fallback single run if tests succeeded on pass 1
        setCicdRuns([{
          id: 1,
          timestamp: new Date().toLocaleTimeString(),
          status: response.data.success !== false ? 'passed' : 'failed',
          iteration: 1,
          maxIterations: 5
        }])
      }

      setStatus('success')
      setCurrentStep('Analysis and healing completed!')

      setHistory(prev => [{
        id: finished,
        repoUrl: config.repoUrl,
        timestamp: new Date().toLocaleString(),
        errorsDetected: response.data.errorsDetected || 0,
        fixesApplied: response.data.fixesApplied || 0,
        prNumber: response.data.prCreated,
        status: response.data.success !== false ? 'success' : 'failed'
      }, ...prev])

    } catch (err) {
      const finished = Date.now()
      setEndTime(finished)

      let errorMessage = 'An error occurred'
      if (err.response) errorMessage = err.response.data?.message || err.message
      else if (err.request) errorMessage = 'No response from server. Make sure the backend is running.'
      else errorMessage = err.message

      setError(errorMessage)
      setStatus('error')

      setHistory(prev => [{
        id: finished,
        repoUrl: config.repoUrl,
        timestamp: new Date().toLocaleString(),
        errorsDetected: 0,
        fixesApplied: 0,
        prNumber: null,
        status: 'error'
      }, ...prev])
    }
  }, [config])

  const clearResults = useCallback(() => {
    setResults(null)
    setErrors([])
    setStatus('idle')
    setCurrentStep('')
    setError(null)
    setCicdRuns([])
    setEndTime(null)
  }, [])

  const value = {
    config, updateConfig,
    status, currentStep,
    results, errors,
    history, error,
    startTime, endTime,
    branchName,
    cicdRuns,
    runAgent, clearResults
  }

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  )
}

export { AgentProvider }

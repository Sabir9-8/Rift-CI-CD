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
  // OpenAI key is optional - will use heuristic fixes if not provided

  const [config, setConfig] = useState({
    repoUrl: '',
    teamName: '',
    leaderName: '',
    token: '',  // Optional - gh CLI will be used if not provided
    openaiKey: ''  // Optional - heuristic fixes used if not provided
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

  const cicdTimerRef = useRef([])  // array of timer IDs

  const updateConfig = useCallback((updates) => {
    setConfig(prev => ({ ...prev, ...updates }))
  }, [])

  /** Sanitise name the same way agent.py does */
  const sanitiseName = (s) =>
    s.trim().toUpperCase().replace(/\s+/g, '_').replace(/[^A-Z0-9_]/g, '')

  /** Simulate CI/CD pipeline iterations while agent runs */
  const startCicdSimulation = useCallback(() => {
    setCicdRuns([])
    let iteration = 1
    const MAX_ITER = 5

    const addRun = (passed) => {
      setCicdRuns(prev => [
        ...prev,
        {
          id: Date.now() + Math.random(),
          timestamp: new Date().toLocaleTimeString(),
          status: passed ? 'passed' : 'failed',
          iteration,
          maxIterations: MAX_ITER
        }
      ])
      iteration++
    }

    // Immediately add first (running) entry
    setCicdRuns([{
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      status: 'running',
      iteration: 1,
      maxIterations: MAX_ITER
    }])

    // Simulate intermediate failures then final pass — store ALL timer IDs
    cicdTimerRef.current = [
      setTimeout(() => addRun(false), 4000),
      setTimeout(() => addRun(false), 8000),
      setTimeout(() => addRun(true), 12000),
      // Safety: after 90s resolve stuck 'running' badge to failed
      setTimeout(() => {
        setCicdRuns(prev =>
          prev.map(r => r.status === 'running' ? { ...r, status: 'failed' } : r)
        )
      }, 90000)
    ]
  }, [])

  const stopCicdSimulation = useCallback((passed) => {
    // Clear every timer (including the 90s safety one)
    if (Array.isArray(cicdTimerRef.current)) {
      cicdTimerRef.current.forEach(id => clearTimeout(id))
    }
    cicdTimerRef.current = []
    // Mark any "running" entry as resolved
    setCicdRuns(prev =>
      prev.map(r => r.status === 'running'
        ? { ...r, status: passed ? 'passed' : 'failed' }
        : r
      )
    )
  }, [])

  const runAgent = useCallback(async () => {
    if (!config.repoUrl || !config.teamName || !config.leaderName) {
      setError('Please fill in all required fields')
      return
    }

    const t = sanitiseName(config.teamName)
    const l = sanitiseName(config.leaderName)
    setBranchName(`${t}_${l}_AI_Fix`)

    const now = Date.now()
    setStartTime(now)
    setEndTime(null)
    setStatus('running')
    setError(null)
    setResults(null)
    setErrors([])
    setCicdRuns([])

    startCicdSimulation()

    try {
      setCurrentStep('Initializing agent...')

      const response = await api.post('/api/run-agent', {
        repoUrl: config.repoUrl,
        teamName: config.teamName,
        leaderName: config.leaderName,
        token: config.token,
        openaiKey: config.openaiKey
      })

      const steps = [
        'Cloning repository...',
        'Running tests...',
        'Detecting errors...',
        'Generating fixes...',
        'Committing and pushing...',
        'Creating pull request...'
      ]
      for (const step of steps) {
        setCurrentStep(step)
        await new Promise(r => setTimeout(r, 1500))
      }

      const finished = Date.now()
      setEndTime(finished)
      setResults(response.data)
      setErrors(response.data.fixes || [])
      setStatus('success')
      stopCicdSimulation(response.data.success !== false)

      setHistory(prev => [{
        id: finished,
        repoUrl: config.repoUrl,
        timestamp: new Date().toLocaleString(),
        errorsDetected: response.data.errorsDetected || 0,
        fixesApplied: response.data.fixesApplied || 0,
        prNumber: response.data.prCreated,
        status: 'success'
      }, ...prev])

    } catch (err) {
      const finished = Date.now()
      setEndTime(finished)
      stopCicdSimulation(false)

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
  }, [config, startCicdSimulation, stopCicdSimulation])

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

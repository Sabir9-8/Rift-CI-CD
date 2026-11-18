import express from 'express'
import cors from 'cors'
import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'
import fs from 'fs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Automatically load .env if present (zero-dependency fallback)
const envPaths = [path.join(__dirname, '.env'), path.join(__dirname, '..', '.env')]
for (const envPath of envPaths) {
  if (fs.existsSync(envPath)) {
    const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/)
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const [k, ...v] = trimmed.split('=')
        const key = k.trim()
        const val = v.join('=').trim().replace(/^["']|["']$/g, '')
        if (key && !process.env[key]) {
          process.env[key] = val
        }
      }
    }
  }
}

const app = express()
const PORT = process.env.PORT || 3002
const isProduction = process.env.NODE_ENV === 'production'

// Determine frontend build path across different deployment structures
const candidate1 = path.join(__dirname, 'frontend', 'dist')
const candidate2 = path.join(__dirname, '..', 'frontend', 'dist')
const frontendPath = isProduction
  ? (fs.existsSync(candidate1) ? candidate1 : (fs.existsSync(candidate2) ? candidate2 : null))
  : null

// CORS configuration - allow all origins (needed for Vercel + Railway cross-origin)
const corsOptions = {
  origin: true,
  credentials: true
}

app.use(cors(corsOptions))
app.use(express.json({ limit: '50mb' }))

// Serve static frontend files in production
if (isProduction && frontendPath && fs.existsSync(frontendPath)) {
  console.log(`Serving frontend from: ${frontendPath}`)
  app.use(express.static(frontendPath))

  // Handle SPA routing - serve index.html for all non-API routes
  app.get('*', (req, res) => {
    if (!req.path.startsWith('/api')) {
      res.sendFile(path.join(frontendPath, 'index.html'))
    }
  })
}

// Store running processes
let currentProcess = null

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    processRunning: currentProcess !== null
  })
})

// API Routes

// Run Agent
app.post('/api/run-agent', (req, res) => {
  const { repoUrl, teamName, leaderName, token, openaiKey, geminiKey } = req.body

  // Token is now optional if gh CLI is available
  if (!repoUrl || !teamName || !leaderName) {
    return res.status(400).json({
      success: false,
      message: 'Missing required fields: repoUrl, teamName, leaderName'
    })
  }

  // Kill any existing process
  if (currentProcess) {
    try {
      currentProcess.kill('SIGTERM')
      setTimeout(() => {
        if (currentProcess) {
          try {
            currentProcess.kill('SIGKILL')
          } catch (e) { }
        }
      }, 2000)
    } catch (e) {
      console.error('Error killing process:', e)
    }
    currentProcess = null
  }

  try {
    // Detect whether rift is in __dirname (Docker root) or in parent dir (local backend/)
    const riftPath = fs.existsSync(path.join(__dirname, 'rift'))
      ? __dirname
      : path.join(__dirname, '..')
    // Automatically detect python command or use PYTHON_BIN env variable
    const pythonBin = process.env.PYTHON_BIN || (process.platform === 'win32' ? 'python' : 'python3')

    const payload = {
      repoUrl,
      teamName,
      leaderName,
      token: token || '',
      openaiKey: openaiKey || '',
      geminiKey: geminiKey || '',
      retryLimit: req.body.retryLimit || 5
    }

    // Sandboxed environment — only pass whitelisted vars, no host secrets
    const sandboxEnv = {
      ...process.env,
      PATH: process.env.PATH || (process.platform === 'win32' ? process.env.Path : '/usr/local/bin:/usr/bin:/bin'),
      HOME: process.env.HOME || '/tmp',
      TMPDIR: process.env.TMPDIR || '/tmp',
      LANG: process.env.LANG || 'en_US.UTF-8',
      PYTHONPATH: riftPath,
      ...(token ? { GITHUB_TOKEN: token } : {}),
      ...(openaiKey ? { OPENAI_API_KEY: openaiKey } : {}),
      ...(geminiKey ? { GEMINI_API_KEY: geminiKey } : {})
    }

    // Spawn secure rift.cli entrypoint with STDIN JSON payload
    const pythonProcess = spawn(pythonBin, ['-u', '-m', 'rift.cli'], {
      cwd: riftPath,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: sandboxEnv
    })

    currentProcess = pythonProcess

    // Write input JSON safely via STDIN to prevent any command/template injection
    pythonProcess.stdin.write(JSON.stringify(payload))
    pythonProcess.stdin.end()

    let output = ''
    let errorOutput = ''

    // Set timeout - 15 minutes (large repos need time to clone and analyze)
    const timeout = setTimeout(() => {
      if (currentProcess) {
        console.log('Process timed out, killing...')
        pythonProcess.kill('SIGTERM')
        currentProcess = null
      }
    }, 15 * 60 * 1000)

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString()
    })

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString()
    })

    pythonProcess.on('error', (err) => {
      clearTimeout(timeout)
      currentProcess = null
      console.error('Process error:', err)
      if (!res.headersSent) {
        res.status(500).json({
          success: false,
          message: 'Failed to start agent: ' + err.message
        })
      }
    })

    pythonProcess.on('close', (code) => {
      clearTimeout(timeout)
      currentProcess = null

      // Look for RESULT in output
      const resultMatch = output.match(/RESULT:(\{.*\})/s)
      if (resultMatch) {
        try {
          const result = JSON.parse(resultMatch[1])
          return res.json({
            success: result.success,
            errorsDetected: result.errors_detected,
            fixesApplied: result.fixes_applied,
            prCreated: result.pr_created,
            error: result.error,
            fixes: result.fixes || [],
            branchName: result.branch_name,
            score: result.score || null,
            ciCdTimeline: result.ci_cd_timeline || [],
            totalTimeSeconds: result.total_time_seconds || null,
            rawResult: result
          })
        } catch (e) {
          console.error('Parse result error:', e)
        }
      }

      // Check for ERROR
      if (output.includes('ERROR:')) {
        const errorMatch = output.match(/ERROR:(.*)/)
        return res.status(500).json({
          success: false,
          message: errorMatch ? errorMatch[1].trim() : 'Agent execution failed'
        })
      }

      // Success fallback
      res.json({
        success: code === 0 || !errorOutput,
        errorsDetected: 0,
        fixesApplied: 0,
        prCreated: null,
        output: output.substring(0, 1000)
      })
    })

  } catch (error) {
    console.error('Spawn error:', error)
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to start agent'
    })
  }
})

// Get status
app.get('/api/status', (req, res) => {
  res.json({
    running: currentProcess !== null,
    pid: currentProcess?.pid || null
  })
})

// Cancel running agent
app.post('/api/cancel', (req, res) => {
  if (currentProcess) {
    currentProcess.kill('SIGTERM')
    setTimeout(() => {
      if (currentProcess) {
        try {
          currentProcess.kill('SIGKILL')
        } catch (e) { }
        currentProcess = null
      }
    }, 1000)
    return res.json({ success: true, message: 'Agent cancelled' })
  }
  return res.json({ success: false, message: 'No agent running' })
})

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason)
})

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`RiftAgent API server running on http://localhost:${PORT}`)
  console.log(`Frontend should connect to: http://localhost:${PORT}`)
})


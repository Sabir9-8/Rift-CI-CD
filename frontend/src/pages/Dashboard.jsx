import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play, CheckCircle, XCircle, Clock, GitBranch, FileCode,
  Sparkles, RefreshCw, ExternalLink, AlertCircle, Trophy,
  Zap, Target, TrendingUp, Activity, Link, Users, Timer,
  ShieldCheck, ShieldX, BarChart2
} from 'lucide-react'
import { useAgent } from '../context/AgentContext'

/* ─── helpers ─────────────────────────────────────────────────── */
const fmtElapsed = (ms) => {
  if (!ms || ms < 0) return '—'
  const totalSec = Math.floor(ms / 1000)
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

const BUG_COLORS = {
  LINTING: '#d29922',
  SYNTAX: '#f85149',
  LOGIC: '#58a6ff',
  TYPE_ERROR: '#e879f9',
  IMPORT: '#fb923c',
  INDENTATION: '#34d399',
}

const bugColor = (type) => BUG_COLORS[(type || '').toUpperCase()] || '#94a3b8'

/* ─── sub-components ──────────────────────────────────────────── */

/** ① Run Summary Card */
const RunSummaryCard = ({ config, results, branchName, startTime, endTime, cicdPassed }) => {
  const elapsed = endTime && startTime ? endTime - startTime : null

  const rows = [
    { icon: <Link size={15} />, label: 'Repository URL', value: config.repoUrl || '—' },
    { icon: <Users size={15} />, label: 'Team / Leader', value: config.teamName && config.leaderName ? `${config.teamName} / ${config.leaderName}` : '—' },
    { icon: <GitBranch size={15} />, label: 'Branch Created', value: branchName || '—' },
    { icon: <AlertCircle size={15} />, label: 'Failures Detected', value: results?.errorsDetected ?? '—' },
    { icon: <Sparkles size={15} />, label: 'Fixes Applied', value: results?.fixesApplied ?? '—' },
    { icon: <Timer size={15} />, label: 'Time Taken', value: fmtElapsed(elapsed) },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 16,
        padding: '1.5rem',
        marginBottom: '1.5rem'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h3 style={{ margin: 0, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
          <Activity size={18} style={{ color: '#58a6ff' }} /> Run Summary
        </h3>
        {cicdPassed !== null && (
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '4px 14px', borderRadius: 999, fontWeight: 700,
            fontSize: '0.78rem', letterSpacing: '0.05em',
            background: cicdPassed ? 'rgba(34,197,94,0.15)' : 'rgba(248,81,73,0.15)',
            border: `1px solid ${cicdPassed ? '#22c55e' : '#f85149'}`,
            color: cicdPassed ? '#22c55e' : '#f85149'
          }}>
            {cicdPassed ? <ShieldCheck size={14} /> : <ShieldX size={14} />}
            CI/CD {cicdPassed ? 'PASSED' : 'FAILED'}
          </span>
        )}
      </div>

      <div className="summary-grid">
        {rows.map(({ icon, label, value }) => (
          <div key={label} style={{
            background: 'rgba(0,0,0,0.25)', borderRadius: 10,
            padding: '0.75rem 1rem', display: 'flex', alignItems: 'flex-start', gap: 10
          }}>
            <span style={{ color: '#58a6ff', marginTop: 2, flexShrink: 0 }}>{icon}</span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: '0.7rem', color: '#8b949e', marginBottom: 2 }}>{label}</div>
              <div style={{
                fontWeight: 600, fontSize: '0.85rem', color: '#e6edf3',
                wordBreak: 'break-all', fontFamily: label === 'Repository URL' || label === 'Branch Created' ? 'monospace' : 'inherit'
              }}>
                {value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

/** ② Score Breakdown Panel */
const ScorePanel = ({ results, startTime, endTime }) => {
  const elapsed = endTime && startTime ? (endTime - startTime) / 60000 : 0
  const fixCount = results?.fixesApplied ?? 0
  const speedBonus = elapsed < 5 ? 10 : 0
  const overCommits = Math.max(0, fixCount - 20)
  const penalty = overCommits * 2
  const final = Math.max(0, 100 + speedBonus - penalty)
  const pct = Math.min(100, (final / 110) * 100)

  const items = [
    { icon: <Target size={16} />, label: 'Base Score', value: '+100', color: '#58a6ff' },
    { icon: <Zap size={16} />, label: `Speed Bonus (${elapsed.toFixed(1)}m)`, value: `+${speedBonus}`, color: speedBonus > 0 ? '#22c55e' : '#8b949e' },
    { icon: <TrendingUp size={16} />, label: `Efficiency Penalty (${fixCount} commits)`, value: penalty > 0 ? `-${penalty}` : '0', color: penalty > 0 ? '#f85149' : '#22c55e' },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 }}
      style={{
        background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(147,51,234,0.1))',
        border: '1px solid rgba(99,102,241,0.3)',
        borderRadius: 16,
        padding: '1.5rem',
        marginBottom: '1.5rem'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1.25rem' }}>
        <Trophy size={20} style={{ color: '#fbbf24' }} />
        <h3 style={{ margin: 0, fontSize: '1rem' }}>Score Breakdown</h3>
      </div>

      {/* Big score number */}
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <div style={{
          fontSize: 'clamp(2.5rem, 8vw, 4.5rem)', fontWeight: 900, lineHeight: 1,
          background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
        }}>
          {final}
        </div>
        <div style={{ color: '#8b949e', fontSize: '0.8rem', marginTop: 4 }}>out of 110 pts</div>
      </div>

      {/* Breakdown grid */}
      <div className="score-grid">
        {items.map(({ icon, label, value, color }) => (
          <div key={label} style={{
            background: 'rgba(0,0,0,0.3)', borderRadius: 10,
            padding: '0.75rem', textAlign: 'center'
          }}>
            <div style={{ color, marginBottom: 4 }}>{icon}</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: '0.65rem', color: '#8b949e', marginTop: 2 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#8b949e', marginBottom: 6 }}>
          <span>Score progress</span>
          <span>{final}/110</span>
        </div>
        <div style={{ height: 10, background: 'rgba(0,0,0,0.4)', borderRadius: 5, overflow: 'hidden' }}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            style={{
              height: '100%',
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
              borderRadius: 5
            }}
          />
        </div>

        {/* Segment markers */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: '#8b949e', marginTop: 4 }}>
          <span>0</span>
          <span>Base 100</span>
          <span>Max 110</span>
        </div>
      </div>
    </motion.div>
  )
}

/** ③ Fixes Applied Table */
const FixesTable = ({ errors }) => {
  if (!errors || errors.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      style={{ marginBottom: '1.5rem' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1rem' }}>
        <BarChart2 size={18} style={{ color: '#58a6ff' }} />
        <h3 style={{ margin: 0, fontSize: '1rem' }}>Fixes Applied</h3>
        <span style={{
          marginLeft: 'auto', background: 'rgba(59,130,246,0.15)',
          border: '1px solid rgba(59,130,246,0.3)', borderRadius: 999,
          padding: '2px 10px', fontSize: '0.75rem', color: '#58a6ff'
        }}>
          {errors.length} total
        </span>
      </div>

      <div style={{ overflowX: 'auto', borderRadius: 12, border: '1px solid rgba(255,255,255,0.08)', WebkitOverflowScrolling: 'touch' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.4)' }}>
              {['File', 'Bug Type', 'Line', 'Commit Message', 'Status'].map(h => (
                <th key={h} style={{
                  padding: '10px 14px', textAlign: 'left', fontWeight: 600,
                  color: '#8b949e', whiteSpace: 'nowrap',
                  borderBottom: '1px solid rgba(255,255,255,0.08)'
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {errors.map((err, idx) => {
              const type = (err.bug_type || 'LOGIC').toUpperCase()
              const fixed = err.status !== 'FAILED' // treat any non-FAILED as fixed
              const commit = `AI-FIX: ${type} at line ${err.line || '?'}`
              return (
                <tr
                  key={idx}
                  style={{
                    background: idx % 2 === 0 ? 'rgba(0,0,0,0.15)' : 'transparent',
                    borderBottom: '1px solid rgba(255,255,255,0.04)',
                    transition: 'background 0.15s'
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(59,130,246,0.07)'}
                  onMouseLeave={e => e.currentTarget.style.background = idx % 2 === 0 ? 'rgba(0,0,0,0.15)' : 'transparent'}
                >
                  <td style={{ padding: '10px 14px', color: '#e6edf3', fontFamily: 'monospace', fontSize: '0.75rem', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {err.file || '—'}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      background: `${bugColor(type)}22`,
                      border: `1px solid ${bugColor(type)}66`,
                      color: bugColor(type),
                      borderRadius: 6, padding: '2px 8px',
                      fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.04em'
                    }}>
                      {type}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px', color: '#8b949e', fontFamily: 'monospace' }}>
                    {err.line || '—'}
                  </td>
                  <td style={{ padding: '10px 14px', color: '#c9d1d9', fontFamily: 'monospace', fontSize: '0.72rem', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {commit}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 5,
                      fontWeight: 700, fontSize: '0.78rem',
                      color: fixed ? '#22c55e' : '#f85149'
                    }}>
                      {fixed ? <CheckCircle size={13} /> : <XCircle size={13} />}
                      {fixed ? 'Fixed' : 'Failed'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}

/** ④ CI/CD Status Timeline */
const CicdTimeline = ({ cicdRuns }) => {
  if (!cicdRuns || cicdRuns.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      style={{
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 16,
        padding: '1.5rem',
        marginBottom: '1.5rem'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1.25rem' }}>
        <Activity size={18} style={{ color: '#58a6ff' }} />
        <h3 style={{ margin: 0, fontSize: '1rem' }}>CI/CD Status Timeline</h3>
        <span style={{
          marginLeft: 'auto', background: 'rgba(139,92,246,0.15)',
          border: '1px solid rgba(139,92,246,0.3)', borderRadius: 999,
          padding: '2px 10px', fontSize: '0.75rem', color: '#a78bfa'
        }}>
          {cicdRuns.length}/{cicdRuns[0]?.maxIterations || 5} runs
        </span>
      </div>

      <div style={{ position: 'relative', paddingLeft: 28 }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: 8, top: 8,
          width: 2, bottom: 8,
          background: 'linear-gradient(to bottom, #3b82f6, #8b5cf6)',
          borderRadius: 2, opacity: 0.4
        }} />

        <AnimatePresence>
          {cicdRuns.map((run, idx) => {
            const isPass = run.status === 'passed'
            const isRun = run.status === 'running'
            const color = isRun ? '#fbbf24' : isPass ? '#22c55e' : '#f85149'

            return (
              <motion.div
                key={run.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.12 }}
                style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, position: 'relative' }}
              >
                {/* Dot */}
                <div style={{
                  position: 'absolute', left: -20,
                  width: 12, height: 12, borderRadius: '50%',
                  background: color, boxShadow: `0 0 8px ${color}`,
                  flexShrink: 0
                }} />

                <div className="timeline-row" style={{ border: `1px solid ${color}33` }}>
                  {/* Badge */}
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                    background: `${color}22`, border: `1px solid ${color}66`,
                    color, borderRadius: 6, padding: '3px 10px',
                    fontWeight: 700, fontSize: '0.72rem', letterSpacing: '0.05em',
                    minWidth: 80, justifyContent: 'center'
                  }}>
                    {isRun
                      ? <><div style={{ width: 8, height: 8, borderRadius: '50%', background: '#fbbf24', animation: 'pulse 1s infinite' }} /> RUNNING</>
                      : isPass
                        ? <><ShieldCheck size={12} /> PASSED</>
                        : <><ShieldX size={12} /> FAILED</>
                    }
                  </span>

                  {/* Iteration */}
                  <span style={{ fontSize: '0.78rem', color: '#8b949e' }}>
                    Iteration <strong style={{ color: '#c9d1d9' }}>{run.iteration}/{run.maxIterations}</strong>
                  </span>

                  {/* Timestamp */}
                  <span className="timeline-timestamp">
                    <Clock size={11} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                    {run.timestamp}
                  </span>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

/* ─── Main Dashboard ──────────────────────────────────────────── */
const Dashboard = () => {
  const {
    config, updateConfig,
    status, currentStep,
    results, errors,
    history, error: agentError,
    runAgent, clearResults,
    startTime, endTime,
    branchName, cicdRuns
  } = useAgent()

  const getStatusBadge = () => {
    const map = {
      idle: { cls: 'status-idle', text: 'Ready' },
      running: { cls: 'status-running', text: 'Running' },
      success: { cls: 'status-success', text: 'Completed' },
      error: { cls: 'status-error', text: 'Error' }
    }
    return map[status] || map.idle
  }

  const statusBadge = getStatusBadge()
  const cicdPassed = results ? results.success !== false : null
  const showResults = status === 'success' && results

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Agent Dashboard</h1>
        <p>Configure and run the AI agent to fix bugs in your repository</p>
      </div>

      <div className="dashboard-grid">
        {/* ── Configuration Form ── */}
        <motion.div className="form-card" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
          <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Configuration</h2>

          <div className="form-group">
            <label>Repository URL *</label>
            <input
              type="text"
              placeholder="https://github.com/owner/repo"
              value={config.repoUrl}
              onChange={e => updateConfig({ repoUrl: e.target.value })}
              disabled={status === 'running'}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Team Name *</label>
              <input
                type="text"
                placeholder="TEAM_A"
                value={config.teamName}
                onChange={e => updateConfig({ teamName: e.target.value })}
                disabled={status === 'running'}
              />
            </div>
            <div className="form-group">
              <label>Leader Name *</label>
              <input
                type="text"
                placeholder="JOHN"
                value={config.leaderName}
                onChange={e => updateConfig({ leaderName: e.target.value })}
                disabled={status === 'running'}
              />
            </div>
          </div>

          <button
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1rem' }}
            onClick={runAgent}
            disabled={status === 'running'}
          >
            {status === 'running'
              ? <>Running...</>
              : <><Play size={18} style={{ marginRight: 8 }} /> Run Agent</>}
          </button>

          {status !== 'idle' && (
            <button
              className="btn btn-secondary"
              style={{ width: '100%', marginTop: '0.75rem' }}
              onClick={clearResults}
            >
              <RefreshCw size={16} style={{ marginRight: 8 }} /> Reset
            </button>
          )}

          {/* Branch preview */}
          {config.teamName && config.leaderName && (
            <div style={{
              marginTop: '1rem', padding: '0.65rem 0.9rem',
              background: 'rgba(59,130,246,0.08)',
              border: '1px solid rgba(59,130,246,0.2)',
              borderRadius: 8, fontSize: '0.75rem'
            }}>
              <span style={{ color: '#8b949e' }}>Branch: </span>
              <span style={{ color: '#58a6ff', fontFamily: 'monospace', fontWeight: 600 }}>
                {branchName || `${config.teamName.toUpperCase().replace(/\s+/g, '_')}_${config.leaderName.toUpperCase().replace(/\s+/g, '_')}_AI_Fix`}
              </span>
            </div>
          )}
        </motion.div>

        {/* ── Results Panel ── */}
        <motion.div className="results-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
          <div className="results-header">
            <h2>Results</h2>
            <span className={`status-badge ${statusBadge.cls}`}>{statusBadge.text}</span>
          </div>

          <div className="results-content" style={showResults ? { alignItems: 'stretch' } : {}}>
            {/* Idle */}
            {status === 'idle' && (
              <div className="results-placeholder">
                <FileCode size={64} />
                <p>Configure the agent and click "Run Agent" to start</p>
              </div>
            )}

            {/* Running */}
            {status === 'running' && (
              <div style={{ textAlign: 'center' }}>
                <div className="loading-spinner" style={{ margin: '0 auto' }} />
                <div className="loading-steps">
                  <p style={{ marginBottom: '1.5rem', color: 'var(--primary-light)' }}>{currentStep}</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {['Clone', 'Analyze', 'Detect', 'Fix', 'Push', 'PR'].map((step, idx) => (
                      <div
                        key={step}
                        className="loading-step"
                        style={{ color: currentStep.toLowerCase().includes(step.toLowerCase()) ? 'var(--primary-light)' : 'var(--text-light)' }}
                      >
                        {currentStep.toLowerCase().includes(step.toLowerCase())
                          ? <div className="loading-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                          : idx < ['Clone', 'Analyze', 'Detect', 'Fix', 'Push', 'PR'].indexOf(['Clone', 'Analyze', 'Detect', 'Fix', 'Push', 'PR'].find(s => currentStep.toLowerCase().includes(s.toLowerCase())))
                            ? <CheckCircle size={16} />
                            : <Clock size={16} />}
                        {step}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Live CI/CD timeline during run */}
                {cicdRuns.length > 0 && (
                  <div style={{ marginTop: '1.5rem', textAlign: 'left' }}>
                    <CicdTimeline cicdRuns={cicdRuns} />
                  </div>
                )}
              </div>
            )}

            {/* Success — four sections */}
            {showResults && (
              <div style={{ width: '100%' }}>
                {/* ① Run Summary */}
                <RunSummaryCard
                  config={config}
                  results={results}
                  branchName={branchName}
                  startTime={startTime}
                  endTime={endTime}
                  cicdPassed={cicdPassed}
                />

                {/* ② Score Breakdown */}
                <ScorePanel results={results} startTime={startTime} endTime={endTime} />

                {/* ③ Fixes Table */}
                <FixesTable errors={errors} />

                {/* ④ CI/CD Timeline */}
                <CicdTimeline cicdRuns={cicdRuns} />

                {/* PR link */}
                {results.prCreated && (
                  <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
                    <a href="#" style={{ color: 'var(--primary-light)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.9rem' }}>
                      <ExternalLink size={15} /> View Pull Request #{results.prCreated}
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* Error */}
            {status === 'error' && (
              <div className="results-placeholder" style={{ color: 'var(--error)' }}>
                <AlertCircle size={64} />
                <p>{agentError || 'An error occurred while running the agent'}</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* ── History ── */}
      {history.length > 0 && (
        <motion.div className="history-section" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <div className="history-header"><h2>Run History</h2></div>
          <div className="history-list">
            {history.map(item => (
              <div className="history-item" key={item.id}>
                <div className="history-info">
                  <h4>{item.repoUrl.split('/').pop()}</h4>
                  <p>{item.timestamp}</p>
                </div>
                <div className="history-stats">
                  <div className="history-stat">
                    <div className="history-stat-value">{item.errorsDetected}</div>
                    <div className="history-stat-label">Errors</div>
                  </div>
                  <div className="history-stat">
                    <div className="history-stat-value">{item.fixesApplied}</div>
                    <div className="history-stat-label">Fixed</div>
                  </div>
                  <div className="history-stat">
                    <div className="history-stat-value" style={{ color: item.status === 'success' ? 'var(--success)' : 'var(--error)' }}>
                      {item.status === 'success' ? <CheckCircle size={20} /> : <XCircle size={20} />}
                    </div>
                    <div className="history-stat-label">Status</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default Dashboard

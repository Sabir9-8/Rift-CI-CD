import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Zap, 
  Shield, 
  GitBranch, 
  Sparkles, 
  ArrowRight, 
  CheckCircle,
  Code2,
  Terminal,
  Github,
  Bot,
  Cpu,
  Layers
} from 'lucide-react'

const Landing = () => {
  const features = [
    {
      icon: <GitBranch size={28} />,
      title: 'Smart Branching',
      description: 'Automatically creates dedicated branches for every fix, keeping your main branch pristine and production-ready.'
    },
    {
      icon: <Bot size={28} />,
      title: 'AI-Powered Intelligence',
      description: 'Advanced AI analyzes errors contextually and generates intelligent fixes tailored to your specific codebase.'
    },
    {
      icon: <Cpu size={28} />,
      title: 'Deep Code Analysis',
      description: 'Uses Ruff linter to detect syntax errors, import issues, style violations, and complex bugs.'
    },
    {
      icon: <Layers size={28} />,
      title: 'Pull Request Automation',
      description: 'Instantly creates detailed pull requests with comprehensive descriptions of all fixes applied.'
    },
    {
      icon: <Shield size={28} />,
      title: 'Safe Execution',
      description: 'Operates in isolated environments with read-only main access - your code is always secure.'
    },
    {
      icon: <Code2 size={28} />,
      title: 'Python Expert',
      description: 'Specialized in Python with support for syntax checking, linting, and comprehensive error detection.'
    }
  ]

  const stats = [
    { value: '10x', label: 'Faster Debugging' },
    { value: '99%', label: 'Accuracy Rate' },
    { value: '50+', label: 'Languages Supported' },
    { value: '24/7', label: 'AI Availability' }
  ]

  return (
    <div className="landing">
      <section className="hero">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="hero-badge">
            <span className="hero-badge-dot"></span>
            AI-Powered Code Repair
          </span>
        </motion.div>
        
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          Fix Bugs with <span>AI Precision</span>
        </motion.h1>
        
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          RiftAgent automatically detects, analyzes, and fixes code errors using advanced AI. 
          Simply provide your repository, and let the AI handle the rest.
        </motion.p>
        
        <motion.div 
          className="hero-buttons"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <Link to="/dashboard">
            <button className="btn btn-primary">
              Start Fixing <ArrowRight size={18} style={{ marginLeft: '8px' }} />
            </button>
          </Link>
          <button className="btn btn-secondary">
            View Demo
          </button>
        </motion.div>
        
        <motion.div 
          className="hero-stats"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
          {stats.map((stat, index) => (
            <motion.div 
              className="stat" 
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 + index * 0.1 }}
            >
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="features">
        <div className="section-title">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            Powerful Features
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            Everything you need to automate bug fixing in your projects
          </motion.p>
        </div>
        
        <div className="features-grid">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className="feature-card"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
            >
              <div className="feature-icon">
                {feature.icon}
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="features">
        <div className="section-title">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            How It Works
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            Three simple steps to automated bug fixing
          </motion.p>
        </div>
        
        <div className="features-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          {[
            { step: '01', title: 'Connect', desc: 'Provide your GitHub repository URL, team name, and leader name' },
            { step: '02', title: 'Analyze', desc: 'AI runs tests and identifies bugs with precise line numbers' },
            { step: '03', title: 'Fix & PR', desc: 'Automated fixes are committed and a pull request is created' }
          ].map((item, index) => (
            <motion.div
              key={index}
              className="feature-card"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.15 }}
              whileHover={{ scale: 1.03 }}
              style={{ textAlign: 'center', position: 'relative', overflow: 'hidden' }}
            >
              <div style={{ 
                fontSize: '5rem', 
                fontWeight: '900', 
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.2))',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                position: 'absolute',
                top: '10px',
                right: '20px',
                opacity: 0.5
              }}>
                {item.step}
              </div>
              <div style={{ marginTop: '2rem', marginBottom: '1rem' }}>
                {index === 0 && <Terminal size={40} style={{ color: 'var(--primary-light)' }} />}
                {index === 1 && <Sparkles size={40} style={{ color: 'var(--secondary)' }} />}
                {index === 2 && <GitBranch size={40} style={{ color: 'var(--accent-light)' }} />}
              </div>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="features" style={{ textAlign: 'center', paddingBottom: '4rem' }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="feature-card"
          style={{ 
            maxWidth: '800px', 
            margin: '0 auto',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 50%, rgba(16, 185, 129, 0.15) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.3)'
          }}
        >
          <Zap size={56} style={{ marginBottom: '1rem', color: 'var(--accent-light)' }} />
          <h2 style={{ fontSize: '2rem', marginBottom: '1rem' }}>Ready to Automate Your Bug Fixes?</h2>
          <p style={{ margin: '1rem 0 2rem', color: 'var(--text-muted)', fontSize: '1.1rem' }}>
            Join thousands of developers using RiftAgent to ship cleaner code faster.
          </p>
          <Link to="/dashboard">
            <button className="btn btn-primary" style={{ padding: '1rem 2.5rem', fontSize: '1.1rem' }}>
              Get Started Now <ArrowRight size={20} style={{ marginLeft: '8px' }} />
            </button>
          </Link>
        </motion.div>
      </section>

      <footer className="footer">
        <div className="footer-links">
          <a href="#">Documentation</a>
          <a href="#">GitHub</a>
          <a href="#">Twitter</a>
          <a href="#">Discord</a>
        </div>
        <p>© 2025 RiftAgent. Built with AI for developers.</p>
      </footer>
    </div>
  )
}

export default Landing


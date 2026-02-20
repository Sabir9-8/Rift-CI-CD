# RiftAgent - AI-Powered Bug Detection & Fixing Tool

A full-stack application that automatically detects, analyzes, and fixes code errors using AI. Features a React dashboard with landing page and a Python backend powered by OpenAI.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.8+
- GitHub Personal Access Token
- OpenAI API Key (optional, for AI fixes)

### Installation

1. **Clone and install Python dependencies:**
```bash
cd RIFTNEW
pip install -r requirements.txt
```

2. **Install Frontend dependencies:**
```bash
cd frontend
npm install
```

3. **Install Backend dependencies:**
```bash
cd ../backend
npm install
```

### Running the Application

**Option 1 - Single Command (Recommended):**
```bash
./start.sh
```

**Option 2 - Manual:**
**Terminal 1 - Backend (API Server):**
```bash
cd backend
node server.js
```
Server runs on http://localhost:3002

**Terminal 2 - Frontend (React App):**
```bash
cd frontend
npm run dev
```
Frontend runs on http://localhost:5173

Open http://localhost:5173 in your browser.

## 📁 Project Structure

```
RIFTNEW/
├── rift/                    # Python Backend Package
│   ├── __init__.py
│   ├── agent.py            # Main RiftAgent class
│   ├── config.py           # Configuration management
│   └── utils.py            # Utility functions
├── backend/                 # Express API Server
│   ├── server.js           # Main server file
│   └── package.json
├── frontend/                # React Frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Landing & Dashboard pages
│   │   ├── context/        # Agent context provider
│   │   └── index.css       # Global styles
│   └── vite.config.js
├── requirements.txt         # Python dependencies
└── README.md
```

## 🔧 Features

### Landing Page
- Modern hero section with stats
- Feature highlights
- How it works section
- Call to action

### Dashboard
- Repository URL configuration
- Team/Leader name input
- GitHub token & OpenAI key inputs
- Real-time progress tracking
- Results display with error details
- Run history

### RiftAgent (Python)
- Automatic repository cloning
- Branch creation
- Test execution
- Error detection & classification
- AI-powered fix generation
- Automatic commit & push
- Pull request creation

## 🔑 Environment Variables

**Backend (optional):**
- `PORT` - Server port (default: 3001)

**Frontend (optional):**
- Configure API URL in vite.config.js

**Python:**
- `GITHUB_TOKEN` - GitHub personal access token
- `OPENAI_API_KEY` - OpenAI API key

## 📝 Usage

1. Open the dashboard at http://localhost:5173
2. Enter your GitHub repository URL
3. Enter team name and leader name
4. Provide your GitHub token (with repo permissions)
5. Optionally add OpenAI key for AI-powered fixes
6. Click "Run Agent"
7. Watch as the agent clones, tests, fixes, and creates a PR!

## 🛠️ Tech Stack

- **Frontend:** React, Vite, Framer Motion, Lucide Icons
- **Backend:** Express.js, Python Shell
- **AI:** OpenAI GPT-3.5
- **GitHub:** PyGithub

## 📄 License

MIT License


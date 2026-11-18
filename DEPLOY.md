# RiftAgent Deployment Configuration

## Overview
This is a full-stack application (React 19 frontend + Express.js backend + LangGraph Python agent).

---

## Deployment Options

### Option 1: Vercel (Frontend) + Railway / Render (Backend) [Recommended]

This is the cleanest and most scalable architecture:

#### Step 1: Deploy Backend (Railway or Render)
1. **Create project on [Railway](https://railway.app) or [Render](https://render.com)**.
2. **Connect repository**: `https://github.com/Sabir9-8/Rift-CI-CD`.
3. **Build using Dockerfile**: Railway auto-detects `Dockerfile` in the root.
4. **Environment Variables**:
   * `PORT`: `3002`
   * `GITHUB_TOKEN`: (Optional GitHub PAT)
   * `GEMINI_API_KEY`: (Optional free Google AI Studio key)
   * `OPENAI_API_KEY`: (Optional OpenAI key)
5. Copy your live backend service URL (e.g. `https://rift-backend-production.up.railway.app`).

#### Step 2: Deploy Frontend on Vercel
1. **Import repository on [Vercel](https://vercel.com)**.
2. Vercel automatically detects `vercel.json` and Vite.
3. In **Environment Variables**, add:
   * **`VITE_API_URL`**: `https://your-backend-url.up.railway.app` (the URL from Step 1)
4. Click **Deploy**. Your React dashboard will be live at `https://your-app.vercel.app`!

---

### Option 2: All-in-One Docker Deployment
Deploy both backend and pre-built frontend in a single container:
```bash
# Build container
docker build -t riftagent .

# Run container
docker run -p 3002:3002 -e GITHUB_TOKEN=xxx -e GEMINI_API_KEY=xxx riftagent
```
Open `http://localhost:3002` in your browser.

---

### Option 3: Render Web Service & Static Site
1. **Backend Web Service**:
   * Build Command: `cd backend && npm install && cd .. && pip install -r requirements.txt`
   * Start Command: `node backend/server.js`
   * Port: `3002`
2. **Frontend Static Site**:
   * Build Command: `cd frontend && npm install && npm run build`
   * Publish Directory: `frontend/dist`
   * Environment Variable: `VITE_API_URL=https://<your-backend-service>.onrender.com`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | Yes | Server port (default: 3002) |
| `GITHUB_TOKEN` | No | GitHub token for creating PRs |
| `OPENAI_API_KEY` | No | OpenAI API key for AI-powered fixes |
| `PYTHONPATH` | Yes | Set to `.` for Python imports |

## Important Notes

1. **Long-running processes**: The Python agent can take 5-15 minutes to analyze repositories. Ensure your deployment platform supports long-running processes (not serverless).

2. **API calls from frontend**: Update the frontend's API base URL to point to your deployed backend:
   - Development: `http://localhost:3002`
   - Production: `https://your-backend-url.com`

3. **CORS**: The backend is configured to accept requests from the frontend domain in production.


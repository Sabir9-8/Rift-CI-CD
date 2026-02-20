# RiftAgent Deployment Configuration

## Overview
This is a full-stack application (React frontend + Express.js backend + Python agent).

## Deployment Options

### Option 1: Render (Recommended)
Render provides easy deployment for both Node.js and Python services.

1. **Create a Render account** at https://render.com
2. **Deploy Backend + Python Agent**:
   - Create a new Web Service
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `node backend/server.js`
   - Add environment variables:
     - `PORT`: 3002
     - `PYTHONPATH`: .
     - `GITHUB_TOKEN`: (your GitHub token for creating PRs)
     - `OPENAI_API_KEY`: (optional, for AI-powered fixes)

3. **Deploy Frontend**:
   - Create a new Static Site
   - Connect the same repository
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`

### Option 2: Railway
Railway supports both Node.js and Python through Dockerfile-based deployment.

1. **Create a Railway project** at https://railway.app
2. **Deploy using Dockerfile** (see Dockerfile in this repo)
3. Set environment variables in Railway dashboard

### Option 3: Docker (Any cloud)
Build and run the Docker container locally or deploy to any cloud provider.

```bash
# Build
docker build -t riftagent .

# Run
docker run -p 3002:3002 -e GITHUB_TOKEN=xxx -e OPENAI_API_KEY=xxx riftagent
```

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


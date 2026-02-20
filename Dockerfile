# RiftAgent Dockerfile
# Supports deployment to Railway, Render, or any Docker-compatible cloud

# Build stage for frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
COPY frontend/vite.config.js ./
COPY frontend/index.html ./
COPY frontend/eslint.config.js ./
COPY frontend/src ./src
COPY frontend/public ./public

# Install frontend dependencies and build
RUN npm install && npm run build

# Production stage
FROM python:3.11-slim

# Install Node.js for the backend
RUN apt-get update && apt-get install -y nodejs npm curl git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY backend/package*.json ./
COPY backend/server.js ./

# Install backend dependencies
RUN npm install

# Copy Python files
COPY requirements.txt .
COPY rift ./rift

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set environment variables
ENV PORT=3002
ENV PYTHONPATH=.
ENV NODE_ENV=production

# Expose the port
EXPOSE 3002

# Start the server
CMD ["node", "server.js"]


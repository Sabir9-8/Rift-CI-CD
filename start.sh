#!/bin/bash

# RiftAgent Startup Script
# Run both backend and frontend with a single command

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "🚀 Starting RiftAgent from $SCRIPT_DIR..."

# Check environment
NODE_ENV="${NODE_ENV:-development}"

# Kill existing processes on ports 3002 and 5173
echo "🧹 Cleaning up existing processes..."
lsof -ti:3002 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

sleep 1

# Start backend
echo "📦 Starting Backend..."
cd "$SCRIPT_DIR/backend"

# Check if running in production mode
if [ "$NODE_ENV" = "production" ]; then
    echo "Running in PRODUCTION mode"
    # In production, we serve both frontend and backend from the same server
    node server.js &
else
    echo "Running in DEVELOPMENT mode"
    node server.js &
fi

BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend only in development mode
if [ "$NODE_ENV" != "production" ]; then
    echo "🎨 Starting Frontend..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev &
    FRONTEND_PID=$!
fi

echo ""
echo "✅ RiftAgent is running!"
echo "   Backend: http://localhost:3002"
if [ "$NODE_ENV" != "production" ]; then
    echo "   Frontend: http://localhost:5173"
else
    echo "   Frontend: http://localhost:3002 (served by backend)"
fi
echo ""
echo "Press Ctrl+C to stop all services"

# Save PIDs to file for later cleanup
echo "$BACKEND_PID ${FRONTEND_PID:-}" > /tmp/riftagent.pids

# Wait for interrupt
wait


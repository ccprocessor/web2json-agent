#!/bin/bash

# Web2JSON Agent - Startup Script
# Starts both the backend API and the frontend UI simultaneously

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"

echo "🚀 Starting Web2JSON Agent..."
echo ""

# Check if the port is occupied
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use. Killing existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 5173 is already in use. Killing existing process..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start the backend
echo "📡 Starting backend API (port 8000)..."
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Production Mode: Disable automatic reloading to avoid restarts triggered by changes in the output directory
# If you need reload for development, use: --reload --reload-exclude 'output/**' --reload-exclude 'logs/**'
"$PYTHON_BIN" -m uvicorn web2json_api.main:app --host 0.0.0.0 --port 8000 \
  --reload-exclude 'output/**' \
  --reload-exclude 'logs/**' \
  --reload-exclude '*.log' \
  > logs/api.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

sleep 3

# Check if the backend has started successfully
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend API started successfully"
else
    echo "❌ Failed to start backend API"
    exit 1
fi

# Start the frontend
echo ""
echo "🎨 Starting frontend UI (port 5173)..."
cd "$SCRIPT_DIR/web2json_ui" && npm run dev > "$SCRIPT_DIR/logs/ui.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

sleep 5

echo ""
echo "✨ Web2JSON Agent is ready!"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "📡 Backend API: http://localhost:8000/api/docs"
echo ""
echo "📝 Logs:"
echo "   Backend: logs/api.log"
echo "   Frontend: logs/ui.log"
echo ""
echo "To stop the services, run: ./stop.sh"
echo "Or press Ctrl+C and run: pkill -f 'uvicorn|vite'"
echo ""

# Save PID
echo $BACKEND_PID > "$SCRIPT_DIR/.backend.pid"
echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend.pid"

# Wait for user interruption
wait

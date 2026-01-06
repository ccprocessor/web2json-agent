#!/bin/bash

# Web2JSON Agent - 启动脚本
# 同时启动后端API和前端UI

echo "🚀 Starting Web2JSON Agent..."
echo ""

# 检查端口是否被占用
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

# 启动后端
echo "📡 Starting backend API (port 8000)..."
cd /Users/brown/Projects/AILabProject/web2json-agent
# 生产模式：禁用自动重载，避免 output 目录变化触发重启
uvicorn web2json_api.main:app --host 0.0.0.0 --port 8000 \
  > logs/api.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend API started successfully"
else
    echo "❌ Failed to start backend API"
    exit 1
fi

# 启动前端
echo ""
echo "🎨 Starting frontend UI (port 5173)..."
cd web2json_ui && npm run dev > ../logs/ui.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# 等待前端启动
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

# 保存PID
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 等待用户中断
wait

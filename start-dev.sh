#!/bin/bash

echo "🚀 Starting ThreatWatch AI Development Environment"
echo "=============================================="

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   macOS: brew services start postgresql"
    echo "   Linux: sudo systemctl start postgresql"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping >/dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first."
    echo "   macOS: brew services start redis"
    echo "   Linux: sudo systemctl start redis"
    exit 1
fi

echo "✅ PostgreSQL and Redis are running"

# Create database if it doesn't exist
createdb threatwatch 2>/dev/null || echo "Database 'threatwatch' already exists"

echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

echo "📦 Installing Node.js dependencies..."
cd ../frontend
npm install

echo "🎯 Setup complete! Now start the services:"
echo ""
echo "Terminal 1 - Backend API:"
echo "cd backend && python run.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "cd frontend && npm run dev"
echo ""
echo "Terminal 3 - Celery Worker (optional):"
echo "cd backend && celery -A app.workers.celery_app worker --loglevel=info"
echo ""
echo "🌐 Access the app at: http://localhost:3000"
echo "📚 API docs at: http://localhost:8000/docs"
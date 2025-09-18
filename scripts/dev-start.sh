#!/bin/bash

# Fraud Detection System - Development Startup Script
# This script starts both backend and frontend services in development mode

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        print_warning "Killing existing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $max_attempts seconds"
    return 1
}

# Main execution
main() {
    print_status "Starting Fraud Detection System in development mode..."
    
    # Check if we're in the right directory
    if [ ! -f "package.json" ] && [ ! -f "frontend/package.json" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Navigate to project root if we're in scripts directory
    if [ -f "../package.json" ] || [ -f "../frontend/package.json" ]; then
        cd ..
    fi
    
    # Load environment variables if .env exists
    if [ -f ".env" ]; then
        print_status "Loading environment variables from .env"
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Set default ports
    BACKEND_PORT=${PORT:-5001}
    FRONTEND_PORT=${FRONTEND_PORT:-3000}
    
    # Check and clean up ports
    if ! check_port $BACKEND_PORT; then
        print_warning "Port $BACKEND_PORT is in use"
        kill_port $BACKEND_PORT
    fi
    
    if ! check_port $FRONTEND_PORT; then
        print_warning "Port $FRONTEND_PORT is in use"
        kill_port $FRONTEND_PORT
    fi
    
    # Check dependencies
    print_status "Checking dependencies..."
    
    # Check Python and backend dependencies
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    if [ ! -f "backend/requirements.txt" ]; then
        print_error "Backend requirements.txt not found"
        exit 1
    fi
    
    # Check Node.js and frontend dependencies
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    if [ ! -f "frontend/package.json" ]; then
        print_error "Frontend package.json not found"
        exit 1
    fi
    
    # Install backend dependencies
    print_status "Installing backend dependencies..."
    cd backend
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    cd ..
    
    # Install frontend dependencies
    print_status "Installing frontend dependencies..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install > /dev/null 2>&1
    fi
    cd ..
    
    # Start backend service
    print_status "Starting backend service on port $BACKEND_PORT..."
    cd backend
    source venv/bin/activate
    PORT=$BACKEND_PORT FLASK_ENV=development python3 app.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to be ready
    if ! wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend API"; then
        print_error "Backend failed to start"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    # Start frontend service
    print_status "Starting frontend service on port $FRONTEND_PORT..."
    cd frontend
    PORT=$FRONTEND_PORT npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to be ready
    if ! wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend App"; then
        print_error "Frontend failed to start"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    
    # Success message
    print_success "Fraud Detection System is running!"
    echo ""
    echo "🚀 Services:"
    echo "   Frontend: http://localhost:$FRONTEND_PORT"
    echo "   Backend:  http://localhost:$BACKEND_PORT"
    echo "   Health:   http://localhost:$BACKEND_PORT/health"
    echo ""
    echo "📋 Process IDs:"
    echo "   Backend PID:  $BACKEND_PID"
    echo "   Frontend PID: $FRONTEND_PID"
    echo ""
    echo "📝 Logs:"
    echo "   Backend:  tail -f logs/backend.log"
    echo "   Frontend: tail -f logs/frontend.log"
    echo ""
    echo "🛑 To stop services:"
    echo "   kill $BACKEND_PID $FRONTEND_PID"
    echo "   or run: ./scripts/dev-stop.sh"
    echo ""
    
    # Save PIDs for cleanup script
    mkdir -p .tmp
    echo "$BACKEND_PID" > .tmp/backend.pid
    echo "$FRONTEND_PID" > .tmp/frontend.pid
    
    # Keep script running and handle cleanup on exit
    trap 'print_status "Shutting down services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; rm -f .tmp/*.pid' EXIT
    
    print_status "Press Ctrl+C to stop all services"
    wait
}

# Create logs directory
mkdir -p logs

# Run main function
main "$@"

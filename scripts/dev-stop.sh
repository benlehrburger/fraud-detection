#!/bin/bash

# Fraud Detection System - Development Stop Script
# This script stops all running development services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to kill process by PID
kill_pid() {
    local pid=$1
    local service_name=$2
    
    if [ ! -z "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        print_status "Stopping $service_name (PID: $pid)..."
        kill -TERM "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Force killing $service_name..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
        
        print_success "$service_name stopped"
    else
        print_warning "$service_name was not running"
    fi
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pids" ]; then
        print_status "Killing processes on port $port ($service_name)..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$remaining_pids" ]; then
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        print_success "Processes on port $port stopped"
    fi
}

main() {
    print_status "Stopping Fraud Detection System development services..."
    
    # Navigate to project root if we're in scripts directory
    if [ -f "../package.json" ] || [ -f "../frontend/package.json" ]; then
        cd ..
    fi
    
    # Stop services using saved PIDs
    if [ -f ".tmp/backend.pid" ]; then
        BACKEND_PID=$(cat .tmp/backend.pid)
        kill_pid "$BACKEND_PID" "Backend Service"
        rm -f .tmp/backend.pid
    fi
    
    if [ -f ".tmp/frontend.pid" ]; then
        FRONTEND_PID=$(cat .tmp/frontend.pid)
        kill_pid "$FRONTEND_PID" "Frontend Service"
        rm -f .tmp/frontend.pid
    fi
    
    # Kill any remaining processes on known ports
    kill_port 5001 "Backend"
    kill_port 3000 "Frontend"
    kill_port 5000 "Legacy Backend"
    
    # Clean up temp directory
    rm -rf .tmp
    
    print_success "All services stopped successfully!"
}

main "$@"

#!/bin/bash

# FraudGuard Setup Script
# Automated installation for both frontend and backend

set -e  # Exit on any error

echo "🛡️  FraudGuard Setup Script"
echo "================================"
echo ""

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
else
    print_error "Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_success "npm $NPM_VERSION found"
else
    print_error "npm is not installed. Please install npm and try again."
    exit 1
fi

echo ""
print_status "Prerequisites check complete!"
echo ""

# Backend setup
print_status "Setting up backend..."

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Verify installation
print_status "Verifying backend installation..."
python -c "import flask, flask_cors, gremlin_python; print('✅ Backend dependencies verified!')"

cd ..

echo ""

# Frontend setup
print_status "Setting up frontend..."

cd frontend

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install
print_success "Node.js dependencies installed"

# Verify installation
print_status "Verifying frontend installation..."
if [ -d "node_modules" ]; then
    print_success "Frontend dependencies verified!"
else
    print_error "Frontend installation failed"
    exit 1
fi

cd ..

echo ""
print_success "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Start Aerospike Graph (ensure it's running on localhost:8182)"
echo "  2. Start backend: cd backend && source venv/bin/activate && python app.py"
echo "  3. Start frontend: cd frontend && npm start"
echo "  4. Open browser to http://localhost:3000"
echo ""
print_status "For detailed instructions, see README.md" 
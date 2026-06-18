#!/bin/bash

# 🚀 Advanced ML Firewall Dashboard - Quick Start Script
# This script automates the setup and initialization

set -e

PROJECT_ROOT="/home/neeraj/Downloads/BT-3030-Sarva-Firewall-main"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "=================================="
echo "🚀 Advanced ML Firewall Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}==> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check Python version
print_step "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check Node.js
print_step "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Please install Node.js 16+"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION found"

# Install Python dependencies
print_step "Installing Python dependencies..."
cd "$BACKEND_DIR"
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
print_success "Python dependencies installed"

# Install Node dependencies
print_step "Installing Node.js dependencies..."
cd "$PROJECT_ROOT"
npm install --legacy-peer-deps > /dev/null 2>&1 || npm install > /dev/null 2>&1
print_success "Node.js dependencies installed"

# Create necessary directories
print_step "Creating directories..."
mkdir -p "$BACKEND_DIR/ml_models/trained_models"
mkdir -p "$BACKEND_DIR/logs"
print_success "Directories created"

# Check for Ollama
print_step "Checking for Ollama (Local LLM)..."
if ! command -v ollama &> /dev/null; then
    print_warning "Ollama not found. Please install from https://ollama.ai/download"
    print_warning "You can still use the system without LLM features"
else
    OLLAMA_VERSION=$(ollama --version)
    print_success "Ollama found: $OLLAMA_VERSION"
fi

# Check dataset
print_step "Checking for dataset..."
if [ -f "/home/neeraj/Downloads/archive/log2.csv" ]; then
    LINES=$(wc -l < /home/neeraj/Downloads/archive/log2.csv)
    print_success "Dataset found with $LINES lines"
else
    print_warning "Dataset not found at /home/neeraj/Downloads/archive/log2.csv"
fi

# Display setup summary
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. ${BLUE}Train ML Models${NC} (run once, takes 10-30 minutes):"
echo "   cd $BACKEND_DIR"
echo "   python3 train_models.py"
echo ""
echo "2. ${BLUE}Start Ollama${NC} (Terminal 1):"
echo "   ollama serve"
echo ""
echo "3. ${BLUE}Start Backend${NC} (Terminal 2):"
echo "   cd $BACKEND_DIR"
echo "   python3 app.py"
echo ""
echo "4. ${BLUE}Start Frontend${NC} (Terminal 3):"
echo "   cd $PROJECT_ROOT"
echo "   npm run dev"
echo ""
echo "5. ${BLUE}Open Browser${NC}:"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:5000/api/health"
echo ""
echo "=================================="
echo "📚 Documentation:"
echo "   See ADVANCED_SETUP_GUIDE.md for detailed information"
echo "=================================="
echo ""

print_success "Setup ready! Run the 5 steps above to start the system."

#!/bin/bash

# SARVA Firewall - Automated Setup Script
# This script automates the entire setup process

set -e  # Exit on error

echo "================================"
echo "🔥 SARVA Firewall - Auto Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Create backend environment file
echo "📝 Creating backend environment configuration..."
cat > backend/.env << 'EOF'
# API Keys - OSINT Integration
SHODAN_API_KEY=mvhsmzpFJEIcTdYg2HhJtoPiWR0GQGt6
ABUSEIPDB_API_KEY=a672ff450abbfa9ccf0ed18edd261b309557e2b36ec6c5a84b1123f947e3641a
VIRUSTOTAL_API_KEY=5f4e4959ea2a71d8f4a0ca2d4332825c6ed46ca9108fc9844443540edd16fae710b1311f792025c3

# Server Configuration
FLASK_ENV=development
FLASK_APP=app.py
HOST=0.0.0.0
PORT=5000
DEBUG=True

# Database
MONGODB_URI=mongodb://mongo:27017/sarva_firewall
MONGODB_USER=admin
MONGODB_PASSWORD=sarva_secure_pass

# Blockchain
WEB3_PROVIDER_URL=https://amoy-rpc.polygon.technology
PRIVATE_KEY=your_eth_private_key_here
CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000

# LLM Configuration
LLM_MODEL=llama2
LLM_BASE_URL=http://localhost:11434

# JWT Secret
JWT_SECRET=sarva_jwt_secret_key_change_in_production

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:5000
EOF

echo "✅ Backend environment configured"
echo ""

# Install frontend dependencies
echo "📦 Installing Node.js dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Start Docker services
echo "🚀 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo ""
echo "📋 Service Status:"
docker-compose ps

echo ""
echo "================================"
echo "✅ SARVA Firewall Setup Complete!"
echo "================================"
echo ""
echo "🌐 Access Points:"
echo "  • Frontend: http://localhost:5173"
echo "  • Backend API: http://localhost:5000"
echo "  • API Health: http://localhost:5000/api/health"
echo "  • MongoDB: localhost:27017"
echo ""
echo "📝 Next Steps:"
echo "  1. Open http://localhost:5173 in your browser"
echo "  2. Login with test credentials"
echo "  3. Go to Dashboard to see threat detection"
echo "  4. Use Attack Simulator to test detection"
echo ""
echo "📚 Documentation:"
echo "  • SETUP_GUIDE.md - Quick start guide"
echo "  • IMPLEMENTATION_GUIDE.md - Full documentation"
echo ""
echo "🔗 Useful Commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Restart: docker-compose restart"
echo ""

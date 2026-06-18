# SARVA Firewall - Complete Backend & Frontend Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (local or Docker)
- Git

### Option 1: Docker Compose (Recommended)

```bash
# From project root
docker-compose up -d

# Access the application
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- API Docs: http://localhost:5000/api/health
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run Flask server
python app.py
```

#### Frontend Setup

```bash
# Install dependencies
npm install

# Set environment variable
export VITE_API_URL=http://localhost:5000/api

# Start dev server
npm run dev
```

## 📋 API Keys Setup

Add these to `backend/.env`:

```env
SHODAN_API_KEY=mvhsmzpFJEIcTdYg2HhJtoPiWR0GQGt6
ABUSEIPDB_API_KEY=a672ff450abbfa9ccf0ed18edd261b309557e2b36ec6c5a84b1123f947e3641a
VIRUSTOTAL_API_KEY=5f4e4959ea2a71d8f4a0ca2d4332825c6ed46ca9108fc9844443540edd16fae710b1311f792025c3
```

## 🔧 Backend API Endpoints

### Threat Detection
- `POST /api/threats/analyze/email` - Analyze email for phishing
- `POST /api/threats/analyze/malware` - Analyze binary behavior
- `POST /api/threats/analyze/network` - Analyze network packet
- `GET /api/threats/recent` - Get recent threats
- `GET /api/threats/timeline` - Get threat timeline
- `GET /api/threats/stats` - Get dashboard statistics

### OSINT Integration
- `POST /api/osint/investigate/ip` - Investigate IP (Shodan, AbuseIPDB)
- `POST /api/osint/investigate/file` - Investigate file hash (VirusTotal)
- `POST /api/osint/investigate/url` - Investigate URL
- `POST /api/osint/shodan/search` - Search Shodan database
- `POST /api/osint/abuseipdb/check` - Check IP reputation
- `POST /api/osint/virustotal/scan` - Scan with VirusTotal

### Attack Simulation
- `POST /api/simulator/ddos` - Simulate DDoS attack
- `POST /api/simulator/phishing` - Simulate phishing campaign
- `POST /api/simulator/malware` - Simulate malware infection
- `POST /api/simulator/portscan` - Simulate port scan
- `POST /api/simulator/sqli` - Simulate SQL injection
- `GET /api/simulator/status/<sim_id>` - Get simulation status

### AI/LLM Assistant
- `POST /api/llm/analyze` - Analyze threat with LLM
- `POST /api/llm/report` - Generate security report
- `POST /api/llm/chat` - Chat with AI assistant
- `POST /api/llm/recommendations` - Get AI recommendations
- `GET /api/llm/status` - Get LLM service status

### Blockchain Logging
- `POST /api/blockchain/log/threat` - Log threat to blockchain
- `GET /api/blockchain/verify/<threat_id>` - Verify threat log
- `GET /api/blockchain/history` - Get threat history
- `GET /api/blockchain/network/status` - Get blockchain status

## 🧠 ML Models

### Implemented Models
1. **Phishing Detector** - Random Forest Classifier
   - Email content analysis
   - Phishing keyword detection
   - URL/domain reputation

2. **Malware Detector** - Pattern-based + ML
   - Binary behavior analysis
   - Registry/file system monitoring
   - Process injection detection

3. **Vulnerability Scanner** - CVE database integration
   - Known vulnerability detection
   - CVSS severity scoring

4. **Network Analyzer** - LSTM-based anomaly detection
   - Traffic pattern analysis
   - Attack vector identification

### Training
```bash
cd backend/ml_models
python train_models.py
```

## 🤖 Local LLM Setup (Optional)

Install and run Ollama for offline AI analysis:

```bash
# Install Ollama (https://ollama.ai)
ollama pull llama2

# Run Ollama service
ollama serve

# SARVA will automatically connect to http://localhost:11434
```

## 🔗 Blockchain Integration

### Network: Polygon Amoy Testnet

1. Get testnet faucet tokens: https://amoy.polygonscan.com/

2. Deploy smart contract:
```bash
cd blockchain
npm install
npx hardhat deploy --network amoy
```

3. Update contract address in `.env`:
```env
CONTRACT_ADDRESS=0x...your_contract_address
```

## 📊 Real-time Monitoring

Frontend connects to backend via WebSocket for live threat updates:

```typescript
import { threatAPI } from '@/lib/api';

// Fetch recent threats
const threats = await threatAPI.getRecentThreats(10);

// Get timeline data for graphs
const timeline = await threatAPI.getThreatTimeline(24);

// Get dashboard stats
const stats = await threatAPI.getStats();
```

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Test phishing detection
curl -X POST http://localhost:5000/api/threats/analyze/email \
  -H "Content-Type: application/json" \
  -d '{"content":"Click here to verify your account", "sender":"attacker@fake.com"}'

# Test OSINT
curl -X POST http://localhost:5000/api/osint/investigate/ip \
  -H "Content-Type: application/json" \
  -d '{"ip":"1.1.1.1"}'

# Test simulator
curl -X POST http://localhost:5000/api/simulator/ddos \
  -H "Content-Type: application/json" \
  -d '{"target_ip":"192.168.1.1", "duration":60}'
```

## 📦 Production Deployment

### Docker Build
```bash
docker build -t sarva-backend:latest ./backend
docker build -t sarva-frontend:latest -f Dockerfile.frontend .
```

### AWS EC2 Deployment
```bash
# SSH into EC2 instance
ssh -i key.pem ec2-user@instance-ip

# Clone repo
git clone https://github.com/your-repo/sarva.git
cd sarva

# Run with Docker Compose
docker-compose -f docker-compose.yml up -d
```

## 🔐 Security Considerations

1. **API Keys**: Store in `.env`, never commit
2. **CORS**: Configure allowed origins in `.env`
3. **JWT**: Implement authentication for protected endpoints
4. **HTTPS**: Use SSL certificates in production
5. **Rate Limiting**: Implement to prevent API abuse
6. **Input Validation**: All inputs are sanitized

## 📱 Features Implemented

✅ AI-based phishing detection
✅ Malware behavior analysis
✅ Real-time threat monitoring dashboard
✅ OSINT integration (Shodan, AbuseIPDB, VirusTotal)
✅ Attack simulation engine
✅ Blockchain-based threat logging
✅ Local LLM integration (offline AI)
✅ WebSocket for live updates
✅ Comprehensive API with REST endpoints
✅ Docker containerization

## 🚀 Next Steps

1. **ML Model Training**: Train on larger dataset
2. **Advanced Analytics**: Implement deep learning (LSTM, CNN)
3. **Mobile App**: Build Android/iOS apps
4. **Advanced Features**: 
   - Zero-day detection
   - Behavior pattern learning
   - Autonomous threat response

## 📞 Support

For issues or questions, check:
- Backend logs: `docker logs sarva_backend`
- Frontend logs: Browser console (F12)
- API health: `http://localhost:5000/api/health`

## 📄 License

MIT License - See LICENSE file

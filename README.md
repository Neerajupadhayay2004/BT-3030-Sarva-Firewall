# 🛡️ SARVA - AI-Powered Universal Firewall

> **Cyber threats are evolving faster than traditional security. SARVA fights back with AI, Blockchain, and OSINT.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What is SARVA?

**SARVA** (Secure AI-powered Real-time Vulnerability & Attack Detection System) is a next-generation firewall that:

*   **Host-Based Filtering (iptables)**: Provides robust host layer access control, packet filtering, and IP-blocking.
*   **Network perimeter (pfSense)**: Integrates policy enforcement, routing, and traffic segmentation.
*   **Packet Inspection (Python + Scapy)**: Deep packet analysis and custom test packet generation.
*   **Real-time threat detection**: Employs Machine Learning models (Random Forest) to evaluate phishing, malware, and network threats.
*   **Immutable Logs (Blockchain)**: Logs alerts securely to Polygon Amoy Testnet for an audit trail.
*   **Local LLM analysis (Ollama)**: Enables automated mitigation recommendations and threat intelligence parsing.
*   **Attack Simulator**: Run mock DDoS, SQLi, Phishing, Malware, and Port Scanning payloads to test firewall responsiveness.

---

## 🚀 Quick Start (30 Seconds)

### Prerequisites
- Docker & Docker Compose
- Node.js (v18+) & Python (v3.11+)

### One-Command Deployment

```bash
chmod +x setup.sh
./setup.sh
```

Then open **http://localhost:5173** and login with test credentials (`username: admin`, `password: firewall2024`).

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                       │
│               React + TypeScript + Tailwind CSS             │
│         (Real-time Dashboard, Graphs, Attack Simulator)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ API (REST + WebSocket)
┌──────────────────────▼──────────────────────────────────────┐
│                     Backend Layer (Flask)                   │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │  Threat Models  │  │  OSINT Services  │  │ Blockchain  │ │
│  ├─ Phishing       │  ├─ Shodan          │  │ Logging &   │ │
│  ├─ Malware       │  ├─ AbuseIPDB      │  │ Verification│ │
│  ├─ Vulnerability │  ├─ VirusTotal     │  │ (Polygon)   │ │
│  └─ Network       │  └──────────────────┘  └─────────────┘ │
│                                                              │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Attack Sim      │  │  LLM Service │  │  Threat      │ │
│  ├─ DDoS           │  │  (Ollama)    │  │  Analyzer    │ │
│  ├─ Phishing       │  │  - Analysis  │  │  - Central   │ │
│  ├─ Malware        │  │  - Reports   │  │  - Logging   │ │
│  └─ Exploits       │  └──────────────┘  └──────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    ┌───▼────┐    ┌────▼───┐    ┌───▼────┐
    │MongoDB │    │ Blockchain │  │ LLM    │
    │        │    │  (Polygon) │  │(Ollama)│
    └────────┘    └────────────┘  └────────┘
```

---

## 🔑 API Keys Setup

Add these to `backend/.env`:

```env
JWT_SECRET=sarva_default_secure_secret_change_me
SHODAN_API_KEY=mvhsmzpFJEIcTdYg2HhJtoPiWR0GQGt6
ABUSEIPDB_API_KEY=a672ff450abbfa9ccf0ed18edd261b309557e2b36ec6c5a84b1123f947e3641a
VIRUSTOTAL_API_KEY=5f4e4959ea2a71d8f4a0ca2d4332825c6ed46ca9108fc9844443540edd16fae710b1311f792025c3
```

---

## 📚 API Endpoints (All Protected via JWT except Login & Health)

### Auth & Health
```
POST   /api/auth/login                     - Secure login returning JWT
GET    /api/health                         - Health check
```

### Threat Detection
```
POST   /api/threats/analyze/email          - Phishing analysis
POST   /api/threats/analyze/malware        - Malware detection
POST   /api/threats/analyze/network        - Network threat analysis
GET    /api/threats/recent                 - Recent threats
GET    /api/threats/timeline               - Threat timeline (24h)
GET    /api/threats/stats                  - Dashboard statistics
```

### OSINT
```
POST   /api/osint/investigate/ip           - IP reputation check
POST   /api/osint/investigate/file         - File hash scan
POST   /api/osint/investigate/url          - URL reputation scan
POST   /api/osint/shodan/search            - Query Shodan
POST   /api/osint/abuseipdb/check          - IP reputation history
POST   /api/osint/virustotal/scan          - Scan with VirusTotal
```

### Attack Simulation
```
POST   /api/simulator/ddos                 - Start DDoS simulation
POST   /api/simulator/phishing             - Start phishing campaign
POST   /api/simulator/malware              - Start malware infection
POST   /api/simulator/portscan             - Start port scan simulation
POST   /api/simulator/sqli                 - Start SQL injection simulation
GET    /api/simulator/status/<id>          - Simulation status
```

### Blockchain
```
POST   /api/blockchain/log/threat          - Log threat to blockchain
GET    /api/blockchain/verify/<id>         - Verify threat log integrity
GET    /api/blockchain/history             - Threat ledger history
GET    /api/blockchain/network/status      - Blockchain network status
GET    /api/blockchain/transaction/<hash>  - View transaction verification
```

### LLM Assistant
```
POST   /api/llm/analyze                    - AI threat analysis
POST   /api/llm/report                     - Generate security report
POST   /api/llm/chat                       - Chat with AI assistant
POST   /api/llm/recommendations            - Mitigation recommendations
GET    /api/llm/status                     - LLM service status
```

---

## 🔐 Security Standards

The firewall conforms to strict security guidelines:
1. **JWT Authentication**: All sensitive API routes require authorization header token.
2. **Command Injection Prevention**: All shell integrations (e.g. `iptables`) use list-based arguments with `subprocess.run`, avoiding string concatenation or `shell=True`.
3. **Path Traversal Prevention**: Safe path utilities validate folder bounds.
4. **WAF Active Protection**: Incoming API requests are parsed in middleware to identify and block XSS, SQLi, Command Injection, LFI, and SSRF attacks instantly, dynamically logging the attacker IP.

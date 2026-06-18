
# SARVA Firewall - Multi-Layer Lab Guide

This guide explains how to set up and use the SARVA Firewall lab with three layers of protection:

1. **Host Layer**: iptables
2. **Network Layer**: pfSense
3. **Packet Layer**: Python + Scapy

---

## Overview

The SARVA Firewall lab demonstrates how different firewall technologies work together at different OSI layers to protect a network.

---

## 1. Host Layer - iptables Setup

### Prerequisites
- Linux system (Ubuntu/Debian recommended)
- Root/sudo access

### Configuration
iptables is managed via the SARVA Firewall API:

#### API Endpoints

- **List Rules**: `GET /api/lab/iptables/rules`
- **Add Rule**: `POST /api/lab/iptables/rules`
- **Block IP**: `POST /api/lab/iptables/block`
- **Reset Rules**: `POST /api/lab/iptables/reset`

#### Example Rules (POST /api/lab/iptables/rules)
```json
{
  "chain": "INPUT",
  "protocol": "tcp",
  "dest_port": "22",
  "source_ip": "192.168.1.0/24",
  "action": "ACCEPT",
  "comment": "Allow SSH from local network"
}
```

#### Blocking an IP
```json
{
  "ip": "10.0.0.5",
  "duration": 3600,
  "comment": "Block suspicious IP for 1 hour"
}
```

### Manual iptables Usage
```bash
# List all rules
sudo iptables -L -n -v

# Block an IP
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# Allow SSH from local network
sudo iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport 22 -j ACCEPT
```

---

## 2. Network Layer - pfSense Setup

### Prerequisites
- pfSense firewall appliance or VM
- pfSense API package installed (https://github.com/jaredhendrickson13/pfsense-api)
- API key generated

### Configuration
Configure pfSense manager via API:

#### Configure Connection
`POST /api/lab/pfsense/configure`
```json
{
  "base_url": "https://192.168.1.1",
  "api_key": "your_pfsense_api_key"
}
```

#### API Endpoints
- **List Rules**: `GET /api/lab/pfsense/rules`
- **Add Rule**: `POST /api/lab/pfsense/rules`
- **Apply Changes**: `POST /api/lab/pfsense/apply`
- **Status**: `GET /api/lab/pfsense/status`

#### Example Rule (POST /api/lab/pfsense/rules)
```json
{
  "protocol": "tcp",
  "source": "any",
  "destination": "192.168.1.10",
  "port": "443",
  "action": "pass",
  "description": "Allow HTTPS to web server"
}
```

---

## 3. Packet Layer - Scapy Setup

### Prerequisites
- Scapy installed (included in requirements.txt)
- Network interface access (may require root)

### Configuration
Control packet inspection via API:

#### API Endpoints
- **Start Sniffing**: `POST /api/lab/scapy/start`
- **Stop Sniffing**: `POST /api/lab/scapy/stop`
- **Get Captured Packets**: `GET /api/lab/scapy/packets`
- **Generate Test Packet**: `POST /api/lab/scapy/test`

#### Example Usage
```json
// Start sniffing on eth0
{
  "interface": "eth0",
  "filter": "tcp port 80"
}

// Generate test packet
{
  "source_ip": "192.168.1.100",
  "dest_ip": "192.168.1.1",
  "source_port": 12345,
  "dest_port": 80,
  "protocol": "TCP"
}
```

### Manual Scapy Usage
```python
from scapy.all import sniff, IP, TCP

def packet_callback(packet):
    if IP in packet:
        print(f"{packet[IP].src} -> {packet[IP].dst}")
        if TCP in packet:
            print(f"  Port: {packet[TCP].sport} -> {packet[TCP].dport}")

# Start sniffing
sniff(prn=packet_callback, iface="eth0", filter="tcp", store=0)
```

---

## 4. Traffic Analysis & Logging

All attacks and traffic are logged to CSV files in `backend/traffic_data/`:

- `attacks.csv`: All detected attacks with details
- `traffic.csv`: All captured packets

### API Endpoints for Analysis
- **Traffic History**: `GET /api/lab/traffic/history`
- **Traffic Stats**: `GET /api/lab/traffic/statistics`
- **Attack History**: `GET /api/lab/attacks/history`
- **Attack Stats**: `GET /api/lab/attacks/statistics`

---

## 5. Complete Lab Workflow

### Step 1: Start the Backend
```bash
cd backend
source venv/bin/activate
python app.py
```

### Step 2: Start Packet Sniffing
Use the API or frontend to start capturing packets with Scapy.

### Step 3: Configure iptables
Add rules to protect the host.

### Step 4: Configure pfSense
Add rules to protect the network perimeter.

### Step 5: Test with Attacks
Use the attack simulator or manual testing to verify defenses.

---

## 6. Attack Detection Patterns

The SARVA Firewall detects these attack types:
- XSS Injection
- SQL Injection
- Command Injection
- Path Traversal
- SSRF
- XXE
- And many more...

All attacks are logged with timestamp, source IP, payload, confidence, and layer.

---

## 7. Automated Responses

Based on attack severity, the firewall can take these actions:

| Severity | Actions |
|----------|---------|
| Critical | Block IP immediately, notify security team, save evidence |
| High | Block IP for 1 hour, log detailed info, monitor further traffic |
| Medium | Rate limit requests, log details, monitor IP |
| Low | Log details, monitor IP |

---

## 8. Troubleshooting

### iptables Not Working
- Check if running as root/sudo
- Verify no other firewall is conflicting
- Check `dmesg` for kernel errors

### pfSense API Issues
- Verify API package is installed
- Check API key permissions
- Ensure firewall is reachable

### Scapy Sniffing Problems
- Ensure interface name is correct
- Check for permissions (may need root)
- Verify filter syntax (uses BPF)

### Traffic Analysis
- Check `backend/traffic_data/` for log files
- Use the API endpoints to retrieve statistics

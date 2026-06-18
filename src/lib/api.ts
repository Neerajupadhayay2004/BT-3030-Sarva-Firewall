// API Configuration and Integration
const API_BASE_URL = '/api';

// Threat Detection APIs
export const threatAPI = {
  analyzeEmail: async (content: string, sender: string) => {
    const response = await fetch(`${API_BASE_URL}/threats/analyze/email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, sender })
    });
    return response.json();
  },

  analyzeMalware: async (behaviorLog: string) => {
    const response = await fetch(`${API_BASE_URL}/threats/analyze/malware`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ behavior_log: behaviorLog })
    });
    return response.json();
  },

  analyzeNetwork: async (packetData: Record<string, any>) => {
    const response = await fetch(`${API_BASE_URL}/threats/analyze/network`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(packetData)
    });
    return response.json();
  },

  getRecentThreats: async (limit = 10) => {
    const response = await fetch(`${API_BASE_URL}/threats/recent?limit=${limit}`);
    return response.json();
  },

  getThreatTimeline: async (hours = 24) => {
    const response = await fetch(`${API_BASE_URL}/threats/timeline?hours=${hours}`);
    return response.json();
  },

  getStats: async () => {
    const response = await fetch(`${API_BASE_URL}/threats/stats`);
    return response.json();
  }
};

// OSINT APIs
export const osintAPI = {
  investigateIP: async (ip: string) => {
    const response = await fetch(`${API_BASE_URL}/osint/investigate/ip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });
    return response.json();
  },

  investigateFile: async (hash: string) => {
    const response = await fetch(`${API_BASE_URL}/osint/investigate/file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hash })
    });
    return response.json();
  },

  investigateURL: async (url: string) => {
    const response = await fetch(`${API_BASE_URL}/osint/investigate/url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    return response.json();
  },

  shodanSearch: async (query: string) => {
    const response = await fetch(`${API_BASE_URL}/osint/shodan/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    return response.json();
  },

  abuseIPDBCheck: async (ip: string) => {
    const response = await fetch(`${API_BASE_URL}/osint/abuseipdb/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });
    return response.json();
  }
};

// Attack Simulator APIs
export const simulatorAPI = {
  startDDoS: async (targetIP: string, duration = 60) => {
    const response = await fetch(`${API_BASE_URL}/simulator/ddos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_ip: targetIP, duration })
    });
    return response.json();
  },

  startPhishing: async (targetEmail: string, emailCount = 100) => {
    const response = await fetch(`${API_BASE_URL}/simulator/phishing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_email: targetEmail, email_count: emailCount })
    });
    return response.json();
  },

  startMalware: async (systemID: string) => {
    const response = await fetch(`${API_BASE_URL}/simulator/malware`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system_id: systemID })
    });
    return response.json();
  },

  startPortScan: async (targetRange: string) => {
    const response = await fetch(`${API_BASE_URL}/simulator/portscan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_range: targetRange })
    });
    return response.json();
  },

  startSQLi: async (targetURL: string, payloadCount = 50) => {
    const response = await fetch(`${API_BASE_URL}/simulator/sqli`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_url: targetURL, payload_count: payloadCount })
    });
    return response.json();
  }
};

// LLM Assistant APIs
export const llmAPI = {
  analyzeThreat: async (threatData: Record<string, any>) => {
    const response = await fetch(`${API_BASE_URL}/llm/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(threatData)
    });
    return response.json();
  },

  generateReport: async (threatLogs: Array<Record<string, any>>) => {
    const response = await fetch(`${API_BASE_URL}/llm/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threat_logs: threatLogs })
    });
    return response.json();
  },

  chat: async (message: string) => {
    const response = await fetch(`${API_BASE_URL}/llm/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    return response.json();
  },

  getRecommendations: async (threatType: string) => {
    const response = await fetch(`${API_BASE_URL}/llm/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threat_type: threatType })
    });
    return response.json();
  },

  getStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/llm/status`);
    return response.json();
  }
};

// Blockchain APIs
export const blockchainAPI = {
  logThreat: async (threatData: Record<string, any>) => {
    const response = await fetch(`${API_BASE_URL}/blockchain/log/threat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(threatData)
    });
    return response.json();
  },

  verifyThreat: async (threatID: string) => {
    const response = await fetch(`${API_BASE_URL}/blockchain/verify/${threatID}`);
    return response.json();
  },

  getThreatHistory: async (limit = 100) => {
    const response = await fetch(`${API_BASE_URL}/blockchain/history?limit=${limit}`);
    return response.json();
  },

  getNetworkStatus: async () => {
    const response = await fetch(`${API_BASE_URL}/blockchain/network/status`);
    return response.json();
  }
};

// Health Check
export const healthCheck = async () => {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
};

export default {
  threatAPI,
  osintAPI,
  simulatorAPI,
  llmAPI,
  blockchainAPI,
  healthCheck
};

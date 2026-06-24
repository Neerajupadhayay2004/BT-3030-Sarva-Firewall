// API Configuration and Integration
const API_BASE_URL = '/api';

/**
 * Helper to get the JWT token from localStorage
 */
const getAuthToken = () => localStorage.getItem("token");

/**
 * Generic fetch wrapper to include auth headers
 */
export const secureFetch = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };

  const response = await fetch(url, { ...options, headers });
  
  // Handle unauthorized globally
  if (response.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("isAuthenticated");
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }
  
  return response.json();
};

// Auth APIs
export const authAPI = {
  login: async (credentials: Record<string, string>) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    return response.json();
  }
};

// Threat Detection APIs
export const threatAPI = {
  analyzeEmail: async (content: string, sender: string) => {
    return secureFetch(`${API_BASE_URL}/threats/analyze/email`, {
      method: 'POST',
      body: JSON.stringify({ content, sender })
    });
  },

  analyzeMalware: async (behaviorLog: string) => {
    return secureFetch(`${API_BASE_URL}/threats/analyze/malware`, {
      method: 'POST',
      body: JSON.stringify({ behavior_log: behaviorLog })
    });
  },

  analyzeNetwork: async (packetData: Record<string, any>) => {
    return secureFetch(`${API_BASE_URL}/threats/analyze/network`, {
      method: 'POST',
      body: JSON.stringify(packetData)
    });
  },

  getRecentThreats: async (limit = 10) => {
    return secureFetch(`${API_BASE_URL}/threats/recent?limit=${limit}`);
  },

  getThreatTimeline: async (hours = 24) => {
    return secureFetch(`${API_BASE_URL}/threats/timeline?hours=${hours}`);
  },

  getStats: async () => {
    return secureFetch(`${API_BASE_URL}/threats/stats`);
  }
};

// OSINT APIs
export const osintAPI = {
  investigateIP: async (ip: string) => {
    return secureFetch(`${API_BASE_URL}/osint/investigate/ip`, {
      method: 'POST',
      body: JSON.stringify({ ip })
    });
  },

  investigateFile: async (hash: string) => {
    return secureFetch(`${API_BASE_URL}/osint/investigate/file`, {
      method: 'POST',
      body: JSON.stringify({ hash })
    });
  },

  investigateURL: async (url: string) => {
    return secureFetch(`${API_BASE_URL}/osint/investigate/url`, {
      method: 'POST',
      body: JSON.stringify({ url })
    });
  },

  shodanSearch: async (query: string) => {
    return secureFetch(`${API_BASE_URL}/osint/shodan/search`, {
      method: 'POST',
      body: JSON.stringify({ query })
    });
  },

  abuseIPDBCheck: async (ip: string) => {
    return secureFetch(`${API_BASE_URL}/osint/abuseipdb/check`, {
      method: 'POST',
      body: JSON.stringify({ ip })
    });
  }
};

// Attack Simulator APIs
export const simulatorAPI = {
  startDDoS: async (targetIP: string, duration = 60) => {
    return secureFetch(`${API_BASE_URL}/simulator/ddos`, {
      method: 'POST',
      body: JSON.stringify({ target_ip: targetIP, duration })
    });
  },

  startPhishing: async (targetEmail: string, emailCount = 100) => {
    return secureFetch(`${API_BASE_URL}/simulator/phishing`, {
      method: 'POST',
      body: JSON.stringify({ target_email: targetEmail, email_count: emailCount })
    });
  },

  startMalware: async (systemID: string) => {
    return secureFetch(`${API_BASE_URL}/simulator/malware`, {
      method: 'POST',
      body: JSON.stringify({ system_id: systemID })
    });
  },

  startPortScan: async (targetRange: string) => {
    return secureFetch(`${API_BASE_URL}/simulator/portscan`, {
      method: 'POST',
      body: JSON.stringify({ target_range: targetRange })
    });
  },

  startSQLi: async (targetURL: string, payloadCount = 50) => {
    return secureFetch(`${API_BASE_URL}/simulator/sqli`, {
      method: 'POST',
      body: JSON.stringify({ target_url: targetURL, payload_count: payloadCount })
    });
  }
};

// LLM Assistant APIs
export const llmAPI = {
  analyzeThreat: async (threatData: Record<string, any>) => {
    return secureFetch(`${API_BASE_URL}/advanced/llm/analyze-threat`, {
      method: 'POST',
      body: JSON.stringify(threatData)
    });
  },

  getStatus: async () => {
    return secureFetch(`${API_BASE_URL}/advanced/llm/status`);
  },

  getRecommendations: async (threatType: string, severity: string) => {
    return secureFetch(`${API_BASE_URL}/advanced/llm/recommendations`, {
      method: 'POST',
      body: JSON.stringify({ threat_type: threatType, severity })
    });
  }
};

// Blockchain APIs
export const blockchainAPI = {
  logThreat: async (threatData: Record<string, any>) => {
    return secureFetch(`${API_BASE_URL}/blockchain/log/threat`, {
      method: 'POST',
      body: JSON.stringify(threatData)
    });
  },

  getThreatHistory: async (limit = 100) => {
    return secureFetch(`${API_BASE_URL}/blockchain/history?limit=${limit}`);
  },

  getNetworkStatus: async () => {
    return secureFetch(`${API_BASE_URL}/blockchain/network/status`);
  }
};

// Health Check
export const healthCheck = async () => {
  return secureFetch(`${API_BASE_URL}/health`);
};

export default {
  authAPI,
  threatAPI,
  osintAPI,
  simulatorAPI,
  llmAPI,
  blockchainAPI,
  healthCheck
};

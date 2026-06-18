import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Shield, Activity, AlertTriangle, CheckCircle, TrendingUp, Database, Menu, LogOut, RefreshCw, XCircle, Wifi, Zap, Globe } from "lucide-react";
import { io } from "socket.io-client";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import StatsCard from "@/components/dashboard/StatsCard";
import AttackChart from "@/components/dashboard/AttackChart";
import AttackDistribution from "@/components/dashboard/AttackDistribution";
import RecentAttacks from "@/components/dashboard/RecentAttacks";
import BlockedIPsTable from "@/components/dashboard/BlockedIPsTable";
import TrendAnalysis from "@/components/dashboard/TrendAnalysis";
import GeographicInsights from "@/components/dashboard/GeographicInsights";
import TimelineChart from "@/components/dashboard/TimelineChart";
import { threatAPI, blockchainAPI } from "@/lib/api";
import { sanitizeHtml, detectXss } from "@/lib/xssProtection";
import { toast } from "sonner";

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<any>(null);
  const [apiData, setApiData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [xssStats, setXssStats] = useState<any>({ total_attempts: 0, blocked_count: 0, recent_attacks: [] });
  const [firewallStats, setFirewallStats] = useState<any>({ 
    stats: { total_packets: 0, blocked_packets: 0, allowed_packets: 0, active_rules: 12 },
    blacklist_count: 0,
    recent_traffic: [] 
  });
  const [socketConnected, setSocketConnected] = useState(false);
  const socketRef = useRef<any>(null);

  const safeData = data ?? { attack_categories: {}, worked: {} };
  const [investigatingIp, setInvestigatingIp] = useState<string | null>(null);
  const [osintResults, setOsintResults] = useState<any>(null);
  
  // Safely read and sanitize query parameters, detect XSS
  const rawMsg = searchParams.get('msg');
  const sanitizedMsg = rawMsg ? sanitizeHtml(rawMsg) : null;
  const showDataWarning = !data && !loading;

  // Check all query params for XSS and log if detected
  useEffect(() => {
    const checkForXss = async () => {
      for (const [key, value] of searchParams) {
        const fullParam = `${key}=${value}`;
        if (detectXss(value)) {
          console.log(`XSS detected in query param: ${key}=${value}`);
          // Log to XSS tracker
          try {
            await fetch('/api/advanced/xss/log', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                payload: fullParam,
                source: 'query-param'
              })
            });
          } catch (e) {
            console.error('Failed to log XSS attack:', e);
          }
          // Also log as firewall attack
          try {
            await fetch('/api/advanced/firewall/log-attack', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                attack_type: 'xss',
                payload: fullParam,
                confidence: 0.98
              })
            });
          } catch (e) {
            console.error('Failed to log firewall attack:', e);
          }
        }
      }
    };
    checkForXss();
  }, [searchParams]);

  const investigateIp = async (ip: string) => {
    setInvestigatingIp(ip);
    setOsintResults(null);
    try {
      const res = await fetch('/api/osint/investigate/ip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip })
      });
      const data = await res.json();
      setOsintResults(data);
    } catch (e) {
      console.error('Failed to investigate IP:', e);
    } finally {
      setInvestigatingIp(null);
    }
  };

  // Fetch firewall stats
  const fetchFirewallStats = async () => {
    try {
      const res = await fetch('/api/advanced/firewall/stats');
      const result = await res.json();
      if (result.status === 'success') {
        setFirewallStats(result);
      }
    } catch (e) {
      console.error("Failed to fetch firewall stats:", e);
    }
  };

  // Fetch XSS stats
  const fetchXssStats = async () => {
    try {
      const res = await fetch('/api/advanced/xss/stats');
      const result = await res.json();
      if (result.status === 'success' && result.stats) {
        setXssStats(result.stats);
      }
    } catch (e) {
      console.error("Failed to fetch XSS stats:", e);
    }
  };

  // Initialize WebSocket connection
  useEffect(() => {
    const isAuth = localStorage.getItem("isAuthenticated");
    if (!isAuth) {
      navigate("/");
      return;
    }

    // Load local database.json
    fetch("/database.json")
      .then((res) => res.json())
      .then((jsonData) => setData(jsonData))
      .catch((err) => console.error("Error loading database:", err));

    // Fetch data from backend API
    fetchBackendData();
    
    // Initial fetch of stats
    fetchFirewallStats();
    fetchXssStats();
    
    // Poll stats every 5 seconds (as backup to WebSocket)
    const interval = setInterval(() => {
      fetchFirewallStats();
      fetchXssStats();
    }, 5000);
    
    // Setup WebSocket for real-time updates
    try {
      const socket = io('http://localhost:5000');
      socketRef.current = socket;
      
      socket.on('connect', () => {
        setSocketConnected(true);
        console.log('✅ Firewall WebSocket Connected');
        toast.success("Real-time firewall connection active");
      });
      
      socket.on('disconnect', () => {
        setSocketConnected(false);
        console.log('❌ Firewall WebSocket Disconnected');
      });
      
      socket.on('firewall_traffic', (data: any) => {
        const packet = data.packet;
        
        if (packet.action === 'BLOCKED') {
          toast.error(`🚨 ${packet.type.toUpperCase()} ATTACK BLOCKED!`, {
            description: `From IP: ${packet.source_ip}`,
            duration: 4000,
          });
        }
        
        // Real-time update of the traffic list
        setFirewallStats((prev: any) => ({
          ...prev,
          stats: {
            ...prev.stats,
            total_packets: prev.stats.total_packets + 1,
            blocked_packets: packet.action === 'BLOCKED' ? prev.stats.blocked_packets + 1 : prev.stats.blocked_packets,
            allowed_packets: packet.action === 'ALLOWED' ? prev.stats.allowed_packets + 1 : prev.stats.allowed_packets,
          },
          recent_traffic: [packet, ...(prev.recent_traffic || [])].slice(0, 30)
        }));
      });

      socket.on('firewall_attack', (data: any) => {
        // Handle direct attack logs if still used
        fetchFirewallStats();
      });

      socket.on('connection_response', (data: any) => {
        console.log('Server connection response:', data);
      });
    } catch (e) {
      console.error('Failed to setup WebSocket:', e);
    }
    
    return () => {
      clearInterval(interval);
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [navigate]);

  const fetchBackendData = async () => {
    try {
      setLoading(true);
      
      // Fetch threat statistics
      const stats = await threatAPI.getStats();
      const recentThreats = await threatAPI.getRecentThreats(10);
      const timeline = await threatAPI.getThreatTimeline(24);
      const blockchainHistory = await blockchainAPI.getThreatHistory(50);

      setApiData({
        stats,
        recentThreats,
        timeline,
        blockchainHistory
      });

      toast.success("Dashboard data updated successfully");
    } catch (error) {
      console.error("Error fetching backend data:", error);
      toast.error("Failed to fetch backend data. Using local data.");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchBackendData();
    setRefreshing(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    navigate("/");
  };



  if (!data && loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Activity className="w-16 h-16 text-primary animate-pulse mx-auto" />
          <p className="text-muted-foreground">Loading firewall data...</p>
        </div>
      </div>
    );
  }

  // Use API data if available, otherwise fall back to local data
  const displayData = apiData?.stats || {
    total_threats_detected: 0,
    threats_blocked: 0,
    critical_threats: 0,
    phishing_emails: 0,
    malware_detected: 0,
    network_attacks: 0,
    system_uptime: "99.8%",
    last_update: new Date().toISOString()
  };

  // Calculate statistics
  const totalAttacks = displayData.total_threats_detected ||
    (Object.values(safeData.attack_categories) as any[]).reduce((sum: number, category: any) => {
      return sum + Object.keys(category).length;
    }, 0);

  const blockedIPs = displayData.threats_blocked || Object.keys(safeData.worked).length;

  const attackTypes = displayData.critical_threats ||
    Object.entries(safeData.attack_categories)
      .filter(([_, attacks]: any) => Object.keys(attacks).length > 0)
      .length;

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-10 h-10 text-primary cyber-glow" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              SARVA Firewall Dashboard
            </h1>
          </div>
          <p className="text-muted-foreground">AI-powered real-time threat monitoring and analytics</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-primary/30 h-9 px-3 md:px-4"
          >
            <RefreshCw className={`w-4 h-4 md:mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="hidden md:inline">Refresh</span>
          </Button>
          <div className="flex items-center gap-1 text-xs text-muted-foreground mr-2">
            <Wifi className={`w-3 h-3 ${socketConnected ? 'text-green-500' : 'text-red-500'}`} />
            {socketConnected ? 'Live' : 'Disconnected'}
          </div>
          <Button variant="outline" onClick={() => navigate("/blockchain")} className="border-primary/30 h-9 px-3 md:px-4">
            <Database className="w-4 h-4 md:mr-2" />
            <span className="hidden md:inline">Blockchain</span>
          </Button>
          <Button variant="outline" onClick={() => navigate("/simulator")} className="border-primary/30 h-9 px-3 md:px-4">
            <Activity className="w-4 h-4 md:mr-2" />
            <span className="hidden md:inline">Simulator</span>
          </Button>
          <Button variant="outline" onClick={() => navigate("/learning")} className="border-primary/30 h-9 px-3 md:px-4">
            <TrendingUp className="w-4 h-4 md:mr-2" />
            <span className="hidden md:inline">Learning</span>
          </Button>
          <Button variant="destructive" onClick={handleLogout} className="h-9 px-3 md:px-4">
            <LogOut className="w-4 h-4 md:mr-2" />
            <span className="hidden md:inline">Logout</span>
          </Button>
        </div>
      </header>

      {/* Safe Message Display Area */}
      {sanitizedMsg && (
        <div className="mb-6 rounded-lg border border-green-500/30 bg-green-500/10 p-4">
          <h4 className="font-semibold text-green-400 mb-2">✅ Sanitized URL Message:</h4>
          <span className="text-foreground">{rawMsg}</span>
          {rawMsg && rawMsg !== sanitizedMsg && (
            <div className="mt-3 pt-3 border-t border-green-500/20">
              <p className="text-sm text-muted-foreground mb-1">🔒 Original malicious payload was sanitized:</p>
              <code className="text-xs bg-black/30 px-2 py-1 rounded text-red-400">{rawMsg}</code>
            </div>
          )}
        </div>
      )}

      {showDataWarning && (
        <div className="mb-6 rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-100">
          Local dashboard data could not be loaded yet. The page is using empty fallback data until the source becomes available.
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <StatsCard
          title="Total Packets Monitored"
          value={firewallStats.stats.total_packets.toString()}
          icon={Activity}
          trend="Live traffic feed"
          trendUp={true}
          color="primary"
        />
        <StatsCard
          title="Threats Blocked"
          value={firewallStats.stats.blocked_packets.toString()}
          icon={Shield}
          trend="Real-time protection"
          trendUp={true}
          color="success"
        />
        <StatsCard
          title="Active Blacklist"
          value={firewallStats.blacklist_count.toString()}
          icon={XCircle}
          trend="IPs quarantined"
          color="destructive"
        />
        <StatsCard
          title="Allowed Traffic"
          value={firewallStats.stats.allowed_packets.toString()}
          icon={CheckCircle}
          trend="Verified safe"
          color="success"
        />
        <StatsCard
          title="Firewall Rules"
          value={firewallStats.stats.active_rules.toString()}
          icon={Database}
          trend="Active policies"
          color="primary"
        />
      </div>



      {/* Data Visualization Tabs */}
      <Tabs defaultValue="logs" className="mb-8">
        <TabsList className="flex flex-wrap w-full lg:w-auto h-auto bg-transparent gap-2 mb-4">
          <TabsTrigger value="logs" className="flex-1 lg:flex-none py-2 px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground border border-primary/20">🔥 Live Traffic Feed</TabsTrigger>
          <TabsTrigger value="overview" className="flex-1 lg:flex-none py-2 px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground border border-primary/20">Overview</TabsTrigger>
          <TabsTrigger value="trends" className="flex-1 lg:flex-none py-2 px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground border border-primary/20">Trends</TabsTrigger>
          <TabsTrigger value="geographic" className="flex-1 lg:flex-none py-2 px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground border border-primary/20">Geographic</TabsTrigger>
          <TabsTrigger value="timeline" className="flex-1 lg:flex-none py-2 px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground border border-primary/20">Timeline</TabsTrigger>
        </TabsList>
        
        <TabsContent value="logs" className="mt-6">
          <Card className="cyber-border bg-card/50 backdrop-blur-sm mb-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-primary" />
                Live Network Traffic Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              {firewallStats.recent_traffic && firewallStats.recent_traffic.length > 0 ? (
                <div className="space-y-4">
                  {firewallStats.recent_traffic.map((packet: any, idx: number) => (
                    <div key={packet.id || idx} className={`border p-5 rounded-xl animate-in fade-in slide-in-from-top-4 duration-500 ${
                      packet.action === 'BLOCKED' ? 'border-red-500/30 bg-red-500/5' : 'border-green-500/10 bg-green-500/5'
                    }`}>
                      <div className="flex justify-between items-start mb-4 flex-wrap gap-4">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            packet.action === 'BLOCKED' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                          }`}>
                            <Shield className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <h4 className="font-bold text-lg uppercase tracking-wider">{packet.type}</h4>
                              <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                                packet.action === 'BLOCKED' ? 'bg-red-500/30 text-red-400 animate-pulse' : 'bg-green-500/30 text-green-400'
                              }`}>
                                {packet.action}
                              </span>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Blocked at: {new Date(packet.timestamp).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <div>
                            <p className="text-xs font-mono text-muted-foreground mb-1">Source IP</p>
                            <code className={`font-bold px-2 py-1 rounded ${
                              packet.action === 'BLOCKED' ? 'text-red-400 bg-red-500/10' : 'text-green-400 bg-green-500/10'
                            }`}>{packet.source_ip}</code>
                          </div>
                          <Button 
                            variant="outline"
                            size="sm"
                            onClick={() => investigateIp(packet.source_ip)}
                            disabled={investigatingIp === packet.source_ip}
                            className="border-primary/30 text-xs"
                          >
                            {investigatingIp === packet.source_ip ? 'Investigating...' : 'Investigate IP'}
                          </Button>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div className={`p-3 rounded-lg border ${
                          packet.action === 'BLOCKED' ? 'bg-red-900/10 border-red-500/20' : 'bg-green-900/10 border-green-500/20'
                        }`}>
                          <h5 className={`text-xs font-bold mb-2 flex items-center gap-2 ${
                            packet.action === 'BLOCKED' ? 'text-red-400' : 'text-green-400'
                          }`}>
                            <Activity className="w-3 h-3" />
                            AI VERDICT
                          </h5>
                          <p className="text-sm font-semibold text-foreground mb-1">{packet.ai_verdict}</p>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                              <div className={`h-full ${packet.action === 'BLOCKED' ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${packet.confidence * 100}%` }}></div>
                            </div>
                            <span className="text-[10px] font-mono">{(packet.confidence * 100).toFixed(1)}% confidence</span>
                          </div>
                        </div>
                        <div className={`p-3 rounded-lg border ${
                          packet.action === 'BLOCKED' ? 'bg-red-900/10 border-red-500/20' : 'bg-green-900/10 border-green-500/20'
                        }`}>
                          <h5 className={`text-xs font-bold mb-2 flex items-center gap-2 ${
                            packet.action === 'BLOCKED' ? 'text-red-400' : 'text-green-400'
                          }`}>
                            <CheckCircle className="w-3 h-3" />
                            ACTION TAKEN
                          </h5>
                          <p className="text-sm font-semibold text-foreground">{packet.action_taken}</p>
                        </div>
                      </div>

                      {packet.packet_details && (
                        <div className="bg-black/40 rounded-lg overflow-hidden border border-white/5">
                          <div className="bg-white/5 px-3 py-1.5 flex justify-between items-center">
                            <span className="text-[10px] font-bold tracking-widest text-muted-foreground uppercase">Deep Packet Inspection (L7)</span>
                            <span className="text-[10px] font-mono text-primary font-bold">{packet.packet_details.protocol}</span>
                          </div>
                          <div className="p-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-[10px]">
                            <div>
                              <span className="text-muted-foreground block mb-1">Source Port</span>
                              <span className="font-mono text-foreground">{packet.packet_details.source_port}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground block mb-1">TCP Flags</span>
                              <span className="font-mono text-primary font-bold">{packet.packet_details.flags}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground block mb-1">Entropy Score</span>
                              <span className={`font-mono ${packet.packet_details.entropy_score > 5 ? 'text-red-400' : 'text-green-400'}`}>
                                {packet.packet_details.entropy_score}
                              </span>
                            </div>
                            <div>
                              <span className="text-muted-foreground block mb-1">Payload</span>
                              <span className="font-mono text-foreground">{packet.packet_details.payload_size} bytes</span>
                            </div>
                          </div>
                          <div className="px-3 pb-3">
                            <span className="text-muted-foreground block mb-1 text-[10px]">Raw Payload Data</span>
                            <div className={`p-2 rounded font-mono text-[10px] break-all border ${
                              packet.action === 'BLOCKED' ? 'bg-red-500/5 text-red-300 border-red-500/10' : 'bg-green-500/5 text-green-300 border-green-500/10'
                            }`}>
                              {packet.payload}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <Activity className="w-12 h-12 mx-auto mb-4 animate-pulse" />
                  <p>Starting live traffic capture...</p>
                </div>
              )}
            </CardContent>
          </Card>

          {osintResults && (
            <Card className="cyber-border bg-card/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary" />
                  OSINT Investigation Results for {osintResults.ip}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="border border-primary/20 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-primary mb-3 flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      AbuseIPDB Reputation
                    </h4>
                    {osintResults.abuseipdb?.data ? (
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Abuse Confidence Score:</span>
                          <span className={`font-bold ${osintResults.abuseipdb.data.abuseConfidenceScore > 50 ? 'text-red-400' : 'text-green-400'}`}>
                            {osintResults.abuseipdb.data.abuseConfidenceScore}/100
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Total Reports:</span>
                          <span className="font-semibold">{osintResults.abuseipdb.data.totalReports}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Last Reported:</span>
                          <span className="font-semibold">{osintResults.abuseipdb.data.lastReportedAt}</span>
                        </div>
                        {osintResults.abuseipdb.data.countryCode && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Country:</span>
                            <span className="font-semibold">{osintResults.abuseipdb.data.countryCode}</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">No AbuseIPDB data available</p>
                    )}
                  </div>

                  <div className="border border-primary/20 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-primary mb-3 flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      Shodan Information
                    </h4>
                    {osintResults.shodan && !osintResults.shodan.error ? (
                      <div className="space-y-2 text-xs">
                        {osintResults.shodan.org && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Organization:</span>
                            <span className="font-semibold">{osintResults.shodan.org}</span>
                          </div>
                        )}
                        {osintResults.shodan.isp && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">ISP:</span>
                            <span className="font-semibold">{osintResults.shodan.isp}</span>
                          </div>
                        )}
                        {osintResults.shodan.ports && (
                          <div>
                            <span className="text-muted-foreground">Open Ports:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {osintResults.shodan.ports.map((port: number) => (
                                <span key={port} className="px-1.5 py-0.5 bg-primary/10 rounded text-primary font-mono">
                                  {port}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">No Shodan data available</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AttackChart data={safeData} />
            <AttackDistribution data={safeData} />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RecentAttacks data={safeData} />
            <BlockedIPsTable data={safeData} />
          </div>
        </TabsContent>

        <TabsContent value="threats" className="mt-6">
          <div className="cyber-border rounded-lg p-6 bg-card/50 backdrop-blur-sm">
            <h3 className="text-lg font-bold mb-4">Recent API-Detected Threats</h3>
            {apiData?.recentThreats && apiData.recentThreats.length > 0 ? (
              <div className="space-y-4">
                {apiData.recentThreats.slice(0, 5).map((threat: any, idx: number) => (
                  <div key={idx} className="border border-primary/20 rounded p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold capitalize">{threat.type}</p>
                        <p className="text-sm text-muted-foreground">{threat.status}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        threat.status === 'detected' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                      }`}>
                        {threat.action?.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-8">No threats detected via API</p>
            )}
          </div>
        </TabsContent>

        <TabsContent value="trends" className="mt-6">
          <TrendAnalysis data={safeData} />
        </TabsContent>

        <TabsContent value="geographic" className="mt-6">
          <GeographicInsights data={safeData} />
        </TabsContent>

        <TabsContent value="timeline" className="mt-6">
          <TimelineChart data={safeData} />
        </TabsContent>
      </Tabs>

      {/* Blockchain Verification Section */}
      <div className="cyber-border rounded-lg p-6 bg-card/50 backdrop-blur-sm">
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-6 h-6 text-primary" />
          <h2 className="text-2xl font-bold text-foreground">Blockchain Verification</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-1">Total Records</p>
            <p className="text-2xl font-bold text-primary">{totalAttacks}</p>
          </div>
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-1">Chain Status</p>
            <p className="text-2xl font-bold text-success flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Verified
            </p>
          </div>
          <div className="bg-muted/50 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-1">Network</p>
            <p className="text-sm font-mono text-foreground">Polygon Amoy</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

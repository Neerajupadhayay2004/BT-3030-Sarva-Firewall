import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertCircle, TrendingUp, Activity, Zap } from 'lucide-react';

const AdvancedDashboard = () => {
  const [threatData, setThreatData] = useState([]);
  const [modelComparison, setModelComparison] = useState({});
  const [threatDistribution, setThreatDistribution] = useState({});
  const [liveMetrics, setLiveMetrics] = useState({
    totalThreats: 0,
    avgConfidence: 0,
    criticalCount: 0,
    blockRate: 0
  });
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState('ensemble');
  const [llmStatus, setLlmStatus] = useState({ running: false, model: 'mistral' });
  const [showLLMPanel, setShowLLMPanel] = useState(false);

  useEffect(() => {
    fetchThreatTimeline();
    fetchModelComparison();
    fetchThreatDistribution();
    fetchLLMStatus();

    // Real-time updates
    const interval = setInterval(() => {
      fetchThreatTimeline();
      fetchModelComparison();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const fetchThreatTimeline = async () => {
    try {
      const response = await fetch('/api/advanced/graphs/threat-timeline');
      const data = await response.json();
      setThreatData(data.timeline || []);
      setLiveMetrics({
        totalThreats: data.total_threats,
        avgConfidence: (data.average_confidence * 100).toFixed(2),
        criticalCount: data.threat_breakdown?.CRITICAL || 0,
        blockRate: ((data.threat_breakdown?.CRITICAL || 0) / (data.total_threats || 1) * 100).toFixed(2)
      });
      setLoading(false);
    } catch (error) {
      console.error('Error fetching threat data:', error);
    }
  };

  const fetchModelComparison = async () => {
    try {
      const response = await fetch('/api/advanced/graphs/model-comparison');
      const data = await response.json();
      setModelComparison(data.model_comparison || {});
    } catch (error) {
      console.error('Error fetching model comparison:', error);
    }
  };

  const fetchThreatDistribution = async () => {
    try {
      const response = await fetch('/api/advanced/graphs/threat-distribution');
      const data = await response.json();
      
      const pieData = Object.entries(data.distribution || {}).map(([key, value]) => ({
        name: key,
        value: value,
        percentage: data.percentages[key]
      }));
      
      setThreatDistribution(pieData);
    } catch (error) {
      console.error('Error fetching threat distribution:', error);
    }
  };

  const fetchLLMStatus = async () => {
    try {
      const response = await fetch('/api/advanced/llm/status');
      const data = await response.json();
      setLlmStatus({
        running: data.llm_running,
        model: data.current_model
      });
    } catch (error) {
      console.error('Error fetching LLM status:', error);
    }
  };

  const COLORS = {
    LOW: '#10b981',
    MEDIUM: '#f59e0b',
    HIGH: '#ef4444',
    CRITICAL: '#8b5cf6'
  };

  const trainModels = async () => {
    try {
      const response = await fetch('/api/advanced/models/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          csv_path: '/home/neeraj/Downloads/archive/log2.csv'
        })
      });
      const data = await response.json();
      alert(`Training complete!\n${JSON.stringify(data.results, null, 2)}`);
    } catch (error) {
      alert(`Training failed: ${error.message}`);
    }
  };

  const startLLM = async () => {
    try {
      const response = await fetch('/api/advanced/llm/start', { method: 'POST' });
      const data = await response.json();
      setLlmStatus({ ...llmStatus, running: data.running });
      alert(data.message);
    } catch (error) {
      alert(`Failed to start LLM: ${error.message}`);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading advanced dashboard...</div>;
  }

  return (
    <div className="w-full bg-slate-950 text-white p-6 space-y-6 max-h-screen overflow-auto">
      {/* Header with Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-4 rounded-lg border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Threats</p>
              <p className="text-3xl font-bold text-white">{liveMetrics.totalThreats}</p>
            </div>
            <AlertCircle className="text-red-500" size={32} />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-4 rounded-lg border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Avg Confidence</p>
              <p className="text-3xl font-bold text-white">{liveMetrics.avgConfidence}%</p>
            </div>
            <TrendingUp className="text-blue-500" size={32} />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-4 rounded-lg border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Critical</p>
              <p className="text-3xl font-bold text-purple-400">{liveMetrics.criticalCount}</p>
            </div>
            <Zap className="text-purple-500" size={32} />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-4 rounded-lg border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Block Rate</p>
              <p className="text-3xl font-bold text-orange-400">{liveMetrics.blockRate}%</p>
            </div>
            <Activity className="text-orange-500" size={32} />
          </div>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-4 flex-wrap">
        <button
          onClick={trainModels}
          className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 px-6 py-2 rounded-lg font-semibold transition"
        >
          🧠 Train All Models
        </button>
        <button
          onClick={startLLM}
          className={`px-6 py-2 rounded-lg font-semibold transition ${
            llmStatus.running 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-gray-600 hover:bg-gray-700'
          }`}
        >
          {llmStatus.running ? '✓' : '○'} LLM: {llmStatus.model}
        </button>
        <button
          onClick={() => setShowLLMPanel(!showLLMPanel)}
          className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg font-semibold transition"
        >
          {showLLMPanel ? 'Hide' : 'Show'} LLM Panel
        </button>
      </div>

      {/* Threat Timeline Graph */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h2 className="text-xl font-bold mb-4">Real-time Threat Timeline</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={threatData.slice(-50)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="timestamp" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} />
            <Legend />
            <Line
              type="monotone"
              dataKey="confidence"
              stroke="#3b82f6"
              dot={false}
              name="Confidence Score"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Model Comparison */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <h2 className="text-xl font-bold mb-4">Model Performance</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={Object.entries(modelComparison).map(([model, metrics]) => ({
              model,
              average: (metrics.average * 100).toFixed(2),
              count: metrics.count
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="model" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} />
              <Bar dataKey="average" fill="#8b5cf6" name="Avg Confidence %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <h2 className="text-xl font-bold mb-4">Threat Distribution</h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={threatDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name} ${percentage.toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {threatDistribution.map((entry) => (
                  <Cell key={`cell-${entry.name}`} fill={COLORS[entry.name]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* LLM Analysis Panel */}
      {showLLMPanel && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <h2 className="text-xl font-bold mb-4">🤖 AI-Powered Threat Analysis</h2>
          <div className="bg-slate-900 p-4 rounded border border-slate-700 min-h-32">
            <p className="text-slate-300">
              {llmStatus.running 
                ? `LLM ready: ${llmStatus.model}\nAnalyzing threats with AI intelligence...` 
                : 'LLM not running. Click "Start LLM" to enable AI analysis.'}
            </p>
          </div>
        </div>
      )}

      {/* Recent Threats Table */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h2 className="text-xl font-bold mb-4">Recent Threats (Last 10)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-600">
              <tr>
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Confidence</th>
                <th className="text-left p-2">Level</th>
              </tr>
            </thead>
            <tbody>
              {threatData.slice(-10).reverse().map((threat, i) => (
                <tr key={i} className="border-b border-slate-700 hover:bg-slate-700">
                  <td className="p-2 text-slate-300">{new Date(threat.timestamp).toLocaleTimeString()}</td>
                  <td className="p-2">{(threat.confidence * 100).toFixed(2)}%</td>
                  <td className="p-2">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      threat.threat_level === 'CRITICAL' ? 'bg-purple-600' :
                      threat.threat_level === 'HIGH' ? 'bg-red-600' :
                      threat.threat_level === 'MEDIUM' ? 'bg-orange-600' :
                      'bg-green-600'
                    }`}>
                      {threat.threat_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdvancedDashboard;

"""
Local LLM Integration using Ollama
Provides threat analysis, recommendations, and intelligent insights
"""

import requests
import logging
import json
from typing import Optional, Dict, Any
from functools import lru_cache
import subprocess
import time

logger = logging.getLogger(__name__)


class LocalLLMService:
    """Integration with local Ollama LLM"""
    
    # Supported models
    MODELS = {
        'llama3.2': {
            'name': 'llama3.2:latest',
            'speed': 'medium',
            'quality': 'excellent',
            'memory': '2GB'
        },
        'mistral': {
            'name': 'mistral:latest',
            'speed': 'fast',
            'quality': 'good',
            'memory': '7GB'
        },
        'neural-chat': {
            'name': 'neural-chat:latest',
            'speed': 'very_fast',
            'quality': 'good',
            'memory': '7GB'
        },
        'orca-mini': {
            'name': 'orca-mini:latest',
            'speed': 'fast',
            'quality': 'good',
            'memory': '3GB'
        },
        'llama2': {
            'name': 'llama2:latest',
            'speed': 'medium',
            'quality': 'excellent',
            'memory': '13GB'
        }
    }
    
    def __init__(self, base_url='http://localhost:11434', model='llama3.2'):
        self.base_url = base_url
        self.model = model
        self.is_running = False
        self._check_ollama_running()
    
    def _check_ollama_running(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                self.is_running = True
                logger.info("Ollama is running")
                return True
        except Exception as e:
            logger.warning(f"Ollama not running: {str(e)}")
            self.is_running = False
        return False
    
    def start_ollama(self):
        """Start Ollama service if not running"""
        if self.is_running:
            return True
        
        try:
            logger.info("Starting Ollama service...")
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            time.sleep(3)
            return self._check_ollama_running()
        except Exception as e:
            logger.error(f"Failed to start Ollama: {str(e)}")
            return False
    
    def pull_model(self, model_name: str = None):
        """Download and setup a model"""
        model = model_name or self.model
        
        try:
            logger.info(f"Pulling model: {model}...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.MODELS.get(model, {}).get('name', model)},
                timeout=300
            )
            
            if response.status_code == 200:
                logger.info(f"Model {model} pulled successfully")
                return True
            else:
                logger.error(f"Failed to pull model: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
            return False
    
    def analyze_threat(self, threat_data: Dict[str, Any]) -> str:
        """Use LLM to analyze threat data"""
        if not self.is_running:
            return self._fallback_analysis(threat_data)
        
        prompt = self._format_threat_analysis_prompt(threat_data)
        return self.generate_response(prompt)
    
    def _format_threat_analysis_prompt(self, threat_data: Dict) -> str:
        """Format threat data for LLM analysis"""
        return f"""
You are a cybersecurity expert analyzing network traffic threats. Analyze the following threat data and provide:
1. Threat Assessment (Low/Medium/High/Critical)
2. Attack Pattern Analysis
3. Recommended Mitigation Steps
4. Investigation Recommendations

THREAT DATA:
- Source Port: {threat_data.get('source_port')}
- Destination Port: {threat_data.get('dest_port')}
- Bytes Transferred: {threat_data.get('bytes')}
- Packets: {threat_data.get('packets')}
- Duration: {threat_data.get('elapsed_time')} seconds
- Confidence Score: {threat_data.get('confidence', 0.0):.2%}
- Model Prediction: {threat_data.get('prediction')}

Provide a concise but detailed analysis.
"""
    
    def get_recommendations(self, threat_type: str, severity: str) -> str:
        """Get AI-powered recommendations for threat response"""
        if not self.is_running:
            return self._fallback_recommendation(threat_type, severity)
        
        prompt = f"""
As a cybersecurity incident response expert, provide tactical recommendations for:
Threat Type: {threat_type}
Severity Level: {severity}

Include:
1. Immediate containment steps
2. Detection methods
3. Long-term prevention measures
4. Tools and technologies to deploy

Keep recommendations practical and actionable.
"""
        return self.generate_response(prompt)
    
    def explain_prediction(self, model_name: str, prediction_data: Dict) -> str:
        """Use LLM to explain ML model predictions"""
        if not self.is_running:
            return "LLM not available"
        
        prompt = f"""
Explain this machine learning model prediction in simple terms:
Model: {model_name}
Features: {json.dumps(prediction_data.get('features', {}), indent=2)}
Prediction: {prediction_data.get('prediction')}
Confidence: {prediction_data.get('confidence', 0.0):.2%}

What features are most important to this prediction?
"""
        return self.generate_response(prompt)
    
    def generate_response(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response using Ollama LLM"""
        if not self.is_running:
            logger.warning("Ollama not running, using fallback")
            return "LLM service unavailable"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.MODELS.get(self.model, {}).get('name', self.model),
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"LLM error: {response.text}")
                return "Error generating response"
        except requests.Timeout:
            logger.error("LLM request timeout")
            return "LLM response timeout"
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}")
            return f"Error: {str(e)}"
    
    def _fallback_analysis(self, threat_data: Dict) -> str:
        """Fallback analysis when LLM not available"""
        severity = threat_data.get('confidence', 0.0)
        if severity > 0.8:
            level = "CRITICAL"
        elif severity > 0.6:
            level = "HIGH"
        elif severity > 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        return f"""
AUTOMATED THREAT ANALYSIS (LLM Unavailable)
===========================================
Threat Level: {level}
Confidence: {severity:.2%}

Source: {threat_data.get('source_port')}:{threat_data.get('src_ip', 'unknown')}
Destination: {threat_data.get('dest_port')}:{threat_data.get('dst_ip', 'unknown')}
Data Volume: {threat_data.get('bytes')} bytes
Duration: {threat_data.get('elapsed_time')} seconds

Recommended Action: {'BLOCK' if severity > 0.6 else 'MONITOR'}
"""
    
    def _fallback_recommendation(self, threat_type: str, severity: str) -> str:
        """Fallback recommendations"""
        recommendations = {
            'DDoS': [
                'Enable DDoS protection/mitigation',
                'Rate limit suspicious IPs',
                'Increase bandwidth capacity',
                'Implement traffic filtering'
            ],
            'Port Scan': [
                'Block scanning IP address',
                'Enable port security',
                'Review firewall rules',
                'Monitor for follow-up attacks'
            ],
            'Data Exfiltration': [
                'Immediately isolate affected system',
                'Analyze data access logs',
                'Enable egress filtering',
                'Deploy DLP solution'
            ],
            'default': [
                'Investigate source IP',
                'Review network logs',
                'Apply security patches',
                'Enable monitoring'
            ]
        }
        
        steps = recommendations.get(threat_type, recommendations['default'])
        return f"""
RECOMMENDED ACTIONS FOR {threat_type.upper()} - {severity} SEVERITY
{'='*60}
{chr(10).join([f'{i+1}. {step}' for i, step in enumerate(steps)])}
"""
    
    @lru_cache(maxsize=128)
    def get_model_info(self, model_name: str = None) -> Dict:
        """Get information about available models"""
        model = model_name or self.model
        return self.MODELS.get(model, {
            'name': model,
            'speed': 'unknown',
            'quality': 'unknown',
            'memory': 'unknown'
        })
    
    def list_available_models(self) -> Dict[str, Dict]:
        """List all available models"""
        return self.MODELS
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model"""
        if model_name in self.MODELS:
            self.model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        return False


class ThreatIntelligence:
    """Combine ML predictions with LLM reasoning"""
    
    def __init__(self, llm_service: LocalLLMService):
        self.llm = llm_service
    
    def analyze_with_reasoning(self, 
                              ml_prediction: Dict,
                              threat_data: Dict) -> Dict:
        """Combine ML prediction with LLM reasoning"""
        
        analysis = {
            'timestamp': threat_data.get('timestamp'),
            'ml_prediction': ml_prediction,
            'confidence': ml_prediction.get('confidence', 0.0)
        }
        
        # Get LLM analysis
        if self.llm.is_running:
            analysis['llm_reasoning'] = self.llm.analyze_threat(threat_data)
            analysis['recommendations'] = self.llm.get_recommendations(
                threat_data.get('threat_type', 'Unknown'),
                self._severity_level(ml_prediction.get('confidence', 0.0))
            )
        else:
            analysis['llm_reasoning'] = "LLM service unavailable"
            analysis['recommendations'] = "Please enable Ollama service for recommendations"
        
        return analysis
    
    def _severity_level(self, confidence: float) -> str:
        """Convert confidence to severity level"""
        if confidence > 0.8:
            return "CRITICAL"
        elif confidence > 0.6:
            return "HIGH"
        elif confidence > 0.4:
            return "MEDIUM"
        else:
            return "LOW"


if __name__ == "__main__":
    # Test LLM service
    llm = LocalLLMService()
    
    print("Available Models:")
    print(json.dumps(llm.list_available_models(), indent=2))
    
    if not llm.is_running:
        print("\nStarting Ollama...")
        if llm.start_ollama():
            print("Ollama started successfully")
        else:
            print("Failed to start Ollama - please ensure it's installed")
    
    # Example: Analyze a threat
    sample_threat = {
        'source_port': 12345,
        'dest_port': 443,
        'bytes': 50000,
        'packets': 250,
        'elapsed_time': 15,
        'confidence': 0.85
    }
    
    print("\nAnalyzing threat...")
    analysis = llm.analyze_threat(sample_threat)
    print(analysis)

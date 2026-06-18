#!/usr/bin/env python3
"""
🧪 SYSTEM TESTING & VALIDATION SCRIPT
Complete validation of the advanced ML firewall system
"""

import subprocess
import requests
import json
import sys
import time
from pathlib import Path
from datetime import datetime

class SystemValidator:
    """Comprehensive system validation"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'status': 'PENDING'
        }
        self.colors = {
            'GREEN': '\033[92m',
            'RED': '\033[91m',
            'YELLOW': '\033[93m',
            'BLUE': '\033[94m',
            'RESET': '\033[0m'
        }
    
    def print_header(self, text):
        print(f"\n{self.colors['BLUE']}{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}{self.colors['RESET']}\n")
    
    def print_success(self, text):
        print(f"{self.colors['GREEN']}✓ {text}{self.colors['RESET']}")
    
    def print_error(self, text):
        print(f"{self.colors['RED']}✗ {text}{self.colors['RESET']}")
    
    def print_warning(self, text):
        print(f"{self.colors['YELLOW']}⚠ {text}{self.colors['RESET']}")
    
    def check_python_packages(self):
        """Check required Python packages"""
        self.print_header("Checking Python Packages")
        
        packages = {
            'tensorflow': 'Deep Learning',
            'sklearn': 'Machine Learning',
            'pandas': 'Data Processing',
            'numpy': 'Numerical Computing',
            'flask': 'Backend Framework',
            'requests': 'HTTP Client',
            'flask_socketio': 'WebSockets'
        }
        
        all_installed = True
        for package, desc in packages.items():
            try:
                __import__(package)
                self.print_success(f"{package:<20} - {desc}")
                self.results['checks'][f'package_{package}'] = 'PASS'
            except ImportError:
                self.print_error(f"{package:<20} - {desc} (NOT INSTALLED)")
                self.results['checks'][f'package_{package}'] = 'FAIL'
                all_installed = False
        
        return all_installed
    
    def check_dataset(self):
        """Check if dataset exists"""
        self.print_header("Checking Dataset")
        
        csv_path = Path("/home/neeraj/Downloads/archive/log2.csv")
        
        if csv_path.exists():
            lines = sum(1 for _ in open(csv_path))
            size_mb = csv_path.stat().st_size / (1024*1024)
            self.print_success(f"Dataset found: {csv_path}")
            self.print_success(f"  - Size: {size_mb:.2f} MB")
            self.print_success(f"  - Records: {lines:,}")
            self.results['checks']['dataset'] = 'PASS'
            return True
        else:
            self.print_error(f"Dataset not found at {csv_path}")
            self.results['checks']['dataset'] = 'FAIL'
            return False
    
    def check_trained_models(self):
        """Check if models are trained"""
        self.print_header("Checking Trained Models")
        
        model_dir = Path("/home/neeraj/Downloads/BT-3030-Sarva-Firewall-main/backend/ml_models/trained_models")
        
        if not model_dir.exists():
            self.print_warning("Models directory not found. Run train_models.py first")
            self.results['checks']['models'] = 'NOT_READY'
            return False
        
        models = {
            'cnn_model.h5': 'CNN Model',
            'lstm_model.h5': 'LSTM Model',
            'random_forest_model.pkl': 'Random Forest',
            'gradient_boosting_model.pkl': 'Gradient Boosting',
            'scaler.pkl': 'Feature Scaler',
            'feature_cols.json': 'Feature Names'
        }
        
        all_found = True
        for model_file, desc in models.items():
            path = model_dir / model_file
            if path.exists():
                size_mb = path.stat().st_size / (1024*1024)
                self.print_success(f"{desc:<25} - {size_mb:.2f} MB")
                self.results['checks'][f'model_{model_file}'] = 'PASS'
            else:
                self.print_warning(f"{desc:<25} - NOT FOUND")
                self.results['checks'][f'model_{model_file}'] = 'NOT_FOUND'
                all_found = False
        
        return all_found
    
    def check_backend_running(self):
        """Check if backend is running"""
        self.print_header("Checking Backend Service")
        
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_success("Backend is running")
                self.print_success(f"  - Status: {data.get('status')}")
                self.print_success(f"  - Service: {data.get('service')}")
                self.results['checks']['backend'] = 'PASS'
                return True
        except requests.exceptions.ConnectionError:
            self.print_error("Backend is NOT running on http://localhost:5000")
            self.print_warning("Start with: cd backend && python3 app.py")
            self.results['checks']['backend'] = 'FAIL'
            return False
        except Exception as e:
            self.print_error(f"Error checking backend: {str(e)}")
            self.results['checks']['backend'] = 'FAIL'
            return False
    
    def check_api_endpoints(self):
        """Check if API endpoints are accessible"""
        self.print_header("Checking API Endpoints")
        
        endpoints = {
            '/api/health': 'Health Check',
            '/api/advanced/models/status': 'Models Status',
            '/api/advanced/llm/status': 'LLM Status',
            '/api/advanced/graphs/threat-timeline': 'Threat Timeline',
        }
        
        backend_ok = False
        for endpoint, desc in endpoints.items():
            try:
                response = requests.get(f'http://localhost:5000{endpoint}', timeout=5)
                if response.status_code == 200:
                    self.print_success(f"{desc:<30} - {endpoint}")
                    self.results['checks'][f'endpoint_{endpoint}'] = 'PASS'
                    backend_ok = True
                else:
                    self.print_warning(f"{desc:<30} - Status {response.status_code}")
                    self.results['checks'][f'endpoint_{endpoint}'] = f'STATUS_{response.status_code}'
            except requests.exceptions.ConnectionError:
                self.print_warning(f"{desc:<30} - Backend not running")
                self.results['checks'][f'endpoint_{endpoint}'] = 'NOT_RUNNING'
            except Exception as e:
                self.print_error(f"{desc:<30} - Error: {str(e)}")
                self.results['checks'][f'endpoint_{endpoint}'] = 'ERROR'
        
        return backend_ok
    
    def check_ollama(self):
        """Check Ollama LLM service"""
        self.print_header("Checking Ollama (Local LLM)")
        
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                self.print_success("Ollama is running")
                
                if models:
                    self.print_success(f"  - Models available: {len(models)}")
                    for model in models[:3]:
                        self.print_success(f"    • {model.get('name')}")
                    self.results['checks']['ollama'] = 'PASS'
                    return True
                else:
                    self.print_warning("  - No models downloaded")
                    self.print_warning("  - Download with: ollama pull mistral")
                    self.results['checks']['ollama'] = 'NO_MODELS'
                    return False
        except requests.exceptions.ConnectionError:
            self.print_warning("Ollama is not running on http://localhost:11434")
            self.print_warning("Start with: ollama serve")
            self.results['checks']['ollama'] = 'NOT_RUNNING'
            return False
        except Exception as e:
            self.print_error(f"Error checking Ollama: {str(e)}")
            self.results['checks']['ollama'] = 'ERROR'
            return False
    
    def check_frontend(self):
        """Check if frontend is running"""
        self.print_header("Checking Frontend")
        
        try:
            response = requests.get('http://localhost:5173', timeout=5)
            if response.status_code == 200:
                self.print_success("Frontend is running on http://localhost:5173")
                self.results['checks']['frontend'] = 'PASS'
                return True
        except requests.exceptions.ConnectionError:
            self.print_warning("Frontend is not running on http://localhost:5173")
            self.print_warning("Start with: npm run dev")
            self.results['checks']['frontend'] = 'NOT_RUNNING'
            return False
        except Exception as e:
            self.print_warning(f"Error checking frontend: {str(e)}")
            self.results['checks']['frontend'] = 'UNKNOWN'
            return False
    
    def test_prediction(self):
        """Test model prediction endpoint"""
        self.print_header("Testing Model Prediction")
        
        try:
            payload = {
                "features": {
                    "Source Port": 443,
                    "Destination Port": 443,
                    "Bytes": 5000,
                    "Packets": 15,
                    "Elapsed Time (sec)": 30,
                    "NAT Source Port": 443,
                    "NAT Destination Port": 443,
                    "Bytes Sent": 2500,
                    "Bytes Received": 2500,
                    "pkts_sent": 8,
                    "pkts_received": 7
                },
                "model": "ensemble"
            }
            
            response = requests.post(
                'http://localhost:5000/api/advanced/models/predict',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                predictions = result.get('predictions', {})
                threat_level = result.get('threat_level', 'UNKNOWN')
                confidence = result.get('ensemble_confidence', 0)
                
                self.print_success("Prediction successful!")
                self.print_success(f"  - Threat Level: {threat_level}")
                self.print_success(f"  - Confidence: {confidence:.2%}")
                self.print_success(f"  - Models: {len(predictions)}")
                
                self.results['checks']['prediction'] = 'PASS'
                return True
            else:
                self.print_error(f"Prediction failed with status {response.status_code}")
                self.results['checks']['prediction'] = f'STATUS_{response.status_code}'
                return False
        
        except requests.exceptions.ConnectionError:
            self.print_warning("Cannot connect to backend for prediction test")
            self.results['checks']['prediction'] = 'NO_BACKEND'
            return False
        except Exception as e:
            self.print_error(f"Prediction test error: {str(e)}")
            self.results['checks']['prediction'] = 'ERROR'
            return False
    
    def run_all_checks(self):
        """Run all validation checks"""
        self.print_header("🧪 ADVANCED ML FIREWALL - SYSTEM VALIDATION")
        
        checks = [
            ("Python Packages", self.check_python_packages),
            ("Dataset", self.check_dataset),
            ("Trained Models", self.check_trained_models),
            ("Backend", self.check_backend_running),
            ("API Endpoints", self.check_api_endpoints),
            ("Ollama LLM", self.check_ollama),
            ("Frontend", self.check_frontend),
            ("Prediction Test", self.test_prediction),
        ]
        
        passed = 0
        failed = 0
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Exception in {check_name}: {e}")
                failed += 1
        
        # Summary
        self.print_header("✅ VALIDATION SUMMARY")
        
        total = len(checks)
        print(f"Total Checks: {total}")
        print(f"Passed: {self.colors['GREEN']}{passed}{self.colors['RESET']}")
        print(f"Failed: {self.colors['RED']}{failed}{self.colors['RESET']}")
        
        if failed == 0:
            print(f"\n{self.colors['GREEN']}🎉 All checks passed! System is ready to use.{self.colors['RESET']}")
            self.results['status'] = 'READY'
        elif failed <= 2:
            print(f"\n{self.colors['YELLOW']}⚠ Some services not running. See above for details.{self.colors['RESET']}")
            self.results['status'] = 'PARTIAL'
        else:
            print(f"\n{self.colors['RED']}⚠ Multiple issues detected. Follow setup guide.{self.colors['RESET']}")
            self.results['status'] = 'ISSUES'
        
        print(f"\n{self.colors['BLUE']}Full results saved to: validation_results.json{self.colors['RESET']}\n")
        
        # Save results
        with open('validation_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results['status'] == 'READY'


if __name__ == "__main__":
    validator = SystemValidator()
    success = validator.run_all_checks()
    sys.exit(0 if success else 1)

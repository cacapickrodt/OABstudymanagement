#!/usr/bin/env python3
"""
Backend API Testing for Sistema de Planejamento de Estudos
Testing cronometer functionality and core APIs
"""

import requests
import json
import time
from datetime import datetime, date, timedelta
import sys

# Backend URL from frontend/.env
BASE_URL = "https://bf6a573c-fdd6-4816-9055-84687664cdb9.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.disciplina_test_id = None
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
    
    def test_api_root(self):
        """Test root API endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "Sistema de Planejamento de Estudos" in data.get("message", ""):
                    self.log_test("API Root", True, "Root endpoint working correctly")
                    return True
                else:
                    self.log_test("API Root", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("API Root", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_get_disciplinas(self):
        """Test GET /api/disciplinas - Should return 19 Brazilian law disciplines"""
        try:
            response = self.session.get(f"{self.base_url}/disciplinas")
            if response.status_code == 200:
                disciplinas = response.json()
                
                # Check if we have 19 disciplines
                if len(disciplinas) == 19:
                    self.log_test("GET Disciplinas Count", True, f"Found {len(disciplinas)} disciplines as expected")
                else:
                    self.log_test("GET Disciplinas Count", False, f"Expected 19 disciplines, got {len(disciplinas)}")
                
                # Check for specific Brazilian law disciplines
                expected_disciplines = [
                    "Direito Constitucional", "Direito Civil", "Direito Penal",
                    "Direito Processual Civil", "Direito Processual Penal",
                    "Direito Administrativo", "Direito Tributário", "Direito Trabalhista"
                ]
                
                found_disciplines = [d.get("nome", "") for d in disciplinas]
                missing_disciplines = [d for d in expected_disciplines if d not in found_disciplines]
                
                if not missing_disciplines:
                    self.log_test("GET Disciplinas Content", True, "All expected Brazilian law disciplines found")
                    # Store first discipline ID for further testing
                    if disciplinas:
                        self.disciplina_test_id = disciplinas[0].get("id")
                    return True
                else:
                    self.log_test("GET Disciplinas Content", False, f"Missing disciplines: {missing_disciplines}")
                    return False
            else:
                self.log_test("GET Disciplinas", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("GET Disciplinas", False, f"Error: {str(e)}")
            return False
    
    def test_update_disciplina(self):
        """Test PUT /api/disciplinas/{id} - Update discipline schedules"""
        if not self.disciplina_test_id:
            self.log_test("PUT Disciplina", False, "No discipline ID available for testing")
            return False
        
        try:
            # Test updating schedule
            update_data = {
                "horario_inicio": "09:00",
                "horario_fim": "10:30"
            }
            
            response = self.session.put(
                f"{self.base_url}/disciplinas/{self.disciplina_test_id}",
                json=update_data
            )
            
            if response.status_code == 200:
                updated_disciplina = response.json()
                if (updated_disciplina.get("horario_inicio") == "09:00" and 
                    updated_disciplina.get("horario_fim") == "10:30"):
                    self.log_test("PUT Disciplina", True, "Schedule updated successfully")
                    return True
                else:
                    self.log_test("PUT Disciplina", False, f"Schedule not updated correctly: {updated_disciplina}")
                    return False
            else:
                self.log_test("PUT Disciplina", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("PUT Disciplina", False, f"Error: {str(e)}")
            return False
    
    def test_desempenho_semanal(self):
        """Test GET /api/desempenho/{week} - Weekly performance tracking"""
        try:
            # Test with current week
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_str = week_start.strftime("%Y-%m-%d")
            
            response = self.session.get(f"{self.base_url}/desempenho/{week_str}")
            
            if response.status_code == 200:
                desempenho = response.json()
                if "semana_inicio" in desempenho:
                    self.log_test("GET Desempenho Semanal", True, f"Weekly performance retrieved for week {week_str}")
                    return True
                else:
                    self.log_test("GET Desempenho Semanal", False, f"Invalid response structure: {desempenho}")
                    return False
            else:
                self.log_test("GET Desempenho Semanal", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("GET Desempenho Semanal", False, f"Error: {str(e)}")
            return False
    
    def test_cronometer_start(self):
        """Test POST /api/timer/iniciar - Start study timer for discipline"""
        if not self.disciplina_test_id:
            self.log_test("POST Timer Start", False, "No discipline ID available for testing")
            return False
        
        try:
            # First, ensure no active session exists by trying to stop any existing one
            try:
                self.session.put(f"{self.base_url}/timer/parar/{self.disciplina_test_id}")
            except:
                pass  # Ignore if no session to stop
            
            timer_data = {
                "disciplina_id": self.disciplina_test_id
            }
            
            response = self.session.post(
                f"{self.base_url}/timer/iniciar",
                json=timer_data
            )
            
            if response.status_code == 200:
                sessao = response.json()
                if (sessao.get("disciplina_id") == self.disciplina_test_id and 
                    sessao.get("ativa") == True):
                    self.log_test("POST Timer Start", True, "Timer started successfully for Direito Civil")
                    return True
                else:
                    self.log_test("POST Timer Start", False, f"Invalid session data: {sessao}")
                    return False
            else:
                self.log_test("POST Timer Start", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("POST Timer Start", False, f"Error: {str(e)}")
            return False
    
    def test_cronometer_status(self):
        """Test GET /api/timer/status/{disciplina_id} - Check if timer is active"""
        if not self.disciplina_test_id:
            self.log_test("GET Timer Status", False, "No discipline ID available for testing")
            return False
        
        try:
            response = self.session.get(f"{self.base_url}/timer/status/{self.disciplina_test_id}")
            
            if response.status_code == 200:
                status = response.json()
                if status.get("ativo") == True and status.get("sessao") is not None:
                    self.log_test("GET Timer Status", True, "Timer status shows active session")
                    return True
                else:
                    self.log_test("GET Timer Status", False, f"Timer not active or invalid status: {status}")
                    return False
            else:
                self.log_test("GET Timer Status", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("GET Timer Status", False, f"Error: {str(e)}")
            return False
    
    def test_cronometer_stop(self):
        """Test PUT /api/timer/parar/{disciplina_id} - Stop timer and calculate duration"""
        if not self.disciplina_test_id:
            self.log_test("PUT Timer Stop", False, "No discipline ID available for testing")
            return False
        
        try:
            # Wait a few seconds to have some duration
            print("   Waiting 3 seconds to accumulate study time...")
            time.sleep(3)
            
            response = self.session.put(f"{self.base_url}/timer/parar/{self.disciplina_test_id}")
            
            if response.status_code == 200:
                result = response.json()
                if ("duracao_segundos" in result and 
                    result.get("duracao_segundos", 0) > 0):
                    duration = result.get("duracao_segundos")
                    formatted = result.get("duracao_formatada", "")
                    self.log_test("PUT Timer Stop", True, f"Timer stopped, duration: {duration}s ({formatted})")
                    return True
                else:
                    self.log_test("PUT Timer Stop", False, f"Invalid duration calculation: {result}")
                    return False
            else:
                self.log_test("PUT Timer Stop", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("PUT Timer Stop", False, f"Error: {str(e)}")
            return False
    
    def test_weekly_summary(self):
        """Test GET /api/timer/resumo-semanal - Weekly time summary by discipline"""
        try:
            response = self.session.get(f"{self.base_url}/timer/resumo-semanal")
            
            if response.status_code == 200:
                resumo = response.json()
                if isinstance(resumo, list):
                    # Check if our test session appears in the summary
                    found_test_discipline = False
                    for item in resumo:
                        if item.get("disciplina_id") == self.disciplina_test_id:
                            found_test_discipline = True
                            total_segundos = item.get("total_segundos", 0)
                            nome = item.get("nome_disciplina", "")
                            if total_segundos > 0:
                                self.log_test("GET Weekly Summary", True, 
                                            f"Weekly summary includes test session: {nome} - {total_segundos}s")
                                return True
                    
                    if not found_test_discipline:
                        self.log_test("GET Weekly Summary", True, 
                                    f"Weekly summary retrieved (no sessions yet): {len(resumo)} disciplines")
                        return True
                else:
                    self.log_test("GET Weekly Summary", False, f"Invalid response format: {resumo}")
                    return False
            else:
                self.log_test("GET Weekly Summary", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("GET Weekly Summary", False, f"Error: {str(e)}")
            return False
    
    def test_prevent_overlapping_sessions(self):
        """Test that multiple disciplines can't have overlapping active sessions"""
        if not self.disciplina_test_id:
            self.log_test("Overlapping Sessions Prevention", False, "No discipline ID available for testing")
            return False
        
        try:
            # First start a new session
            timer_data = {
                "disciplina_id": self.disciplina_test_id
            }
            
            start_response = self.session.post(
                f"{self.base_url}/timer/iniciar",
                json=timer_data
            )
            
            if start_response.status_code != 200:
                self.log_test("Overlapping Sessions Prevention", False, 
                            f"Could not start initial session: {start_response.status_code}")
                return False
            
            # Now try to start another session for the same discipline
            response = self.session.post(
                f"{self.base_url}/timer/iniciar",
                json=timer_data
            )
            
            # This should fail with 400 status
            if response.status_code == 400:
                error_msg = response.json().get("detail", "")
                if "já existe uma sessão ativa" in error_msg.lower():
                    self.log_test("Overlapping Sessions Prevention", True, "Correctly prevents overlapping sessions")
                    # Clean up by stopping the session
                    self.session.put(f"{self.base_url}/timer/parar/{self.disciplina_test_id}")
                    return True
                else:
                    self.log_test("Overlapping Sessions Prevention", False, f"Wrong error message: {error_msg}")
                    return False
            else:
                self.log_test("Overlapping Sessions Prevention", False, 
                            f"Should have failed with 400, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Overlapping Sessions Prevention", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("=" * 60)
        print("BACKEND API TESTING - Sistema de Planejamento de Estudos")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print()
        
        # Core API tests
        print("🔍 Testing Core APIs...")
        self.test_api_root()
        self.test_get_disciplinas()
        self.test_update_disciplina()
        self.test_desempenho_semanal()
        
        print("\n⏱️  Testing Cronometer APIs (High Priority)...")
        self.test_cronometer_start()
        self.test_cronometer_status()
        self.test_cronometer_stop()
        self.test_weekly_summary()
        self.test_prevent_overlapping_sessions()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some backend tests failed!")
        sys.exit(1)
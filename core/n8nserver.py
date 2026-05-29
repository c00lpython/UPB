import subprocess
import threading
import requests
import time
import os

class N8nServer:
    def __init__(self):
        self.process = None
        self.port = 5678
        self.is_running = False
        self.url = f"http://localhost:{self.port}"
    
    def start(self):
        """Запускает n8n сервер в фоновом потоке"""
        def run_server():
            try:
                self.process = subprocess.Popen(
                    ["npx", "n8n", "start", f"--port={self.port}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # Ждём запуска
                for _ in range(30):
                    time.sleep(1)
                    if self._check_health():
                        self.is_running = True
                        print(f"✅ n8n сервер запущен на {self.url}")
                        return
                
                print("❌ n8n сервер не запустился")
                
            except Exception as e:
                print(f"❌ Ошибка запуска n8n: {e}")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
    
    def _check_health(self):
        try:
            response = requests.get(f"{self.url}/healthz", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.is_running = False
            print("🛑 n8n сервер остановлен")
    
    def get_workflow_url(self, workflow_id=None):
        if workflow_id:
            return f"{self.url}/workflow/{workflow_id}"
        return self.url
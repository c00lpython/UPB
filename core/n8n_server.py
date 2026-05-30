# core/n8n_server.py
import subprocess
import threading
import time
import os
import signal


class N8nServer:
    def __init__(self, port=5678):
        self.port = port
        self.process = None
        self.is_running = False
        self.url = f"http://localhost:{port}"
    
    def start(self):
        def run():
            try:
                # Запускаем n8n в ОТДЕЛЬНОМ cmd окне (без блокировки)
                # Используем start для создания нового окна
                self.process = subprocess.Popen(
                    f"start cmd /k n8n start --tunnel",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Даём время на запуск
                time.sleep(3)
                
                # Проверяем доступность порта
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', self.port))
                if result == 0:
                    self.is_running = True
                    print(f"[n8n] Server started on port {self.port}")
                sock.close()
                
            except Exception as e:
                print(f"Failed to start n8n: {e}")
                self._start_alternative()
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        
        # Ждём запуска
        for _ in range(15):
            if self.is_running:
                break
            time.sleep(1)
    
    def _start_alternative(self):
        """Альтернативный запуск без нового окна"""
        try:
            self.process = subprocess.Popen(
                ["n8n", "start", "--tunnel"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(3)
            
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', self.port))
            if result == 0:
                self.is_running = True
                print(f"[n8n] Server started on port {self.port}")
            sock.close()
        except Exception as e:
            print(f"Alternative start failed: {e}")
    
    def stop(self):
        if self.process:
            if os.name == 'nt':
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGTERM)
            self.process = None
            self.is_running = False
    
    def is_ready(self):
        return self.is_running
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer


class DevToolsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1e1e1e; border-left: 1px solid #787878;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.devtools_view = QWebEngineView()
        layout.addWidget(self.devtools_view)
        
        self.current_web_view = None
        self.attempts = 0
    
    def attach_to_browser(self, browser_widget):
        """Связывает DevTools с браузером"""
        self.browser_widget = browser_widget
        self.refresh_for_tab(browser_widget.get_current_web_view())
    
    def refresh_for_tab(self, web_view):
        """Обновляет DevTools для новой вкладки"""
        self.current_web_view = web_view
        self.attempts = 0
        
        # Просто перезагружаем страницу DevTools
        self.load_devtools()
    
    def load_devtools(self):
        """Загружает DevTools через remote debugging"""
        self.attempts += 1
        
        # Пробуем перезагрузить страницу
        current_url = self.devtools_view.url().toString()
        
        if "localhost:9222" in current_url:
            # Если уже на DevTools, просто обновляем
            self.devtools_view.reload()
            print(f"🔄 DevTools reloaded (attempt {self.attempts})")
        else:
            # Первая загрузка
            url = "http://127.0.0.1:9222"
            self.devtools_view.setUrl(QUrl(url))
            print(f"🔄 DevTools loading: {url}")
        
        if self.attempts < 3:
            QTimer.singleShot(2000, self.check_if_ready)
    
    def check_if_ready(self):
        """Проверяет, загрузился ли DevTools"""
        js = """
        (function() {
            return document.querySelector('.inspector-view') !== null;
        })();
        """
        
        def callback(result):
            if result:
                print("✅ DevTools ready!")
                # Пробуем автоматически выбрать первую страницу
                self.select_first_page()
            else:
                print("⚠️ DevTools still loading...")
                if self.attempts < 3:
                    QTimer.singleShot(2000, self.load_devtools)
        
        try:
            self.devtools_view.page().runJavaScript(js, callback)
        except:
            pass
    
    def select_first_page(self):
        """Автоматически выбирает первую страницу в Inspectable Pages"""
        js = """
        (function() {
            // Находим первую ссылку inspect
            var links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {
                if (links[i].innerText.includes('inspect')) {
                    links[i].click();
                    console.log('✅ Auto-selected first page');
                    return true;
                }
            }
            console.log('⚠️ No inspect link found');
            return false;
        })();
        """
        self.devtools_view.page().runJavaScript(js)
    
    def show_fallback_message(self):
        """Показывает инструкцию"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    background-color: #1e1e1e;
                    color: #cccccc;
                    font-family: monospace;
                    padding: 20px;
                    text-align: center;
                }
                h3 { color: #ffaa00; }
                .instruction {
                    text-align: left;
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #2d2d2d;
                    border-left: 3px solid #0e639c;
                }
                code {
                    background-color: #3c3c3c;
                    padding: 2px 6px;
                    border-radius: 3px;
                }
                button {
                    background-color: #0e639c;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    margin-top: 20px;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <h3>🔧 Chrome DevTools</h3>
            <div class="instruction">
                <b>📌 Как открыть DevTools:</b><br><br>
                • Нажмите <kbd>правую кнопку мыши</kbd> → <b>Inspect</b><br>
                • Или нажмите <kbd>F12</kbd><br><br>
                <b>🔗 Remote Debugging:</b><br>
                Откройте Chrome и перейдите на <code>http://localhost:9222</code>
            </div>
            <button onclick="window.location.reload()">🔄 Retry</button>
        </body>
        </html>
        """
        self.devtools_view.setHtml(html)
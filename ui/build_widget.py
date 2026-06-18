# ui/build_widget.py

import os
import sys
import json
import shutil
import subprocess
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QGroupBox, QGridLayout,
    QLineEdit, QCheckBox, QComboBox, QSpinBox,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer


class BuildWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    cleanup_signal = pyqtSignal(str)  # для очистки clone-файлов

    def __init__(self, project_name: str, settings: dict, run_tests: bool = False):
        super().__init__()
        self.project_name = project_name
        self.settings = settings
        self.run_tests = run_tests
        self.project_path = os.path.join("projects", project_name)
        self.build_path = os.path.join("builds", project_name)

    def run(self):
        try:
            self.log_signal.emit(f"🚀 Начинаем сборку проекта: {self.project_name}")
            self.log_signal.emit(f"📁 Папка сборки: {self.build_path}")

            os.makedirs(self.build_path, exist_ok=True)

            # 1. Копируем шаблон
            self._copy_template()

            # 2. Копируем variables.xlsx
            self._copy_variables()

            # 3. Копируем или генерируем script.txt
            self._copy_or_generate_script()

            # 4. Копируем profile
            self._copy_profile()

            # 5. Генерируем config.conf
            self._generate_config()

            # 6. Генерируем run-скрипты
            self._generate_run_scripts()

            # 7. Очистка clone-файлов
            self._cleanup_clones()

            # 8. Сохраняем настройки сборки в проекте
            self._save_build_config()

            # 9. Запускаем тесты (если нужно)
            if self.run_tests:
                self._run_tests()

            self.log_signal.emit(f"✅ Сборка завершена успешно!")
            self.log_signal.emit(f"📁 Результат: {self.build_path}")
            self.finished_signal.emit(True, self.build_path)

        except Exception as e:
            import traceback
            error_msg = f"❌ Ошибка сборки: {str(e)}\n{traceback.format_exc()}"
            self.log_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg)

    def _copy_template(self):
        template_dir = "templates/parser_template"
        if not os.path.exists(template_dir):
            self.log_signal.emit(f"⚠️ Шаблон не найден: {template_dir}")
            return

        skip_files = ['TODO.txt', '__pycache__', '.git']
        self.log_signal.emit("📂 Копируем шаблон парсера...")

        for item in os.listdir(template_dir):
            src = os.path.join(template_dir, item)
            dst = os.path.join(self.build_path, item)

            if item in skip_files:
                self.log_signal.emit(f"🧹 Пропускаем {item}")
                continue

            try:
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    self.log_signal.emit(f"📁 Скопирована папка: {item}")
                else:
                    shutil.copy2(src, dst)
                    self.log_signal.emit(f"📄 Скопирован: {item}")
            except Exception as e:
                self.log_signal.emit(f"⚠️ Ошибка копирования {item}: {e}")

    def _copy_variables(self):
        src_vars = os.path.join(self.project_path, "variables.xlsx")
        dst_vars = os.path.join(self.build_path, "variables.xlsx")
        self.log_signal.emit("📊 Копируем variables.xlsx...")

        if os.path.exists(src_vars):
            self._safe_copy(src_vars, dst_vars, "variables.xlsx")
        else:
            self.log_signal.emit("⚠️ variables.xlsx не найдена, создаём пустую")
            try:
                import pandas as pd
                df = pd.DataFrame(columns=["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
                df.to_excel(dst_vars, index=False)
            except ImportError:
                with open(dst_vars, 'w') as f:
                    f.write("")

    def _copy_or_generate_script(self):
        src_script = os.path.join(self.project_path, "script.txt")
        dst_script = os.path.join(self.build_path, "script.txt")
        self.log_signal.emit("📝 Проверяем script.txt...")

        if os.path.exists(src_script):
            self._safe_copy(src_script, dst_script, "script.txt")
            return

        self.log_signal.emit("⚙️ Генерируем script.txt через компилятор...")
        try:
            workflow_path = os.path.join("ui", "SE", "core", "blocks.json")
            if not os.path.exists(workflow_path):
                raise FileNotFoundError(f"blocks.json не найден: {workflow_path}")

            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from ui.SE.core.compiler import UPBCompiler

            compiler = UPBCompiler(workflow_path, os.path.join(self.project_path, "variables.xlsx"))
            compiler.save(dst_script, mode="chain")
            self.log_signal.emit("✅ script.txt сгенерирован")
        except Exception as e:
            self.log_signal.emit(f"⚠️ Ошибка: {e}, создаём fallback")
            with open(dst_script, 'w') as f:
                f.write("# UPB Generated Script (fallback)\nopen_url|{'url': 'https://example.com'}\n")

    def _copy_profile(self):
        src_profile = os.path.join(self.project_path, "profile")
        dst_profile = os.path.join(self.build_path, "profile")
        self.log_signal.emit("👤 Проверяем профиль...")

        if not os.path.exists(src_profile):
            self.log_signal.emit("⚠️ Профиль не найден, создаём пустой")
            os.makedirs(dst_profile, exist_ok=True)
            return

        if os.path.exists(dst_profile):
            try:
                shutil.rmtree(dst_profile)
            except Exception:
                self.log_signal.emit("📁 Профиль занят, создаём с суффиксом _clone")
                dst_profile = f"{dst_profile}_clone"

        os.makedirs(dst_profile, exist_ok=True)
        self.log_signal.emit("👤 Копируем файлы профиля...")

        copied = 0
        errors = []
        for root, dirs, files in os.walk(src_profile):
            rel_path = os.path.relpath(root, src_profile)
            dst_dir = os.path.join(dst_profile, rel_path)
            os.makedirs(dst_dir, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_dir, file)
                if self._safe_copy(src_file, dst_file, f"profile/{file}"):
                    copied += 1
                else:
                    errors.append(file)

        if errors:
            self.log_signal.emit(f"⚠️ {len(errors)} файлов не скопированы: {', '.join(errors[:3])}...")
        self.log_signal.emit(f"✅ Скопировано {copied} файлов профиля")

    def _safe_copy(self, src: str, dst: str, name: str) -> bool:
        """Безопасное копирование с повторными попытками"""
        for attempt in range(5):
            try:
                shutil.copy2(src, dst)
                return True
            except (PermissionError, OSError):
                if attempt < 4:
                    time.sleep(0.3)
                else:
                    return False
        return False

    def _generate_config(self):
        config_path = os.path.join(self.build_path, "config.conf")
        self.log_signal.emit("📝 Генерируем config.conf...")

        settings = self.settings
        variables = []
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'vm_table'):
            vm_table = self.main_window.vm_table
            for row in range(vm_table.table.rowCount()):
                name_item = vm_table.table.item(row, 0)
                xpath_item = vm_table.table.item(row, 1)
                if name_item and name_item.text():
                    var = {
                        'name': name_item.text(),
                        'selector': xpath_item.text() if xpath_item else '',
                        'strategy': 'xpath',
                        'type': 'text'
                    }
                    variables.append(var)

        config_content = f"""[PROJECT]
name = {self.project_name}
url = {settings.get('url', 'https://example.com')}

[BROWSER]
headless = {str(settings.get('headless', True)).lower()}
timeout = {settings.get('timeout', 10)}
retry_count = {settings.get('retry', 3)}

[URLS]
main = {settings.get('url', 'https://example.com')}

[VARIABLES]
items = {json.dumps(variables, indent=4, ensure_ascii=False)}

[OUTPUT]
format = {settings.get('output_format', 'excel')}
excel_path = output.xlsx
json_path = output.json

[LOGGING]
level = INFO
log_file = parser.log

[TELEGRAM]
enabled = {str(bool(settings.get('telegram_token') and settings.get('telegram_chat_id'))).lower()}
bot_token = {settings.get('telegram_token', '')}
chat_id = {settings.get('telegram_chat_id', '')}
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        self.log_signal.emit("✅ config.conf сгенерирован")

    def _generate_run_scripts(self):
        self.log_signal.emit("📄 Генерируем run-скрипты...")

        run_sh = os.path.join(self.build_path, "run.sh")
        with open(run_sh, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\npython3 main.py \"$@\"\n")
        os.chmod(run_sh, 0o755)

        run_ps1 = os.path.join(self.build_path, "run.ps1")
        with open(run_ps1, 'w', encoding='utf-8') as f:
            f.write("python main.py $args\n")

        self.log_signal.emit("✅ run-скрипты сгенерированы")

    def _save_build_config(self):
        """Сохраняет настройки сборки в папку проекта"""
        config_path = os.path.join(self.project_path, ".build_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
        self.log_signal.emit("💾 Настройки сборки сохранены в проекте")

    def _cleanup_clones(self):
        """Удаляет clone-файлы, если есть оригиналы"""
        self.log_signal.emit("🧹 Очищаем clone-файлы...")
        deleted = 0

        for root, dirs, files in os.walk(self.build_path):
            for file in files:
                if "_clone_" in file:
                    original = file.split("_clone_")[0] + os.path.splitext(file)[1]
                    original_path = os.path.join(root, original)
                    if os.path.exists(original_path):
                        try:
                            os.remove(os.path.join(root, file))
                            deleted += 1
                        except Exception as e:
                            self.log_signal.emit(f"⚠️ Не удалён clone: {file} ({e})")

        if deleted:
            self.log_signal.emit(f"🗑️ Удалено {deleted} clone-файлов")

    def _run_tests(self):
        tests_dir = os.path.join(self.build_path, "tests")
        if not os.path.exists(tests_dir):
            self.log_signal.emit("🧪 Нет тестов для запуска")
            return

        self.log_signal.emit("🧪 Запускаем тесты...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", tests_dir],
                cwd=self.build_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self.log_signal.emit("✅ Тесты пройдены")
            else:
                self.log_signal.emit(f"❌ Тесты не пройдены:\n{result.stdout}")
        except Exception as e:
            self.log_signal.emit(f"⚠️ Ошибка запуска тестов: {e}")


class BuildWidget(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.project_manager = main_window.project_manager if main_window else None
        self.current_project = None

        self.init_ui()
        self.load_build_config()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_project_info)
        self.timer.start(2000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Информация о проекте
        info_group = QGroupBox("📁 Текущий проект")
        info_group.setStyleSheet("""
            QGroupBox { color: #cccccc; border: 1px solid #3c3c3c; border-radius: 5px; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
        """)
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(8)
        info_layout.addWidget(QLabel("Проект:"), 0, 0)
        self.project_name_label = QLabel("(не выбран)")
        self.project_name_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        info_layout.addWidget(self.project_name_label, 0, 1)
        info_layout.addWidget(QLabel("Путь:"), 1, 0)
        self.project_path_label = QLabel("—")
        self.project_path_label.setStyleSheet("color: #cccccc;")
        info_layout.addWidget(self.project_path_label, 1, 1)
        info_layout.addWidget(QLabel("Переменных:"), 2, 0)
        self.vars_count_label = QLabel("0")
        self.vars_count_label.setStyleSheet("color: #cccccc;")
        info_layout.addWidget(self.vars_count_label, 2, 1)
        layout.addWidget(info_group)

        # Настройки сборки
        settings_group = QGroupBox("⚙️ Настройки парсера")
        settings_group.setStyleSheet(info_group.styleSheet())
        settings_layout = QGridLayout(settings_group)
        settings_layout.setSpacing(8)

        settings_layout.addWidget(QLabel("🌐 URL:"), 0, 0)
        self.url_input = QLineEdit("https://example.com")
        self.url_input.setStyleSheet("background-color: #252526; color: #cccccc; border: 1px solid #3c3c3c; padding: 4px;")
        settings_layout.addWidget(self.url_input, 0, 1, 1, 3)

        settings_layout.addWidget(QLabel("🕶️ Headless:"), 1, 0)
        self.headless_check = QCheckBox()
        self.headless_check.setChecked(True)
        settings_layout.addWidget(self.headless_check, 1, 1)

        settings_layout.addWidget(QLabel("⏱️ Таймаут (сек):"), 1, 2)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setStyleSheet("background-color: #252526; color: #cccccc; border: 1px solid #3c3c3c;")
        settings_layout.addWidget(self.timeout_spin, 1, 3)

        settings_layout.addWidget(QLabel("📤 Формат:"), 2, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["excel", "csv", "json"])
        self.format_combo.setStyleSheet("background-color: #252526; color: #cccccc; border: 1px solid #3c3c3c;")
        settings_layout.addWidget(self.format_combo, 2, 1)

        settings_layout.addWidget(QLabel("🔄 Retry:"), 2, 2)
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.setStyleSheet("background-color: #252526; color: #cccccc; border: 1px solid #3c3c3c;")
        settings_layout.addWidget(self.retry_spin, 2, 3)

        settings_layout.addWidget(QLabel("🤖 Telegram токен:"), 3, 0)
        self.tg_token_input = QLineEdit()
        self.tg_token_input.setPlaceholderText("(опционально)")
        self.tg_token_input.setStyleSheet("background-color: #252526; color: #cccccc; border: 1px solid #3c3c3c; padding: 4px;")
        settings_layout.addWidget(self.tg_token_input, 3, 1, 1, 3)

        settings_layout.addWidget(QLabel("📱 Chat ID:"), 4, 0)
        self.tg_chat_input = QLineEdit()
        self.tg_chat_input.setPlaceholderText("(опционально)")
        self.tg_chat_input.setStyleSheet("background-color: #252526; color: #cccccc; border: 1px solid #3c3c3c; padding: 4px;")
        settings_layout.addWidget(self.tg_chat_input, 4, 1, 1, 3)

        settings_layout.addWidget(QLabel("🧪 Запустить тесты:"), 5, 0)
        self.tests_check = QCheckBox()
        self.tests_check.setChecked(False)
        settings_layout.addWidget(self.tests_check, 5, 1)

        layout.addWidget(settings_group)

        # Кнопки
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.build_btn = QPushButton("🚀 Собрать парсер")
        self.build_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c; color: white; padding: 10px 25px;
                border: none; border-radius: 4px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:disabled { background-color: #3c3c3c; color: #787878; }
        """)
        self.build_btn.clicked.connect(self.start_build)

        self.open_folder_btn = QPushButton("📂 Открыть папку")
        self.open_folder_btn.setStyleSheet("background-color: #3c3c3c; color: #cccccc; padding: 10px 25px; border: none; border-radius: 4px;")
        self.open_folder_btn.clicked.connect(self.open_project_folder)

        self.clear_btn = QPushButton("🧹 Очистить проект")
        self.clear_btn.setStyleSheet("background-color: #3c3c3c; color: #cccccc; padding: 10px 25px; border: none; border-radius: 4px;")
        self.clear_btn.clicked.connect(self.clear_build)

        self.save_config_btn = QPushButton("💾 Сохранить настройки")
        self.save_config_btn.setStyleSheet("background-color: #3c3c3c; color: #cccccc; padding: 10px 25px; border: none; border-radius: 4px;")
        self.save_config_btn.clicked.connect(self.save_build_config)

        actions_layout.addWidget(self.build_btn)
        actions_layout.addWidget(self.open_folder_btn)
        actions_layout.addWidget(self.clear_btn)
        actions_layout.addWidget(self.save_config_btn)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)

        # Лог
        log_group = QGroupBox("📋 Лог сборки")
        log_group.setStyleSheet(info_group.styleSheet())
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #cccccc; font-family: Consolas; font-size: 11px; border: 1px solid #3c3c3c;")
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("QProgressBar { background-color: #3c3c3c; border: none; height: 6px; border-radius: 3px; } QProgressBar::chunk { background-color: #0e639c; border-radius: 3px; }")
        layout.addWidget(self.progress)

    def load_build_config(self):
        """Загружает настройки сборки из папки проекта"""
        if not self.current_project:
            return
        config_path = os.path.join("projects", self.current_project, ".build_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                self.url_input.setText(settings.get('url', 'https://example.com'))
                self.headless_check.setChecked(settings.get('headless', True))
                self.timeout_spin.setValue(settings.get('timeout', 10))
                self.retry_spin.setValue(settings.get('retry', 3))
                idx = self.format_combo.findText(settings.get('output_format', 'excel'))
                if idx >= 0:
                    self.format_combo.setCurrentIndex(idx)
                self.tg_token_input.setText(settings.get('telegram_token', ''))
                self.tg_chat_input.setText(settings.get('telegram_chat_id', ''))
                self.log(f"💾 Загружены настройки сборки для {self.current_project}")
            except Exception as e:
                self.log(f"⚠️ Ошибка загрузки настроек: {e}")

    def save_build_config(self):
        """Сохраняет настройки сборки в папку проекта"""
        if not self.current_project:
            QMessageBox.warning(self, "Ошибка", "Выберите проект")
            return
        settings = self.get_settings()
        config_path = os.path.join("projects", self.current_project, ".build_config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            self.log(f"💾 Настройки сохранены для {self.current_project}")
        except Exception as e:
            self.log(f"❌ Ошибка сохранения: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить настройки: {e}")

    def update_project_info(self):
        if not self.project_manager:
            return
        project_name = self.project_manager.current_project
        self.current_project = project_name

        if project_name:
            self.project_name_label.setText(project_name)
            self.project_name_label.setStyleSheet("color: #0e639c; font-weight: bold;")
            self.project_path_label.setText(os.path.abspath(os.path.join("projects", project_name)))
            vars_count = self.main_window.vm_table.table.rowCount() if self.main_window and hasattr(self.main_window, 'vm_table') else 0
            self.vars_count_label.setText(str(vars_count))
            if self.main_window and hasattr(self.main_window, 'browser_widget'):
                current_tab = self.main_window.browser_widget.get_current_tab()
                if current_tab:
                    url = current_tab.get_current_url()
                    if url and url != "" and url != "about:blank":
                        self.url_input.setText(url)
            self.build_btn.setEnabled(True)
            # Если есть сохранённые настройки — загружаем
            if not hasattr(self, '_config_loaded'):
                self.load_build_config()
                self._config_loaded = True
        else:
            self.project_name_label.setText("(не выбран)")
            self.project_name_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            self.project_path_label.setText("—")
            self.vars_count_label.setText("0")
            self.build_btn.setEnabled(False)

    def get_settings(self) -> dict:
        return {
            'url': self.url_input.text().strip(),
            'headless': self.headless_check.isChecked(),
            'timeout': self.timeout_spin.value(),
            'delay': 1,
            'retry': self.retry_spin.value(),
            'output_format': self.format_combo.currentText(),
            'telegram_token': self.tg_token_input.text().strip(),
            'telegram_chat_id': self.tg_chat_input.text().strip(),
        }

    def start_build(self):
        if not self.current_project:
            QMessageBox.warning(self, "Ошибка", "Выберите проект на вкладке Project")
            return

        self.log_text.clear()
        self.log("🚀 Запуск сборки...")
        self.build_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        settings = self.get_settings()
        self.worker = BuildWorker(self.current_project, settings, self.tests_check.isChecked())
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_build_finished)
        self.worker.start()

    def on_build_finished(self, success: bool, result: str):
        self.build_btn.setEnabled(True)
        self.progress.setVisible(False)
        if success:
            self.log(f"✅ Сборка завершена: {result}")
            QMessageBox.information(self, "Сборка завершена", f"Парсер собран!\n\n📁 Папка: {result}")
        else:
            self.log(f"❌ Сборка не удалась")
            QMessageBox.critical(self, "Ошибка сборки", result)

    def open_project_folder(self):
        if not self.current_project:
            return
        build_path = os.path.abspath(os.path.join("builds", self.current_project))
        if os.path.exists(build_path):
            if sys.platform == 'win32':
                os.startfile(build_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', build_path])
            else:
                subprocess.run(['xdg-open', build_path])

    def clear_build(self):
        if not self.current_project:
            return
        build_path = os.path.join("builds", self.current_project)
        if not os.path.exists(build_path):
            self.log("🧹 Папка сборки уже пуста")
            return

        reply = QMessageBox.question(self, "Очистка сборки", f"Удалить все файлы сборки для '{self.current_project}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(build_path)
                self.log(f"🧹 Папка сборки очищена")
            except Exception as e:
                self.log(f"❌ Ошибка очистки: {e}")

    def log(self, message: str):
        from PyQt6.QtCore import QDateTime
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_signal.emit(message)
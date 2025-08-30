#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — Cordova/Android Builder (single-file)
Updated version with enhanced progress bar showing current task and global progress
Fixed Cordova platform add using cordova CLI directly, with npm bootstrap
Added keystore creation dialog with fields like in Android Studio, localized RU/EN
Updated keystore UI to match the Signing dialog style from the photo, with fields for alias, passwords, show passwords checkbox
Localized buttons: Clear, Select Keystore, Create Keystore
Made progress bar smoother
"""
import os
import sys
import subprocess
import threading
import zipfile
import shutil
import traceback
import time
import socket
from datetime import datetime
import platform

def ensure_npm_cli(node_dir, logger=None):
    """
    Ensure npm-cli.js exists inside provided embedded node_dir.
    If absent, attempt to download and extract npm into node_dir/node_modules/npm.
    Returns the path to npm-cli.js (may not exist if bootstrap failed).
    """
    import os, urllib.request, io, tarfile
    try:
        candidates = [
            os.path.join(node_dir, "node_modules", "npm", "bin", "npm-cli.js"),
            os.path.join(node_dir, "lib", "node_modules", "npm", "bin", "npm-cli.js"),
            os.path.join(node_dir, "npm-cli.js"),
            os.path.join(node_dir, "bin", "npm-cli.js"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        try:
            if logger: logger.log("npm not found in embedded Node — downloading npm package...", "WARNING")
            npm_tgz_url = "https://registry.npmjs.org/npm/-/npm-10.8.2.tgz"
            with urllib.request.urlopen(npm_tgz_url, timeout=30) as resp:
                data = resp.read()
            tf = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")
            dest = os.path.join(node_dir, "node_modules", "npm")
            os.makedirs(dest, exist_ok=True)
            prefix = "package/"
            for member in tf.getmembers():
                name = member.name
                if name.startswith(prefix):
                    member.name = name[len(prefix):]
                else:
                    member.name = name
                if member.name in ("", "."):
                    continue
                try:
                    tf.extract(member, path=dest)
                except Exception:
                    continue
            cli = os.path.join(dest, "bin", "npm-cli.js")
            if os.path.exists(cli):
                if logger: logger.log(f"Bootstrapped npm to {cli}", "SUCCESS")
                return cli
        except Exception as e:
            if logger: logger.log(f"Failed to bootstrap npm: {e}", "ERROR")
    except Exception:
        pass
    return os.path.join(node_dir, "node_modules", "npm", "bin", "npm-cli.js")

# GUI library
try:
    import customtkinter as ctk
except Exception:
    print("Please install customtkinter: pip install customtkinter")
    sys.exit(1)
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
# HTTP
try:
    import requests
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests
# clipboard
try:
    import pyperclip
except Exception:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"])
        import pyperclip
    except Exception:
        class _PyperclipStub:
            @staticmethod
            def copy(text):
                print("pyperclip not installed; cannot copy.")
        pyperclip = _PyperclipStub()
# Process handling for cleanup
try:
    import psutil
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil
# ------------------------
# Utilities
# ------------------------
def safe_makedirs(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"Failed to create directory {path}: {e}")
def human_size(num):
    try:
        n = float(num)
    except Exception:
        return "?"
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if n < 1024.0:
            return f"{n:3.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}ПБ"
def kill_processes_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name.lower() in (proc.info.get('name') or "").lower():
                proc.terminate()
                proc.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

# ------------------------
# Translations (EN -> RU)
# ------------------------
TRANSLATIONS = {
    "Project type:": "Тип проекта:",
    "Load Project": "Загрузить проект",
    "Build:": "Тип сборки:",
    "⚡ Build": "⚡ Собрать",
    "No project loaded": "Проект не загружен",
    "Keystore (for signed builds):": "Keystore (для подписанных сборок):",
    "Not selected": "Не выбран",
    "Select Keystore": "Выбрать Keystore",
    "Create Keystore": "Создать Keystore",
    "Choose": "Выбрать",
    "Create": "Создать",
    "Clear": "Очистить",
    "Manual Actions": "Ручные действия",
    "Open dependencies folder": "Открыть папку зависимостей",
    "Re-check deps": "Проверить зависимости",
    "Clear logs": "Очистить логи",
    "Logs (compact)": "Логи (компактно)",
    "Save Logs": "Сохранить логи",
    "Copy Logs": "Копировать логи",
    "Open log folder": "Открыть папку логов",
    "Tip: For Cordova, upload a ZIP with config.xml at root. For Android Studio, select project folder with gradlew.": 
        "Подсказка: Для Cordova загрузите ZIP с config.xml в корне. Для Android Studio выберите папку с gradlew.",
    "Ready": "Готово",
    "Language": "Язык",
    "Delete all project folders": "Удалить все папки проектов",
    "Cordova": "Cordova",
    "Android Studio": "Android Studio",
    "Debug APK": "Debug APK",
    "Unsigned Release APK": "Unsigned Release APK",
    "Unsigned AAB": "Unsigned AAB",
    "Signed Debug APK": "Signed Debug APK",
    "Signed Release APK": "Signed Release APK",
    "Signed AAB": "Signed AAB",
    "Application started": "Приложение запущено",
    "Checking dependencies...": "Проверяю зависимости...",
    "Missing: {name} ({path})": "Не найдено: {name} ({path})",
    "Found: {name} ({path})": "Найдено: {name} ({path})",
    "Will install: {list}": "Установлю: {list}",
    "Installing dependency: {name}": "Устанавливаю: {name}",
    "Downloading {description} from {url}": "Скачиваю {description} из {url}",
    "Downloaded {description} → {path}": "Скачано {description} → {path}",
    "Extracting {description} to {target}...": "Распаковка {description} в {target}...",
    "{description} installed to {target}": "{description} установлено в {target}",
    "Flattening inner directory {inner} → {dir}": "Выравниваю вложенную папку {inner} → {dir}",
    "Installed Node.js: {version}": "Node.js установлен: {version}",
    "Installed JDK: {version}": "JDK установлен: {version}",
    "Android SDK command-line tools installed to {path}": "Android SDK установлен в {path}",
    "Created license file: {fname}": "Создан файл лицензии: {fname}",
    "License file exists: {fname}": "Файл лицензии уже есть: {fname}",
    "Accepting Android SDK licenses (writing license files + interactive sdkmanager)...": "Принимаю лицензии Android SDK (пишу файлы + запускаю sdkmanager)...",
    "sdkmanager accepted licenses (interactive)": "sdkmanager принял лицензии (интерактивно)",
    "Installing Android SDK components (build-tools, platforms, platform-tools)...": "Установка компонентов Android SDK (build-tools, platforms, platform-tools)...",
    "All dependencies installed and environment configured": "Все зависимости установлены и окружение настроено",
    "Loading Cordova ZIP: {zip}": "Загружаю Cordova ZIP: {zip}",
    "Cordova project loaded and validated (config.xml found)": "Cordova проект загружен и валиден (config.xml найден)",
    "Build started: {mode} for {ptype}": "Запущена сборку: {mode} для {ptype}",
    "Using Cordova command: {cmd}": "Используется Cordova: {cmd}",
    "Adding Android platform to Cordova (if missing)...": "Добавляю платформу Android в Cordova (если нужно)...",
    "Running Cordova build: {cmd}": "Запускаю Cordova build: {cmd}",
    "Found build artifacts: {paths}": "Найдено артефактов: {paths}",
    "Artifact ready: {path} (size {size})": "Готов артефакт: {path} (размер {size})",
    "Signing APK: {path}": "Подписываю APK: {path}",
    "APK signed: {path}": "APK подписан: {path}",
    "Signing AAB: {path}": "Подписываю AAB: {path}",
    "AAB signed with jarsigner: {path}": "AAB подписан jarsigner: {path}",
    "Command finished successfully (code {rc})": "Команда выполнена успешно (код {rc})",
    "Command finished with code {rc}": "Команда завершилась с кодом {rc}",
    "Error: {err}": "Ошибка: {err}",
    "Warning: {warn}": "Предупреждение: {warn}",
    "Keystore selected: {path}": "Keystore выбран: {path}",
    "Keystore created: {path}": "Keystore создан: {path}",
    "Keystore cleared": "Keystore очищен",
    "Logs saved: {path}": "Логи сохранены: {path}",
    "Language changed to {lang}": "Язык переключен на {lang}",
    "English": "English",
    "Russian": "Русский",
    "Installing Cordova CLI locally": "Устанавливаю Cordova CLI локально",
    "Cordova CLI installed: {version}": "Cordova CLI установлен: {version}",
    "Create a new keystore": "Создать новый keystore",
    "First and Last Name": "Имя и Фамилия",
    "Organizational Unit": "Подразделение организации",
    "Organization": "Организация",
    "City or Locality": "Город или Местность",
    "State or Province": "Штат или Провинция",
    "Country Code (XX)": "Код страны (XX)",
    "Alias": "Псевдоним",
    "Validity (years)": "Срок действия (лет)",
    "Keystore Password": "Пароль keystore",
    "Confirm Password": "Подтвердите пароль",
    "Key Password (optional, if different)": "Пароль ключа (опционально, если отличается)",
    "Cancel": "Отмена",
    "Help": "Помощь",
    "Passwords do not match": "Пароли не совпадают",
    "Fill all required fields": "Заполните все обязательные поля",
    "Keystore creation failed": "Создание keystore провалено",
    "No keystore configured for signed build": "Keystore не настроен для подписанной сборки",
    "Signing": "Подпись",
    "Keystore": "Хранилище ключей",
    "Key alias": "Псевдоним ключа",
    "Show passwords": "Показать пароли",
    "Key password (optional)": "Пароль ключа (опционально)",
    "Confirm": "Подтвердить",
    "Validity must be a number": "Срок действия должен быть числом",
    "Checking dependencies...": "Проверка зависимостей...",
    "Installing {dep}...": "Установка {dep}...",
    "Downloading {description}...": "Скачивание {description}...",
    "Downloading {description}... {percent}%": "Скачивание {description}... {percent}%",
    "Download completed": "Скачивание завершено",
    "Extracting {description}... {percent}%": "Распаковка {description}... {percent}%",
    "{description} installed": "{description} установлено",
    "Accepting SDK licenses...": "Принятие лицензий SDK...",
    "Licenses accepted": "Лицензии приняты",
    "Installing component: {comp}...": "Установка компонента: {comp}...",
    "Component {comp} installed": "Компонент {comp} установлен",
    "Loading ZIP archive...": "Загрузка ZIP-архива...",
    "Extracting ZIP archive... {percent}%": "Распаковка ZIP-архива... {percent}%",
    "Preparing project...": "Подготовка проекта...",
    "Project ready for build": "Проект готов к сборке",
    "Project loading error": "Ошибка загрузки проекта",
    "Starting build...": "Начало сборки...",
    "Starting Cordova build...": "Начало сборки Cordova...",
    "Adding Android platform...": "Добавление платформы Android...",
    "Android platform added": "Платформа Android добавлена",
    "Android platform already added": "Платформа Android уже добавлена",
    "Applying patches...": "Применение патчей...",
    "Build: {mode_internal}...": "Сборка: {mode_internal}...",
    "Build completed": "Сборка выполнена",
    "Artifacts found": "Артефакты найдены",
    "Signing completed": "Подпись завершена",
    "Build completed successfully": "Сборка завершена успешно",
    "Starting Android Studio build...": "Начало сборки Android Studio...",
    "Signing APK: {basename}...": "Подпись APK: {basename}...",
    "Signing AAB: {basename}...": "Подпись AAB: {basename}...",
    "Country code must be 2 letters": "Код страны должен состоять из 2 букв",
    "Validity must be positive": "Срок действия должен быть положительным"
}
def translate(template, lang, **kwargs):
    if lang == 'ru' and template in TRANSLATIONS:
        try:
            return TRANSLATIONS[template].format(**kwargs)
        except Exception:
            return TRANSLATIONS[template]
    try:
        return template.format(**kwargs) if kwargs else template
    except Exception:
        return template
# ------------------------
# Logger
# ------------------------
class Logger:
    LEVELS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "SUCCESS": "✅"
    }
    def __init__(self, text_widget, get_lang_callable):
        self.text_widget = text_widget
        self.get_lang = get_lang_callable
        self._ensure_log_file()
        self._setup_tags()
    def _ensure_log_file(self):
        safe_makedirs(os.path.join(os.getcwd(), "logs"))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logfile = os.path.join(os.getcwd(), "logs", f"app_{ts}.log")
        try:
            with open(self.logfile, "w", encoding="utf-8") as f:
                f.write(f"=== LOG STARTED AT {datetime.now().isoformat()} ===\n")
        except Exception as e:
            print(f"Failed to create log file: {e}")
    def _setup_tags(self):
        try:
            self.text_widget.tag_config("debug", foreground="gray")
            self.text_widget.tag_config("info", foreground="white")
            self.text_widget.tag_config("warning", foreground="orange")
            self.text_widget.tag_config("error", foreground="red")
            self.text_widget.tag_config("success", foreground="light green")
        except Exception:
            pass
    def _write_file(self, line):
        try:
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass
    def raw(self, line):
        if line is None:
            return
        if isinstance(line, bytes):
            try:
                line = line.decode("utf-8", errors="replace")
            except Exception:
                line = str(line)
        if not line.endswith("\n"):
            line = line + "\n"
        ts = datetime.now().strftime("%H:%M:%S")
        out = f"[{ts}] {line}"
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", out, "debug")
            self.text_widget.configure(state="disabled")
            self.text_widget.see("end")
        except Exception:
            print(out, end="")
        self._write_file(out)
    def log(self, template, level="INFO", **kwargs):
        level = level.upper()
        prefix = self.LEVELS.get(level, "•")
        ts = datetime.now().strftime("%H:%M:%S")
        lang = self.get_lang() or 'en'
        try:
            eng = template.format(**kwargs) if kwargs else template
        except Exception:
            eng = template
        loc = translate(template, lang, **kwargs)
        ui_line = f"[{ts}] {prefix} {loc}\n"
        file_line = f"[{ts}] {prefix} {eng} -> {loc}\n"
        try:
            self.text_widget.configure(state="normal")
            tag = level.lower() if level.lower() in ("debug", "info", "warning", "error", "success") else None
            if tag:
                self.text_widget.insert("end", ui_line, tag)
            else:
                self.text_widget.insert("end", ui_line)
            self.text_widget.configure(state="disabled")
            self.text_widget.see("end")
        except Exception:
            print(ui_line, end="")
        self._write_file(file_line)
    def export(self):
        try:
            target = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Log files", "*.log"), ("All files", "*.*")])
            if not target:
                return
            shutil.copyfile(self.logfile, target)
            self.log("Logs saved: {path}", "SUCCESS", path=target)
            messagebox.showinfo("Logs", f"Saved logs to: {target}")
        except Exception as e:
            self.log("Error: {err}", "ERROR", err=str(e))
    def copy(self):
        try:
            content = self.text_widget.get("1.0", "end")
            pyperclip.copy(content)
            self.log("Copy Logs", "SUCCESS")
        except Exception as e:
            self.log("Error: {err}", "ERROR", err=str(e))
    def clear_ui(self):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.delete("1.0", "end")
            self.text_widget.configure(state="disabled")
            self.log("Ready", "INFO")
        except Exception:
            pass
# ------------------------
# Main Application
# ------------------------
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cordova / Android Builder")
        self.geometry("1160x760")
        self.minsize(980, 640)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        # Directories
        self.BASE = os.path.abspath(os.getcwd())
        self.DEP_DIR = os.path.join(self.BASE, "dependencies")
        self.PROJ_DIR = os.path.join(self.BASE, "projects")
        self.LOGS_DIR = os.path.join(self.BASE, "logs")
        safe_makedirs(self.DEP_DIR)
        safe_makedirs(self.PROJ_DIR)
        safe_makedirs(self.LOGS_DIR)
        # State
        self.lang = 'en'
        self.project_types_internal = ["Cordova", "Android Studio"]
        self.build_types_internal = [
            "Debug APK",
            "Unsigned Release APK",
            "Unsigned AAB",
            "Signed Debug APK",
            "Signed Release APK",
            "Signed AAB"
        ]
        self.project_display_var = tk.StringVar()
        self.build_display_var = tk.StringVar()
        self.project_internal_var = tk.StringVar(value=self.project_types_internal[0])
        self.build_internal_var = tk.StringVar(value=self.build_types_internal[0])
        self.keystore_info = {}
        self.project_loaded = False
        self.project_path = None
        self.dependencies_installed = False
        self._cached_env = None
        self.keystore_dialog = None
        # Веса для прогресс-бара (общий прогресс установки зависимостей)
        self.dependency_weights = {
            "Node.js": 20,
            "JDK": 20,
            "Android SDK command-line tools": 30,
            "Gradle": 15,
            "Cordova CLI": 15
        }
        # Добавленные переменные для улучшенного прогресс-бара
        self.current_progress = 0  # Текущее значение прогресса
        self.target_progress = 0   # Целевое значение прогресса для плавного перехода
        self.progress_animation_id = None # ID анимации для after_cancel
        self.current_task = tk.StringVar(value=self._tr("Ready"))  # Текущая задача
        # Keystore vars
        self.ks_path_var = tk.StringVar(value=self._tr("Not selected"))
        self.alias_var = tk.StringVar()
        self.ks_pass_var = tk.StringVar()
        self.key_pass_var = tk.StringVar()
        self.show_pass_var = tk.BooleanVar(value=False)
        # UI creation
        self._build_ui()
        self.logger = Logger(self.log_widget, self._get_lang)
        self.logger.log("Application started", "INFO")
        threading.Thread(target=self.check_dependencies, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Trace for keystore info update
        self.ks_path_var.trace_add("write", self._update_keystore_info)
        self.alias_var.trace_add("write", self._update_keystore_info)
        self.ks_pass_var.trace_add("write", self._update_keystore_info)
        self.key_pass_var.trace_add("write", self._update_keystore_info)
        # Trace for build type to toggle signing section
        self.build_internal_var.trace_add("write", self._toggle_signing_section)
        self._toggle_signing_section()
    def _get_lang(self):
        return self.lang
    def _tr(self, text, **kwargs):
        return translate(text, self.lang, **kwargs)
    def _localize_display(self, key):
        return translate(key, self.lang)
    def _rebuild_optionmenus(self):
        proj_values = [self._localize_display(k) for k in self.project_types_internal]
        self._proj_display_to_internal = {self._localize_display(k): k for k in self.project_types_internal}
        try:
            self.opt_project.configure(values=proj_values)
            current_internal = self.project_internal_var.get()
            self.project_display_var.set(self._localize_display(current_internal))
        except Exception:
            pass
        build_values = [self._localize_display(k) for k in self.build_types_internal]
        self._build_display_to_internal = {self._localize_display(k): k for k in self.build_types_internal}
        try:
            self.opt_build.configure(values=build_values)
            current_internal_b = self.build_internal_var.get()
            self.build_display_var.set(self._localize_display(current_internal_b))
        except Exception:
            pass
    def _build_ui(self):
        pad = 12
        header = ctk.CTkFrame(self, corner_radius=12)
        header.pack(fill="x", padx=pad, pady=(pad, 6))
        lbl_project_type = ctk.CTkLabel(header, text=self._tr("Project type:"))
        lbl_project_type.pack(side="left", padx=(8, 6))
        self.opt_project = ctk.CTkOptionMenu(header, values=[], variable=self.project_display_var, width=160, command=self._on_project_display_change)
        self.opt_project.pack(side="left", padx=(0, 10))
        self.btn_load = ctk.CTkButton(header, text=f"📂 {self._tr('Load Project')}", width=220, command=self.load_project, state="disabled")
        self.btn_load.pack(side="left", padx=(0, 10))
        lbl_build = ctk.CTkLabel(header, text=self._tr("Build:"))
        lbl_build.pack(side="left", padx=(6, 6))
        self.opt_build = ctk.CTkOptionMenu(header, values=[], variable=self.build_display_var, width=320, command=self._on_build_display_change)
        self.opt_build.pack(side="left", padx=(0, 10))
        self.btn_build = ctk.CTkButton(header, text=self._tr("⚡ Build"), width=160, fg_color="#2ecc71", command=self.start_build, state="disabled")
        self.btn_build.pack(side="left", padx=(0, 10))
        status_frame = ctk.CTkFrame(self, corner_radius=12)
        status_frame.pack(fill="x", padx=pad, pady=(6, 0))
        # Создаем метку для отображения текущей задачи
        self.task_label = ctk.CTkLabel(status_frame, textvariable=self.current_task, anchor="w", font=("Arial", 12))
        self.task_label.pack(fill="x", padx=10, pady=(5, 0))
        # Стилизация прогресс-бара
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Horizontal.TProgressbar",
            troughcolor="#2b2b2b",
            bordercolor="#1f1f1f",
            background="#2ecc71",
            lightcolor="#2ecc71",
            darkcolor="#27ae60",
            thickness=12,
            borderwidth=0,
            relief="flat")
        self.progress = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate", style="Custom.Horizontal.TProgressbar")
        self.progress.pack(fill="x", padx=10, pady=(0, 5))
        self.progress["maximum"] = 100
        self._set_progress(0, self._tr("Ready"))
        # Метка для отображения глобального прогресса
        self.global_percent = ctk.CTkLabel(status_frame, text="0%", font=("Arial", 12, "bold"), anchor="e")
        self.global_percent.pack(fill="x", padx=10, pady=(0, 10))
        center = ctk.CTkFrame(self, corner_radius=12)
        center.pack(fill="both", expand=True, padx=pad, pady=(6, pad))
        left = ctk.CTkFrame(center, corner_radius=12)
        left.pack(side="left", fill="both", expand=True, padx=(10, 6), pady=10)
        proj_info = ctk.CTkFrame(left, corner_radius=12)
        proj_info.pack(fill="x", padx=10, pady=8)
        self.project_info_var = tk.StringVar(value=self._tr("No project loaded"))
        ctk.CTkLabel(proj_info, textvariable=self.project_info_var, wraplength=520).pack(padx=8, pady=8)
        self.ks_frame = ctk.CTkFrame(left, corner_radius=12)
        # pack will be managed by _toggle_signing_section
        lbl_ks = ctk.CTkLabel(self.ks_frame, text=self._tr("Signing"))
        lbl_ks.pack(anchor="w", padx=8, pady=(6, 0))
        ks_path_frame = ctk.CTkFrame(self.ks_frame)
        ks_path_frame.pack(fill="x", padx=8, pady=5)
        lbl_ks_path = ctk.CTkLabel(ks_path_frame, text=self._tr("Keystore"))
        lbl_ks_path.pack(side="left", padx=5)
        entry_ks_path = ctk.CTkEntry(ks_path_frame, state="readonly", textvariable=self.ks_path_var)
        entry_ks_path.pack(side="left", fill="x", expand=True, padx=5)
        btn_choose = ctk.CTkButton(ks_path_frame, text=self._tr("Choose"), width=80, command=self._choose_keystore)
        btn_choose.pack(side="left", padx=5)
        btn_create = ctk.CTkButton(ks_path_frame, text=self._tr("Create"), width=80, command=self._create_keystore_dialog)
        btn_create.pack(side="left", padx=5)
        lbl_alias = ctk.CTkLabel(self.ks_frame, text=self._tr("Key alias"))
        lbl_alias.pack(anchor="w", padx=8, pady=5)
        entry_alias = ctk.CTkEntry(self.ks_frame, textvariable=self.alias_var)
        entry_alias.pack(fill="x", padx=8, pady=5)
        checkbox_show = ctk.CTkCheckBox(self.ks_frame, text=self._tr("Show passwords"), variable=self.show_pass_var, command=self._toggle_show_pass)
        checkbox_show.pack(anchor="w", padx=8, pady=5)
        lbl_ks_pass = ctk.CTkLabel(self.ks_frame, text=self._tr("Keystore Password"))
        lbl_ks_pass.pack(anchor="w", padx=8, pady=5)
        self.entry_ks_pass = ctk.CTkEntry(self.ks_frame, textvariable=self.ks_pass_var, show="*")
        self.entry_ks_pass.pack(fill="x", padx=8, pady=5)
        lbl_key_pass = ctk.CTkLabel(self.ks_frame, text=self._tr("Key password (optional)"))
        lbl_key_pass.pack(anchor="w", padx=8, pady=5)
        self.entry_key_pass = ctk.CTkEntry(self.ks_frame, textvariable=self.key_pass_var, show="*")
        self.entry_key_pass.pack(fill="x", padx=8, pady=5)
        btn_clear_ks = ctk.CTkButton(self.ks_frame, text=self._tr("Clear"), width=100, command=self._clear_keystore)
        btn_clear_ks.pack(pady=10, padx=8)
        manual_frame = ctk.CTkFrame(left, corner_radius=12)
        manual_frame.pack(fill="x", padx=10, pady=8)
        man_header = ctk.CTkFrame(manual_frame, corner_radius=8)
        man_header.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(man_header, text="⚙️", width=36).pack(side="left", padx=(4, 6))
        self.lbl_manual = ctk.CTkLabel(man_header, text=self._tr("Manual Actions"), font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_manual.pack(side="left", padx=(2, 12))
        lang_label = ctk.CTkLabel(man_header, text=self._tr("Language"))
        lang_label.pack(side="right", padx=(0, 6))
        self.lang_btn_font = ctk.CTkFont(size=16, weight="bold")
        self.lang_btn = ctk.CTkButton(man_header, text="🇺🇸", width=110, height=42, font=self.lang_btn_font, command=self._toggle_language)
        self.lang_btn.pack(side="right", padx=6)
        self._update_lang_button()
        man_controls = ctk.CTkFrame(manual_frame, corner_radius=8)
        man_controls.pack(fill="x", padx=8, pady=(0, 8))
        self.btn_open_deps = ctk.CTkButton(man_controls, text=self._tr("Open dependencies folder"), width=230, command=self._open_dependencies)
        self.btn_open_deps.pack(side="left", padx=6, pady=6)
        self.btn_recheck = ctk.CTkButton(man_controls, text=self._tr("Re-check deps"), width=170, command=lambda: threading.Thread(target=self.check_dependencies, daemon=True).start())
        self.btn_recheck.pack(side="left", padx=6, pady=6)
        self.btn_clear_logs = ctk.CTkButton(man_controls, text=self._tr("Clear logs"), width=150, command=lambda: self.logger.clear_ui())
        self.btn_clear_logs.pack(side="left", padx=6, pady=6)
        self.btn_delete_projects = ctk.CTkButton(man_controls, text=self._tr("Delete all project folders"), width=230, command=self._delete_project_folders, fg_color="#e74c3c")
        self.btn_delete_projects.pack(side="left", padx=6, pady=6)
        right = ctk.CTkFrame(center, corner_radius=12)
        right.pack(side="left", fill="both", expand=True, padx=(6, 10), pady=10)
        ctk.CTkLabel(right, text=self._tr("Logs (compact)")).pack(anchor="w", padx=8, pady=(8, 0))
        self.log_widget = scrolledtext.ScrolledText(right, wrap="word", height=34, bg="#0b0b0b", fg="#e0e0e0", font=("Consolas", 10))
        self.log_widget.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_widget.configure(state="disabled")
        log_btns = ctk.CTkFrame(right, corner_radius=8)
        log_btns.pack(fill="x", padx=8, pady=(0, 8))
        btn_save = ctk.CTkButton(log_btns, text=self._tr("Save Logs"), width=140, command=lambda: self.logger.export())
        btn_save.pack(side="left", padx=6)
        btn_copy = ctk.CTkButton(log_btns, text=self._tr("Copy Logs"), width=140, command=lambda: self.logger.copy())
        btn_copy.pack(side="left", padx=6)
        btn_open_logs = ctk.CTkButton(log_btns, text=self._tr("Open log folder"), width=160, command=self._open_logs_dir)
        btn_open_logs.pack(side="left", padx=6)
        footer = ctk.CTkFrame(self, corner_radius=12)
        footer.pack(fill="x", padx=pad, pady=(0, pad))
        self.hint_var = tk.StringVar(value=self._tr("Tip: For Cordova, upload a ZIP with config.xml at root. For Android Studio, select project folder with gradlew."))
        ctk.CTkLabel(footer, textvariable=self.hint_var).pack(anchor="w", padx=10, pady=8)
        self._rebuild_optionmenus()
        self.project_display_var.trace_add("write", self._on_project_display_var_changed)
        self.build_display_var.trace_add("write", self._on_build_display_var_changed)
    def _toggle_signing_section(self, *args):
        if self.build_internal_var.get().startswith("Signed"):
            self.ks_frame.pack(fill="x", padx=10, pady=8)
        else:
            self.ks_frame.pack_forget()
    def _on_project_display_change(self, *args):
        pass
    def _on_build_display_change(self, *args):
        pass
    def _on_project_display_var_changed(self, *args):
        val = self.project_display_var.get()
        internal = self._proj_display_to_internal.get(val, self.project_types_internal[0])
        self.project_internal_var.set(internal)
    def _on_build_display_var_changed(self, *args):
        val = self.build_display_var.get()
        internal = self._build_display_to_internal.get(val, self.build_types_internal[0])
        self.build_internal_var.set(internal)
    def _update_lang_button(self):
        self.lang_btn.configure(text="🇷🇺" if self.lang == 'en' else "🇺🇸")
    def _toggle_language(self):
        self.lang = 'ru' if self.lang == 'en' else 'en'
        self._rebuild_optionmenus()
        self._refresh_ui_texts()
        self._update_lang_button()
        lang_name_local = self._tr("Russian") if self.lang == 'ru' else self._tr("English")
        self.logger.log("Language changed to {lang}", "INFO", lang=lang_name_local)
    def _refresh_ui_texts(self):
        try:
            self.btn_load.configure(text=f"📂 {self._tr('Load Project')}")
            self.btn_build.configure(text=self._tr("⚡ Build"))
            self.lbl_manual.configure(text=self._tr("Manual Actions"))
            self.btn_open_deps.configure(text=self._tr("Open dependencies folder"))
            self.btn_recheck.configure(text=self._tr("Re-check deps"))
            self.btn_clear_logs.configure(text=self._tr("Clear logs"))
            self.btn_delete_projects.configure(text=self._tr("Delete all project folders"))
            self.hint_var.set(self._tr("Tip: For Cordova, upload a ZIP with config.xml at root. For Android Studio, select project folder with gradlew."))
            current_project_info = self.project_info_var.get()
            if current_project_info == "No project loaded" or current_project_info == "Проект не загружен":
                self.project_info_var.set(self._tr("No project loaded"))
            else:
                # Assuming it's "Проект загружен: path", no need to re-translate path
                pass
            current_ks = self.ks_path_var.get()
            if current_ks == "Not selected" or current_ks == "Не выбран":
                self.ks_path_var.set(self._tr("Not selected"))
            self.current_task.set(self._tr(self.current_task.get()))
        except Exception as e:
            self.logger.log("Error updating UI texts: {err}", "ERROR", err=str(e))
    def _toggle_show_pass(self):
        show = "" if self.show_pass_var.get() else "*"
        self.entry_ks_pass.configure(show=show)
        self.entry_key_pass.configure(show=show)
    def _update_keystore_info(self, *args):
        path = self.ks_path_var.get()
        if path != self._tr("Not selected"):
            self.keystore_info["path"] = path
        self.keystore_info["alias"] = self.alias_var.get()
        self.keystore_info["storepass"] = self.ks_pass_var.get()
        self.keystore_info["keypass"] = self.key_pass_var.get() or self.ks_pass_var.get()
    def _choose_keystore(self):
        ks = filedialog.askopenfilename(title=self._tr("Select Keystore"), filetypes=[("Keystore", "*.jks *.keystore"), ("All files", "*.*")])
        if ks:
            self.ks_path_var.set(ks)
            self.logger.log("Keystore selected: {path}", "SUCCESS", path=ks)
    def _create_keystore_dialog(self):
        if hasattr(self, 'keystore_dialog') and self.keystore_dialog and self.keystore_dialog.winfo_exists():
            self.keystore_dialog.focus()
            return
        self.keystore_dialog = ctk.CTkToplevel(self)
        self.keystore_dialog.title(self._tr("Create a new keystore"))
        self.keystore_dialog.geometry("400x500")
        self.keystore_dialog.resizable(False, False)
        self.keystore_dialog.protocol("WM_DELETE_WINDOW", self._on_keystore_dialog_close)
        pad = 10
        # Scrollable frame for fields
        scroll_frame = ctk.CTkScrollableFrame(self.keystore_dialog)
        scroll_frame.pack(fill="both", expand=True, padx=pad, pady=pad)
        # Поля
        lbl_name = ctk.CTkLabel(scroll_frame, text=self._tr("First and Last Name"))
        lbl_name.pack(pady=(pad, 0), anchor="w")
        entry_name = ctk.CTkEntry(scroll_frame)
        entry_name.pack(fill="x")
        lbl_unit = ctk.CTkLabel(scroll_frame, text=self._tr("Organizational Unit"))
        lbl_unit.pack(pady=(pad, 0), anchor="w")
        entry_unit = ctk.CTkEntry(scroll_frame)
        entry_unit.pack(fill="x")
        lbl_org = ctk.CTkLabel(scroll_frame, text=self._tr("Organization"))
        lbl_org.pack(pady=(pad, 0), anchor="w")
        entry_org = ctk.CTkEntry(scroll_frame)
        entry_org.pack(fill="x")
        lbl_city = ctk.CTkLabel(scroll_frame, text=self._tr("City or Locality"))
        lbl_city.pack(pady=(pad, 0), anchor="w")
        entry_city = ctk.CTkEntry(scroll_frame)
        entry_city.pack(fill="x")
        lbl_state = ctk.CTkLabel(scroll_frame, text=self._tr("State or Province"))
        lbl_state.pack(pady=(pad, 0), anchor="w")
        entry_state = ctk.CTkEntry(scroll_frame)
        entry_state.pack(fill="x")
        lbl_country = ctk.CTkLabel(scroll_frame, text=self._tr("Country Code (XX)"))
        lbl_country.pack(pady=(pad, 0), anchor="w")
        entry_country = ctk.CTkEntry(scroll_frame)
        entry_country.pack(fill="x")
        lbl_alias = ctk.CTkLabel(scroll_frame, text=self._tr("Alias"))
        lbl_alias.pack(pady=(pad, 0), anchor="w")
        entry_alias = ctk.CTkEntry(scroll_frame)
        entry_alias.pack(fill="x")
        lbl_validity = ctk.CTkLabel(scroll_frame, text=self._tr("Validity (years)"))
        lbl_validity.pack(pady=(pad, 0), anchor="w")
        entry_validity = ctk.CTkEntry(scroll_frame)
        entry_validity.pack(fill="x")
        lbl_ks_pass = ctk.CTkLabel(scroll_frame, text=self._tr("Keystore Password"))
        lbl_ks_pass.pack(pady=(pad, 0), anchor="w")
        entry_ks_pass = ctk.CTkEntry(scroll_frame, show="*")
        entry_ks_pass.pack(fill="x")
        lbl_confirm_pass = ctk.CTkLabel(scroll_frame, text=self._tr("Confirm Password"))
        lbl_confirm_pass.pack(pady=(pad, 0), anchor="w")
        entry_confirm_pass = ctk.CTkEntry(scroll_frame, show="*")
        entry_confirm_pass.pack(fill="x")
        lbl_key_pass = ctk.CTkLabel(scroll_frame, text=self._tr("Key Password (optional, if different)"))
        lbl_key_pass.pack(pady=(pad, 0), anchor="w")
        entry_key_pass = ctk.CTkEntry(scroll_frame, show="*")
        entry_key_pass.pack(fill="x")
        # Buttons frame at bottom
        buttons = ctk.CTkFrame(self.keystore_dialog)
        buttons.pack(fill="x", side="bottom", pady=pad, padx=pad)
        btn_create = ctk.CTkButton(buttons, text=self._tr("Confirm"), command=lambda: self._create_keystore(
            self.keystore_dialog, entry_name.get(), entry_unit.get(), entry_org.get(), entry_city.get(), entry_state.get(), entry_country.get(),
            entry_alias.get(), entry_validity.get(), entry_ks_pass.get(), entry_confirm_pass.get(), entry_key_pass.get()
        ))
        btn_create.pack(side="left", padx=pad)
        btn_cancel = ctk.CTkButton(buttons, text=self._tr("Cancel"), command=self._on_keystore_dialog_close)
        btn_cancel.pack(side="left", padx=pad)
    def _on_keystore_dialog_close(self):
        if self.keystore_dialog:
            self.keystore_dialog.destroy()
            self.keystore_dialog = None
    def _create_keystore(self, dialog, name, unit, org, city, state, country, alias, validity, ks_pass, confirm_pass, key_pass):
        if ks_pass != confirm_pass:
            messagebox.showerror(self._tr("Error"), self._tr("Passwords do not match"))
            return
        if not all([name, unit, org, city, state, country, alias, validity, ks_pass]):
            messagebox.showerror(self._tr("Error"), self._tr("Fill all required fields"))
            return
        try:
            validity_days = int(validity) * 365
            if validity_days <= 0:
                raise ValueError("Validity must be positive")
        except ValueError:
            messagebox.showerror(self._tr("Error"), self._tr("Validity must be a number"))
            return
        if len(country) != 2:
            messagebox.showerror(self._tr("Error"), self._tr("Country code must be 2 letters"))
            return
        ks_path = filedialog.asksaveasfilename(defaultextension=".jks", filetypes=[("Keystore", "*.jks")])
        if not ks_path:
            return
        dname = f"CN={name}, OU={unit}, O={org}, L={city}, ST={state}, C={country}"
        keytool = os.path.join(self.DEP_DIR, "jdk", "bin", "keytool.exe" if platform.system() == "Windows" else "keytool")
        cmd = [
            keytool, "-genkey", "-v", "-keystore", ks_path, "-keyalg", "RSA", "-keysize", "2048",
            "-validity", str(validity_days), "-alias", alias, "-dname", dname,
            "-storepass", ks_pass, "-keypass", key_pass or ks_pass
        ]
        rc = self._run_and_stream(cmd)
        if rc == 0:
            self.ks_path_var.set(ks_path)
            self.alias_var.set(alias)
            self.ks_pass_var.set(ks_pass)
            self.key_pass_var.set(key_pass or ks_pass)
            self.logger.log("Keystore created: {path}", "SUCCESS", path=ks_path)
            self._on_keystore_dialog_close()
        else:
            messagebox.showerror(self._tr("Error"), self._tr("Keystore creation failed"))
    def _clear_keystore(self):
        self.ks_path_var.set(self._tr("Not selected"))
        self.alias_var.set("")
        self.ks_pass_var.set("")
        self.key_pass_var.set("")
        self.keystore_info = {}
        self.logger.log("Keystore cleared", "INFO")
    def _animate_progress(self):
        """Плавно изменяет значение прогресс-бара к target_progress."""
        if abs(self.current_progress - self.target_progress) < 0.5: # Порог останова
            self.current_progress = self.target_progress
            self.progress['value'] = self.current_progress
            self.global_percent.configure(text=f"{int(self.current_progress)}%")
            self.progress_animation_id = None
            return

        # Вычисляем шаг анимации (например, 1% за итерацию или 5% разницы)
        step = (self.target_progress - self.current_progress) * 0.1 # 10% разницы за шаг
        if abs(step) < 0.1: # Минимальный шаг
            step = 1 if self.target_progress > self.current_progress else -1
        self.current_progress += step
        self.progress['value'] = self.current_progress
        self.global_percent.configure(text=f"{int(self.current_progress)}%")
        
        # Планируем следующий шаг анимации
        self.progress_animation_id = self.after(20, self._animate_progress) # ~50 FPS

    def _set_progress(self, pct, task=None):
        try:
            # Ограничиваем значение между 0 и 100
            pct = max(0, min(100, pct))
            self.target_progress = pct # Устанавливаем целевое значение
            
            # Останавливаем предыдущую анимацию, если она была
            if self.progress_animation_id:
                self.after_cancel(self.progress_animation_id)
            
            # Запускаем новую анимацию
            self._animate_progress()

            # Обновляем текст текущей задачи
            if task:
                self.current_task.set(task)

        except Exception:
            pass

    def load_project(self):
        try:
            if self.project_internal_var.get() == "Android Studio":
                path = filedialog.askdirectory()
            else:
                path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")])
            if not path:
                return
            if self.project_internal_var.get() == "Cordova" and path.endswith(".zip"):
                self._load_cordova_zip(path)
            else:
                self._load_project_folder(path)
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _load_cordova_zip(self, zip_path):
        try:
            self.logger.log("Loading Cordova ZIP: {zip}", "INFO", zip=zip_path)
            self._set_progress(5, self._tr("Loading ZIP archive..."))
            archive_name = os.path.splitext(os.path.basename(zip_path))[0]
            target = os.path.join(self.PROJ_DIR, archive_name)
            safe_makedirs(target)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.namelist())
                extracted_files = 0
                for file in zip_ref.namelist():
                    zip_ref.extract(file, target)
                    extracted_files += 1
                    progress = 5 + (extracted_files / total_files * 10)  # 10% for extraction
                    self._set_progress(progress, self._tr("Extracting ZIP archive... {percent}%", percent=int(extracted_files / total_files * 100)))
            # Fix directory structure if needed
            inner_dirs = [d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))]
            if len(inner_dirs) == 1 and os.path.exists(os.path.join(target, inner_dirs[0], "config.xml")):
                inner = os.path.join(target, inner_dirs[0])
                for item in os.listdir(inner):
                    shutil.move(os.path.join(inner, item), target)
                shutil.rmtree(inner)
                self.logger.log("Flattening inner directory {inner} → {dir}", "INFO", inner=inner, dir=target)
                self._set_progress(20, self._tr("Preparing project..."))
            self.project_path = target
            if os.path.exists(os.path.join(target, "config.xml")):
                self.project_loaded = True
                self.project_info_var.set(f"Проект загружен: {target}")
                self.btn_build.configure(state="normal")
                self.logger.log("Cordova project loaded and validated (config.xml found)", "SUCCESS")
                self._set_progress(25, self._tr("Project ready for build"))
            else:
                self.logger.log("Error: {err}", "ERROR", err="config.xml not found in ZIP")
                self.project_loaded = False
                self.project_info_var.set(self._tr("No project loaded"))
                self.btn_build.configure(state="disabled")
                self._set_progress(0, self._tr("Project loading error"))
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
            self.project_loaded = False
            self.project_info_var.set(self._tr("No project loaded"))
            self.btn_build.configure(state="disabled")
            self._set_progress(0, self._tr("Project loading error"))
    def _load_project_folder(self, folder):
        try:
            self.project_path = folder
            gradlew = os.path.join(folder, "gradlew.bat" if platform.system() == "Windows" else "gradlew")
            if os.path.exists(gradlew):
                self.project_loaded = True
                self.project_info_var.set(f"Проект загружен: {folder}")
                self.btn_build.configure(state="normal")
                self.logger.log("Android Studio project loaded and validated (gradlew found)", "SUCCESS")
                self._set_progress(25, self._tr("Project ready for build"))
            else:
                self.logger.log("Error: {err}", "ERROR", err="gradlew not found in folder")
                self.project_loaded = False
                self.project_info_var.set(self._tr("No project loaded"))
                self.btn_build.configure(state="disabled")
                self._set_progress(0, self._tr("Project loading error"))
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
            self.project_loaded = False
            self.project_info_var.set(self._tr("No project loaded"))
            self.btn_build.configure(state="disabled")
            self._set_progress(0, self._tr("Project loading error"))
    def check_dependencies(self):
        self.after(0, lambda: self.btn_load.configure(state="disabled"))
        self.logger.log("Checking dependencies...", "INFO")
        self._set_progress(2, self._tr("Checking dependencies..."))
        node_dir = os.path.join(self.DEP_DIR, "node")
        jdk_dir = os.path.join(self.DEP_DIR, "jdk")
        sdk_tools_dir = os.path.join(self.DEP_DIR, "android-sdk", "cmdline-tools", "latest")
        gradle_dir = os.path.join(self.DEP_DIR, "gradle")
        cordova_dir = os.path.join(self.DEP_DIR, "node", "node_modules", "cordova")
        missing = []
        node_exe = os.path.join(node_dir, "node.exe" if platform.system() == "Windows" else "bin/node")
        java_exe = os.path.join(jdk_dir, "bin", "java.exe" if platform.system() == "Windows" else "bin/java")
        sdkmanager_exe = os.path.join(sdk_tools_dir, "bin", "sdkmanager.bat" if platform.system() == "Windows" else "sdkmanager")
        gradle_exe = os.path.join(gradle_dir, "bin", "gradle.bat" if platform.system() == "Windows" else "bin/gradle")
        cordova_exe = os.path.join(cordova_dir, "bin", "cordova")
        if not os.path.exists(node_exe):
            missing.append("Node.js")
        if not os.path.exists(java_exe):
            missing.append("JDK")
        if not os.path.exists(sdkmanager_exe):
            missing.append("Android SDK command-line tools")
        if not os.path.exists(gradle_exe):
            missing.append("Gradle")
        if not os.path.exists(cordova_exe):
            missing.append("Cordova CLI")
        if missing:
            self.logger.log("Missing: {name} ({path})", "WARNING", name=", ".join(missing), path=self.DEP_DIR)
            self.logger.log("Will install: {list}", "INFO", list=", ".join(missing))
            self._install_dependencies(missing)
        else:
            self.logger.log("Found: {name} ({path})", "SUCCESS", name="All dependencies", path=self.DEP_DIR)
            self.dependencies_installed = True
            self._setup_environment()
            self.logger.log("All dependencies installed and environment configured", "SUCCESS")
            self._set_progress(100, self._tr("Ready"))
        self.after(0, lambda: self.btn_load.configure(state="normal" if self.dependencies_installed else "disabled"))
    def _install_dependencies(self, missing):
        try:
            total_weight = sum(self.dependency_weights[dep] for dep in missing)
            current_progress = 5
            for dep in missing:
                self.logger.log("Installing dependency: {name}", "INFO", name=dep)
                self._set_progress(current_progress, self._tr("Installing {dep}...", dep=dep))
                if dep == "Node.js":
                    self._install_node(current_progress, self.dependency_weights[dep], total_weight)
                elif dep == "JDK":
                    self._install_jdk(current_progress, self.dependency_weights[dep], total_weight)
                elif dep == "Android SDK command-line tools":
                    self._install_sdk_tools(current_progress, self.dependency_weights[dep], total_weight)
                elif dep == "Gradle":
                    self._install_gradle(current_progress, self.dependency_weights[dep], total_weight)
                elif dep == "Cordova CLI":
                    self._install_cordova(current_progress, self.dependency_weights[dep], total_weight)
                current_progress += self.dependency_weights[dep]
                self._set_progress(current_progress, self._tr("{dep} installed", dep=dep))
            self.dependencies_installed = True
            self._setup_environment()
            self.logger.log("All dependencies installed and environment configured", "SUCCESS")
            self._set_progress(100, self._tr("Ready"))
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
            self._set_progress(0, self._tr("Ready"))
    def _install_node(self, start_progress, weight, total_weight):
        try:
            node_url = ("https://nodejs.org/dist/v18.16.0/node-v18.16.0-win-x64.zip" if platform.system() == "Windows" 
                       else "https://nodejs.org/dist/v18.16.0/node-v18.16.0-linux-x64.tar.xz")
            node_dir = os.path.join(self.DEP_DIR, "node")
            self._download_and_extract(node_url, node_dir, "Node.js", start_progress, weight, total_weight)
            self._flatten_dir(node_dir)
            self.logger.log("Installed Node.js: {version}", "SUCCESS", version=self._get_node_version())
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _install_jdk(self, start_progress, weight, total_weight):
        try:
            jdk_url = ("https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.2%2B8/OpenJDK17U-jdk_x64_windows_hotspot_17.0.2_8.zip" 
                      if platform.system() == "Windows" 
                      else "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.2%2B8/OpenJDK17U-jdk_x64_linux_hotspot_17.0.2_8.tar.gz")
            jdk_dir = os.path.join(self.DEP_DIR, "jdk")
            self._download_and_extract(jdk_url, jdk_dir, "JDK", start_progress, weight, total_weight)
            self._flatten_dir(jdk_dir)
            self.logger.log("Installed JDK: {version}", "SUCCESS", version=self._get_jdk_version())
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _install_sdk_tools(self, start_progress, weight, total_weight):
        try:
            sdk_url = ("https://dl.google.com/android/repository/commandlinetools-win-9477386_latest.zip" 
                      if platform.system() == "Windows" 
                      else "https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip")
            sdk_tools_dir = os.path.join(self.DEP_DIR, "android-sdk", "cmdline-tools")
            self._download_and_extract(sdk_url, sdk_tools_dir, "Android SDK command-line tools", start_progress, weight, total_weight)
            self._fix_sdk_structure(sdk_tools_dir)
            sdk_dir = os.path.join(self.DEP_DIR, "android-sdk")
            self._accept_sdk_licenses(sdk_dir, start_progress + weight * 0.3, weight * 0.2, total_weight)
            self._install_sdk_components(sdk_dir, start_progress + weight * 0.5, weight * 0.5, total_weight)
            self.logger.log("Android SDK command-line tools installed to {path}", "SUCCESS", path=sdk_dir)
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _install_gradle(self, start_progress, weight, total_weight):
        try:
            gradle_url = "https://services.gradle.org/distributions/gradle-7.6-bin.zip"
            gradle_dir = os.path.join(self.DEP_DIR, "gradle")
            self._download_and_extract(gradle_url, gradle_dir, "Gradle", start_progress, weight, total_weight)
            self._flatten_dir(gradle_dir)
            self.logger.log("Installed Gradle: {version}", "SUCCESS", version="7.6")
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _install_cordova(self, start_progress, weight, total_weight):
        try:
            self.logger.log("Installing Cordova CLI locally", "INFO")
            self._set_progress(start_progress, self._tr("Installing Cordova CLI locally"))
            
            node_dir = os.path.join(self.DEP_DIR, "node")
            node_exe = os.path.join(node_dir, "node.exe" if platform.system() == "Windows" else "bin/node")
            npm_cli_path = ensure_npm_cli(node_dir, self.logger)
            if not os.path.exists(npm_cli_path):
                raise Exception("npm-cli.js not found even after bootstrap")

            if not os.path.exists(node_exe):
                raise Exception("node.exe not found; cannot install Cordova")
            
            env = self._get_env()
            cmd = [node_exe, npm_cli_path, "install", "cordova@12.0.0", "--no-save"]
            rc = self._run_and_stream(cmd, cwd=node_dir)
            self._set_progress(start_progress + weight * 0.5, self._tr("Installing Cordova CLI locally"))
            if rc == 0:
                cordova_exe = os.path.join(node_dir, "node_modules", "cordova", "bin", "cordova")
                if os.path.exists(cordova_exe):
                    self.logger.log("Cordova CLI installed: {version}", "SUCCESS", version="12.0.0")
                    self._set_progress(start_progress + weight, self._tr("Cordova CLI installed"))
                else:
                    self.logger.log("Error: {err}", "ERROR", err="Cordova installation failed; binary not found")
            else:
                self.logger.log("Error: {err}", "ERROR", err=f"Cordova installation failed with code {rc}")
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _download_and_extract(self, url, target_dir, description, start_progress, weight, total_weight):
        try:
            self.logger.log("Downloading {description} from {url}", "INFO", description=description, url=url)
            self._set_progress(start_progress, self._tr("Downloading {description}...", description=description))
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            ext = url.split('?')[0].split('.')[-1]
            temp_file = os.path.join(self.DEP_DIR, f"temp_{description.replace(' ', '_')}.{ext}")
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            download_progress = start_progress + (downloaded / total_size) * (weight * 0.5)
                            percent = int(downloaded / total_size * 100)
                            self._set_progress(download_progress, self._tr("Downloading {description}... {percent}%", description=description, percent=percent))
            self.logger.log("Downloaded {description} → {path}", "INFO", description=description, path=temp_file)
            self._set_progress(start_progress + weight * 0.5, self._tr("Download completed"))
            self.logger.log("Extracting {description} to {target}...", "INFO", description=description, target=target_dir)
            safe_makedirs(target_dir)
            if temp_file.endswith(('.tar.gz', '.tar.xz', '.tar', '.gz', '.xz')):
                import tarfile
                with tarfile.open(temp_file, 'r:*') as tar_ref:
                    total_files = len(tar_ref.getnames())
                    extracted_files = 0
                    for member in tar_ref.getnames():
                        tar_ref.extract(member, target_dir)
                        extracted_files += 1
                        extract_progress = start_progress + weight * 0.5 + (extracted_files / total_files) * (weight * 0.5)
                        percent = int(extracted_files / total_files * 100)
                        self._set_progress(extract_progress, self._tr("Extracting {description}... {percent}%", description=description, percent=percent))
            else:
                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    total_files = len(zip_ref.namelist())
                    extracted_files = 0
                    for file in zip_ref.namelist():
                        zip_ref.extract(file, target_dir)
                        extracted_files += 1
                        extract_progress = start_progress + weight * 0.5 + (extracted_files / total_files) * (weight * 0.5)
                        percent = int(extracted_files / total_files * 100)
                        self._set_progress(extract_progress, self._tr("Extracting {description}... {percent}%", description=description, percent=percent))
            self.logger.log("{description} installed to {target}", "SUCCESS", description=description, target=target_dir)
            self._set_progress(start_progress + weight, self._tr("{description} installed", description=description))
            try:
                os.remove(temp_file)
            except Exception:
                pass
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
            raise
    def _flatten_dir(self, dir_path):
        try:
            inner_dirs = [d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))]
            if len(inner_dirs) == 1:
                inner = os.path.join(dir_path, inner_dirs[0])
                for item in os.listdir(inner):
                    src = os.path.join(inner, item)
                    dest = os.path.join(dir_path, item)
                    if os.path.exists(dest):
                        if os.path.isdir(dest):
                            shutil.rmtree(dest)
                        else:
                            os.remove(dest)
                    shutil.move(src, dest)
                shutil.rmtree(inner)
                self.logger.log("Flattening inner directory {inner} → {dir}", "INFO", inner=inner, dir=dir_path)
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _get_node_version(self):
        try:
            node = os.path.join(self.DEP_DIR, "node", "node.exe" if platform.system() == "Windows" else "bin/node")
            if os.path.exists(node):
                out = subprocess.check_output([node, "--version"], text=True, timeout=5)
                return out.strip()
            return "unknown"
        except Exception:
            return "unknown"
    def _get_jdk_version(self):
        try:
            java = os.path.join(self.DEP_DIR, "jdk", "bin", "java.exe" if platform.system() == "Windows" else "bin/java")
            if os.path.exists(java):
                out = subprocess.check_output([java, "-version"], stderr=subprocess.STDOUT, text=True, timeout=5)
                for line in out.splitlines():
                    if "version" in line.lower():
                        return line.strip().split()[1].strip('"')
            return "unknown"
        except Exception:
            return "unknown"
    def _fix_sdk_structure(self, tools_dir):
        try:
            latest = os.path.join(tools_dir, "latest")
            safe_makedirs(latest)
            for item in os.listdir(tools_dir):
                if item == "latest":
                    continue
                p = os.path.join(tools_dir, item)
                if os.path.isdir(p) and "bin" in os.listdir(p):
                    for sub in os.listdir(p):
                        s = os.path.join(p, sub)
                        d = os.path.join(latest, sub)
                        if os.path.exists(d):
                            if os.path.isdir(d):
                                shutil.rmtree(d)
                            else:
                                os.remove(d)
                        shutil.move(s, d)
                    try:
                        shutil.rmtree(p)
                    except Exception:
                        pass
                    self.logger.log("Flattening inner directory {inner} → {dir}", "INFO", inner=p, dir=latest)
                    return
            if "bin" in os.listdir(tools_dir):
                for it in os.listdir(tools_dir):
                    if it == "latest":
                        continue
                    s = os.path.join(tools_dir, it)
                    d = os.path.join(latest, it)
                    if os.path.exists(d):
                        if os.path.isdir(d):
                            shutil.rmtree(d)
                        else:
                            os.remove(d)
                        shutil.move(s, d)
                self.logger.log("Flattening inner directory {inner} → {dir}", "INFO", inner=tools_dir, dir=latest)
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _accept_sdk_licenses(self, sdk_dir, start_progress, weight, total_weight):
        try:
            self.logger.log("Accepting Android SDK licenses (writing license files + interactive sdkmanager)...", "INFO")
            self._set_progress(start_progress, self._tr("Accepting SDK licenses..."))
            licenses_dir = os.path.join(sdk_dir, "licenses")
            safe_makedirs(licenses_dir)
            license_files = {
                "android-sdk-license": "24333f8a63b6825ea9c5514f83c2829b004d1fee",
                "android-sdk-preview-license": "84831b9409646a918e30573b5c9c3cb0",
                "android-googletv-license": "601085b94cd77f0b54ff86406957099ebe79c4d6",
                "uiautomator-license": "8933bad161af4178b1185b1a37fbf41ea5269c11"
            }
            for fname, content in license_files.items():
                p = os.path.join(licenses_dir, fname)
                if not os.path.exists(p):
                    with open(p, "w") as f:
                        f.write(content)
                    self.logger.log("Created license file: {fname}", "DEBUG", fname=fname)
                else:
                    self.logger.log("License file exists: {fname}", "DEBUG", fname=fname)
            sdkmanager = self._get_sdkmanager_path()
            if not os.path.exists(sdkmanager):
                self.logger.log("Warning: {warn}", "WARNING", warn="sdkmanager not found, skipping interactive license acceptance")
                return
            env = self._get_env()
            cmd = [sdkmanager, "--licenses", f"--sdk_root={sdk_dir}"]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
            try:
                for _ in range(50):
                    try:
                        proc.stdin.write("y\n")
                        proc.stdin.flush()
                    except Exception:
                        pass
                    time.sleep(0.05)
                while True:
                    line = proc.stdout.readline()
                    if not line and proc.poll() is not None:
                        break
                    if line:
                        self.logger.raw(line.rstrip("\n"))
                rc = proc.wait(timeout=300)
                if rc == 0:
                    self.logger.log("sdkmanager accepted licenses (interactive)", "SUCCESS")
                else:
                    self.logger.log("Warning: {warn}", "WARNING", warn=f"sdkmanager returned {rc}")
                self._set_progress(start_progress + weight, self._tr("Licenses accepted"))
            except Exception as e:
                self.logger.log("Error: {err}", "ERROR", err=str(e))
                self.logger.raw(traceback.format_exc())
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _install_sdk_components(self, sdk_dir, start_progress, weight, total_weight):
        try:
            sdkmanager = self._get_sdkmanager_path()
            if not os.path.exists(sdkmanager):
                raise Exception("sdkmanager not found")
            components = [
                "platform-tools",
                "platforms;android-33",
                "platforms;android-34",
                "build-tools;33.0.2"
            ]
            env = self._get_env()
            total_comps = len(components)
            comp_progress = weight / total_comps if total_comps > 0 else weight
            for i, comp in enumerate(components):
                self.logger.log("Installing Android SDK components (build-tools, platforms, platform-tools)...", "INFO")
                self.logger.log("Installing Android SDK component: {name}", "INFO", name=comp)
                self._set_progress(start_progress + i * comp_progress, self._tr("Installing component: {comp}...", comp=comp))
                cmd = [sdkmanager, "--verbose", comp, f"--sdk_root={sdk_dir}"]
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
                try:
                    for _ in range(20):
                        try:
                            proc.stdin.write("y\n")
                            proc.stdin.flush()
                        except Exception:
                            pass
                        time.sleep(0.1)
                    while True:
                        line = proc.stdout.readline()
                        if not line and proc.poll() is not None:
                           break
                        if line:
                            self.logger.raw(line.rstrip("\n"))
                    rc = proc.wait(timeout=300)
                    if rc == 0:
                        self.logger.log("{description} installed to {target}", "SUCCESS", description=comp, target=sdk_dir)
                    else:
                        self.logger.log("Warning: {warn}", "WARNING", warn=f"{comp} install returned {rc}")
                    self._set_progress(start_progress + (i + 1) * comp_progress, self._tr("Component {comp} installed", comp=comp))
                except Exception as e:
                    self.logger.log("Error: {err}", "ERROR", err=str(e))
                    self.logger.raw(traceback.format_exc())
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _get_sdkmanager_path(self):
        return os.path.join(self.DEP_DIR, "android-sdk", "cmdline-tools", "latest", "bin", 
                           "sdkmanager.bat" if platform.system() == "Windows" else "sdkmanager")
    def _setup_environment(self):
        try:
            env = os.environ.copy()
            env["JAVA_HOME"] = os.path.join(self.DEP_DIR, "jdk")
            env["ANDROID_HOME"] = os.path.join(self.DEP_DIR, "android-sdk")
            env["ANDROID_SDK_ROOT"] = env["ANDROID_HOME"]
            env["GRADLE_HOME"] = os.path.join(self.DEP_DIR, "gradle")
            parts = [
                os.path.join(env["GRADLE_HOME"], "bin"),
                os.path.join(self.DEP_DIR, "node" if platform.system() == "Windows" else "node/bin"),
                os.path.join(self.DEP_DIR, "node", "node_modules", "cordova", "bin"),
                os.path.join(env["JAVA_HOME"], "bin"),
                os.path.join(env["ANDROID_HOME"], "platform-tools"),
                os.path.join(env["ANDROID_HOME"], "cmdline-tools", "latest", "bin")
            ]
            parts.append(env.get("PATH", ""))
            env["PATH"] = os.pathsep.join(p for p in parts if p)
            self._cached_env = env
            self.logger.log("Environment variables configured:", "DEBUG")
            self.logger.log("  JAVA_HOME: {path}", "DEBUG", path=env["JAVA_HOME"])
            self.logger.log("  ANDROID_HOME: {path}", "DEBUG", path=env["ANDROID_HOME"])
            self.logger.log("  GRADLE_HOME: {path}", "DEBUG", path=env["GRADLE_HOME"])
            self.logger.log("  PATH (prefix): {path}", "DEBUG", path=(env["PATH"][:200] + "..."))
            self.logger.log("Environment setup complete", "SUCCESS")
            return True
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
            raise
    def _get_env(self):
        if self._cached_env:
            return self._cached_env
        self._setup_environment()
        return self._cached_env
    def _run_and_capture(self, cmd, cwd=None):
        try:
            env = self._get_env()
            completed = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, encoding='utf-8')
            out = completed.stdout or ""
            for line in out.splitlines():
                self.logger.raw(line)
            return out
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
            raise
    def _run_and_stream(self, cmd, cwd=None, timeout=3600):
        try:
            cmd_display = " ".join(cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
            self.logger.log("Executing: {cmd}", "DEBUG", cmd=cmd_display)
            env = self._get_env()
            shell = platform.system() == "Windows"
            proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, 
                                 text=True, env=env, bufsize=1, shell=shell)
            try:
                while True:
                    line = proc.stdout.readline()
                    if not line and proc.poll() is not None:
                        break
                    if line:
                        self.logger.raw(line.rstrip("\n"))
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    pass
                self.logger.log("Error: {err}", "ERROR", err="Command timeout")
                return -1
            if rc == 0:
                self.logger.log("Command finished successfully (code {rc})", "SUCCESS", rc=rc)
            else:
                self.logger.log("Command finished with code {rc}", "ERROR", rc=rc)
            return rc
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
            return -1
    def start_build(self):
        if not self.project_loaded:
            messagebox.showerror(self._tr("Error"), self._tr("No project loaded"))
            return
        if self.project_internal_var.get() == "Cordova" and not self.dependencies_installed:
            messagebox.showwarning(self._tr("Warning"), self._tr("Dependencies are still being installed. Wait or re-run after installation."))
            return
        mode_internal = self.build_internal_var.get()
        if mode_internal.startswith("Signed"):
            if not self.keystore_info.get("path") or not self.keystore_info.get("alias") or not self.keystore_info.get("storepass"):
                messagebox.showerror(self._tr("Error"), self._tr("No keystore configured for signed build"))
                return
        self.btn_build.configure(state="disabled")
        self._set_progress(0, self._tr("Starting build..."))
        threading.Thread(target=self._build_thread, daemon=True).start()
    def _build_thread(self):
        try:
            mode_internal = self.build_internal_var.get()
            project_type_internal = self.project_internal_var.get()
            self.logger.log("Build started: {mode} for {ptype}", "INFO", mode=mode_internal, ptype=project_type_internal)
            self._set_progress(2, self._tr("Starting build..."))
            if project_type_internal == "Cordova":
                self._build_cordova(mode_internal)
            else:
                self._build_android_studio(mode_internal)
            self.logger.log("Build process completed (thread exit)", "INFO")
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
        finally:
            self.btn_build.configure(state="normal")
            self._set_progress(100, self._tr("Build completed"))
            time.sleep(1)
            self._set_progress(0, self._tr("Ready"))
    def _build_cordova(self, mode_internal):
        self._set_progress(10, self._tr("Starting Cordova build..."))
        node_dir = os.path.join(self.DEP_DIR, "node")
        cordova_exe = os.path.join(node_dir, "node_modules", "cordova", "bin", "cordova")
        if not os.path.exists(cordova_exe):
            raise Exception("Cordova CLI not found in dependencies")
        cordova_cmd = cordova_exe
        self.logger.log("Using Cordova command: {cmd}", "INFO", cmd=cordova_cmd)
        cwd = self.project_path

        # Добавление платформы через Cordova CLI
        platforms_dir = os.path.join(cwd, "platforms")
        android_platform_dir = os.path.join(platforms_dir, "android")
        if not os.path.exists(android_platform_dir):
            self.logger.log("Adding Android platform to Cordova (if missing)...", "INFO")
            self._set_progress(20, self._tr("Adding Android platform..."))
            # Обеспечиваем наличие npm
            npm_cli_path = ensure_npm_cli(node_dir, self.logger)
            if not os.path.exists(npm_cli_path):
                raise Exception("npm-cli.js not found even after bootstrap")
            # Команда cordova platform add
            node_exe = os.path.join(node_dir, "node.exe" if platform.system() == "Windows" else "bin/node")
            add_cmd = [node_exe, cordova_cmd, "platform", "add", "android@12.0.0", "--no-telemetry"]
            rc_add = self._run_and_stream(add_cmd, cwd=cwd)
            if rc_add != 0:
                raise Exception(f"Cordova platform add failed with code {rc_add}")
            self._set_progress(30, self._tr("Android platform added"))
        else:
            self.logger.log("Android platform already exists", "INFO")
            self._set_progress(30, self._tr("Android platform already added"))

        try:
            self._apply_cordova_patches(cwd)
            self._set_progress(35, self._tr("Applying patches..."))
        except Exception as e:
            self.logger.log("Warning: {warn}", "WARNING", warn=str(e))
        # Сборка через Cordova CLI
        node_exe = os.path.join(node_dir, "node.exe" if platform.system() == "Windows" else "bin/node")
        cmd = [node_exe, cordova_cmd, "build", "android", "--no-telemetry"]
        if mode_internal == "Debug APK":
            cmd.append("--debug")
        elif mode_internal == "Unsigned Release APK":
            cmd.append("--release")
        elif mode_internal == "Unsigned AAB":
            cmd.extend(["--release", "--", "--packageType=bundle"])
        else:
            cmd.append("--release")
        self.logger.log("Running Cordova build: {cmd}", "INFO", cmd=" ".join(cmd))
        self._set_progress(40, self._tr("Build: {mode_internal}...", mode_internal=mode_internal))
        rc = self._run_and_stream(cmd, cwd=cwd)
        self._set_progress(70, self._tr("Build completed"))
        if rc != 0:
            raise Exception(f"Cordova build failed with code {rc}")
        artifacts = self._find_artifacts_cordova(cwd)
        self.logger.log("Found build artifacts: {paths}", "INFO", paths=", ".join(artifacts) if artifacts else "(none)")
        self._set_progress(80, self._tr("Artifacts found"))
        if any(mode_internal.startswith(s) for s in ("Signed",)):
            if not self.keystore_info.get("path"):
                raise Exception("Keystore not configured for signed build")
            self._sign_and_align(artifacts)
            self._set_progress(95, self._tr("Signing completed"))
        else:
            if artifacts:
                p = artifacts[0]
                try:
                    size = human_size(os.path.getsize(p))
                except Exception:
                    size = "?"
                self.logger.log("Artifact ready: {path} (size {size})", "SUCCESS", path=p, size=size)
                self._open_artifact_folder(p)
        self._set_progress(100, self._tr("Build completed successfully"))
    def _apply_cordova_patches(self, project_dir):
        try:
            cordova_gradle = os.path.join(project_dir, "platforms", "android", "CordovaLib", "cordova.gradle")
            if os.path.exists(cordova_gradle):
                with open(cordova_gradle, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if "import groovy.xml.XmlParser" not in content:
                    new = "import groovy.xml.XmlParser\n" + content
                    with open(cordova_gradle, "w", encoding="utf-8") as f:
                        f.write(new)
                    self.logger.log("Added import groovy.xml.XmlParser to cordova.gradle", "SUCCESS")
                else:
                    self.logger.log("cordova.gradle already patched", "DEBUG")
            else:
                self.logger.log("cordova.gradle not found, skipping patch", "DEBUG")
        except Exception as e:
            self.logger.log("Warning: {warn}", "WARNING", warn=str(e))
    def _find_artifacts_cordova(self, project_dir):
        out = []
        base = os.path.join(project_dir, "platforms", "android")
        if not os.path.exists(base):
            base = project_dir
        for root, _, files in os.walk(base):
            for f in files:
                if f.endswith((".apk", ".aab")):
                    out.append(os.path.join(root, f))
        return out
    def _build_android_studio(self, mode_internal):
        self._set_progress(10, self._tr("Starting Android Studio build..."))
        gradlew = "gradlew.bat" if platform.system() == "Windows" else "./gradlew"
        cwd = self.project_path
        gradlew_path = os.path.join(cwd, gradlew)
        if not os.path.exists(gradlew_path):
            raise Exception("gradlew not found in project root")
        if mode_internal == "Debug APK":
            cmd = [gradlew, "assembleDebug"]
        elif mode_internal == "Unsigned Release APK":
            cmd = [gradlew, "assembleRelease"]
        elif mode_internal == "Unsigned AAB":
            cmd = [gradlew, "bundleRelease"]
        else:
            cmd = [gradlew, "assembleRelease"]
        self.logger.log("Running gradle command: {cmd}", "INFO", cmd=" ".join(cmd))
        self._set_progress(20, self._tr("Build: {mode_internal}...", mode_internal=mode_internal))
        rc = self._run_and_stream(cmd, cwd=cwd)
        self._set_progress(70, self._tr("Build completed"))
        if rc != 0:
            raise Exception(f"Gradle build failed with code {rc}")
        artifacts = []
        for root, _, files in os.walk(cwd):
            for f in files:
                if f.endswith((".apk", ".aab")):
                    artifacts.append(os.path.join(root, f))
        self.logger.log("Found build artifacts: {paths}", "INFO", paths=", ".join(artifacts) if artifacts else "(none)")
        self._set_progress(80, self._tr("Artifacts found"))
        if any(mode_internal.startswith(s) for s in ("Signed",)):
            if not self.keystore_info.get("path"):
                raise Exception("Keystore not configured for signed build")
            self._sign_and_align(artifacts)
            self._set_progress(95, self._tr("Signing completed"))
        else:
            if artifacts:
                p = artifacts[0]
                try:
                    size = human_size(os.path.getsize(p))
                except Exception:
                    size = "?"
                self.logger.log("Artifact ready: {path} (size {size})", "SUCCESS", path=p, size=size)
                self._open_artifact_folder(p)
        self._set_progress(100, self._tr("Build completed successfully"))
    def _ask_keystore_quick(self):
        try:
            ks = filedialog.askopenfilename(title=self._tr("Select Keystore"), filetypes=[("Keystore", "*.jks *.keystore"), ("All files", "*.*")])
            if not ks:
                return
            storepass = simpledialog.askstring(self._tr("Keystore password"), self._tr("Enter keystore password:"), show="*")
            alias = simpledialog.askstring(self._tr("Key alias"), self._tr("Enter key alias:"))
            keypass = simpledialog.askstring(self._tr("Key password"), self._tr("Enter key password (if same as store, leave blank):"), show="*")
            if ks and storepass and alias:
                self.keystore_info = {"path": ks, "storepass": storepass, "alias": alias, "keypass": keypass or storepass}
                self.ks_path_var.set(ks)
                self.logger.log("Keystore selected: {path}", "SUCCESS", path=ks)
            else:
                self.logger.log("Warning: {warn}", "WARNING", warn="Keystore selection incomplete")
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _sign_and_align(self, artifacts):
        for art in artifacts:
            if art.endswith(".apk"):
                self._sign_apk(art)
            elif art.endswith(".aab"):
                self._sign_aab(art)
    def _sign_apk(self, apk):
        try:
            self.logger.log("Signing APK: {path}", "INFO", path=apk)
            basename = os.path.basename(apk)
            self._set_progress(self.current_progress, self._tr("Signing APK: {basename}...", basename=basename))
            buildtools = os.path.join(self.DEP_DIR, "android-sdk", "build-tools", "33.0.2")
            zipalign = os.path.join(buildtools, "zipalign.exe" if platform.system() == "Windows" else "zipalign")
            apksigner = os.path.join(buildtools, "apksigner.bat" if platform.system() == "Windows" else "apksigner")
            src = apk
            if os.path.exists(zipalign):
                aligned = apk.replace(".apk", ".aligned.apk")
                rc = self._run_and_stream([zipalign, "-p", "4", src, aligned])
                if rc == 0:
                    src = aligned
                    self.logger.log("Debug: {msg}", "DEBUG", msg=f"zipalign created {aligned}")
                else:
                    self.logger.log("Warning: {warn}", "WARNING", warn="zipalign failed; continuing with original apk")
            else:
                self.logger.log("Warning: {warn}", "WARNING", warn="zipalign not found")
            if not os.path.exists(apksigner):
                self.logger.log("Error: {err}", "ERROR", err="apksigner not found")
                return
            ks = self.keystore_info
            cmd = [
                apksigner, "sign",
                "--ks", ks["path"],
                "--ks-pass", f"pass:{ks['storepass']}",
                "--ks-key-alias", ks["alias"],
                "--key-pass", f"pass:{ks['keypass']}",
                src
            ]
            rc = self._run_and_stream(cmd)
            if rc == 0:
                self.logger.log("APK signed: {path}", "SUCCESS", path=src)
                self._open_artifact_folder(src)
            else:
                self.logger.log("Error: {err}", "ERROR", err=f"apksigner returned {rc}")
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _sign_aab(self, aab):
        try:
            self.logger.log("Signing AAB: {path}", "INFO", path=aab)
            basename = os.path.basename(aab)
            self._set_progress(self.current_progress, self._tr("Signing AAB: {basename}...", basename=basename))
            jarsigner = os.path.join(self.DEP_DIR, "jdk", "bin", "jarsigner.exe" if platform.system() == "Windows" else "jarsigner")
            if not os.path.exists(jarsigner):
                self.logger.log("Error: {err}", "ERROR", err="jarsigner not found")
                return
            ks = self.keystore_info
            cmd = [
                jarsigner, "-verbose",
                "-keystore", ks["path"],
                "-storepass", ks["storepass"],
                "-keypass", ks["keypass"],
                aab, ks["alias"]
            ]
            rc = self._run_and_stream(cmd)
            if rc == 0:
                self.logger.log("AAB signed with jarsigner: {path}", "SUCCESS", path=aab)
                self._open_artifact_folder(aab)
            else:
                self.logger.log("Error: {err}", "ERROR", err=f"jarsigner returned {rc}")
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
            self.logger.raw(traceback.format_exc())
    def _open_artifact_folder(self, path):
        try:
            folder = os.path.dirname(path)
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self.logger.log("Opening folder: {folder}", "INFO", folder=folder)
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
    def _open_dependencies(self):
        self._open_artifact_folder(self.DEP_DIR)
    def _open_logs_dir(self):
        self._open_artifact_folder(self.LOGS_DIR)
    def _delete_project_folders(self):
        try:
            if os.path.exists(self.PROJ_DIR):
                shutil.rmtree(self.PROJ_DIR)
                safe_makedirs(self.PROJ_DIR)
                self.logger.log("Deleted all project folders: {path}", "SUCCESS", path=self.PROJ_DIR)
                self.project_loaded = False
                self.project_info_var.set(self._tr("No project loaded"))
                self.btn_build.configure(state="disabled")
            else:
                self.logger.log("No project folders to delete", "INFO")
        except Exception as e:
            self.logger.log("Error: {err}", "ERROR", err=str(e))
    def on_closing(self):
        kill_processes_by_name("java")
        kill_processes_by_name("node")
        kill_processes_by_name("gradle")
        try:
            self.destroy()
        except Exception:
            pass
def main():
    app = MainApp()
    try:
        app.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)
if __name__ == "__main__":
    main()
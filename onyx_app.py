import sys
import os
import uuid
import time
import pyperclip
import threading
import subprocess
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTabWidget, QPushButton, QLineEdit, QLabel, QComboBox, 
                             QCheckBox, QGroupBox, QScrollArea, QFrame, QProgressBar, QFileDialog, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QSize
from PyQt6.QtGui import QIcon, QFont

import onyx_backend as core

# ================= STYLE =================
STYLESHEET = """
QMainWindow, QWidget { background-color: #121212; color: #E0E0E0; font-family: 'Segoe UI', Arial; font-size: 14px; }
QTabWidget::pane { border: 1px solid #333333; }
QTabBar::tab { background: #1E1E1E; color: #AAAAAA; padding: 10px 20px; border: 1px solid #333333; }
QTabBar::tab:selected { background: #333333; color: #FFFFFF; border-bottom: 2px solid #0078D7; }
QPushButton { background-color: #333333; border: 1px solid #555555; color: #FFFFFF; padding: 6px 12px; border-radius: 4px; }
QPushButton:hover { background-color: #444444; border-color: #0078D7; }
QPushButton:pressed { background-color: #222222; }
QLineEdit, QComboBox, QTextEdit { background-color: #1E1E1E; border: 1px solid #333333; color: #FFFFFF; padding: 4px; }
QTableWidget { background-color: #1E1E1E; gridline-color: #333333; color: #FFFFFF; selection-background-color: #0078D7; }
QProgressBar { border: 1px solid #333333; text-align: center; }
QProgressBar::chunk { background-color: #0078D7; }
QGroupBox { border: 1px solid #333333; margin-top: 20px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; color: #0078D7; }
"""

# ================= WORKER SIGNALS =================
class WorkerSignals(QObject):
    progress = pyqtSignal(str, int, str)
    finished = pyqtSignal(str, dict, bool)
    log = pyqtSignal(str, str)
    update_result = pyqtSignal(bool, str)
    app_update_found = pyqtSignal(str, str)
    
    # Dependencies
    dep_progress = pyqtSignal(int)
    dep_status = pyqtSignal(str)
    dep_finished = pyqtSignal(bool, str)

# ================= MAIN APP =================
class OnyxApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Onyx Studio v{core.VERSION}")
        self.resize(1000, 750)
        if os.path.exists("icon.ico"): self.setWindowIcon(QIcon("icon.ico"))
        
        self.settings = core.SettingsManager()
        self.history = core.HistoryManager()
        self.updater = core.SelfUpdater()
        self.dep_manager = core.DependencyManager()
        self.active_tasks = {}
        self.clipboard_monitor_active = True
        
        self.signals = WorkerSignals()
        self.connect_signals()

        self.setup_ui()
        
        # CHECK DEPENDENCIES ON STARTUP
        if not self.dep_manager.is_ffmpeg_installed():
            self.show_dep_dialog()
        else:
            self.start_clipboard_monitor()

    def connect_signals(self):
        self.signals.progress.connect(self.on_task_progress)
        self.signals.finished.connect(self.on_task_finished)
        self.signals.log.connect(self.on_task_log)
        self.signals.update_result.connect(self.on_update_result)
        self.signals.app_update_found.connect(self.on_app_update_found)
        self.signals.dep_progress.connect(self.on_dep_progress)
        self.signals.dep_status.connect(self.on_dep_status)
        self.signals.dep_finished.connect(self.on_dep_finished)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.tab_dashboard = QWidget(); self.setup_dashboard(self.tab_dashboard); self.tabs.addTab(self.tab_dashboard, "Dashboard")
        self.tab_tasks = QWidget(); self.setup_tasks(self.tab_tasks); self.tabs.addTab(self.tab_tasks, "Tasks")
        self.tab_yt = QWidget(); self.setup_youtube(self.tab_yt); self.tabs.addTab(self.tab_yt, "YouTube Pro")
        self.tab_thumb = QWidget(); self.setup_thumbnails(self.tab_thumb); self.tabs.addTab(self.tab_thumb, "Thumbnails")
        self.tab_network = QWidget(); self.setup_network(self.tab_network); self.tabs.addTab(self.tab_network, "Settings")
        self.tab_history = QWidget(); self.setup_history(self.tab_history); self.tabs.addTab(self.tab_history, "History")

    # ================= DEPENDENCY DIALOG (NEW) =================
    def show_dep_dialog(self):
        self.dep_dialog = QDialog(self)
        self.dep_dialog.setWindowTitle("First Time Setup")
        self.dep_dialog.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint) # No Close Button
        self.dep_dialog.setFixedSize(550, 180)
        
        layout = QVBoxLayout(self.dep_dialog)
        
        lbl_info = QLabel("Essential components (FFmpeg) are missing.")
        lbl_info.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(lbl_info)
        
        layout.addWidget(QLabel("Onyx needs to download this once for high-quality video support."))
        
        self.lbl_dep_status = QLabel("Initializing...")
        self.lbl_dep_status.setStyleSheet("color: #0078D7;")
        layout.addWidget(self.lbl_dep_status)
        
        self.pbar_dep = QProgressBar()
        self.pbar_dep.setValue(0)
        layout.addWidget(self.pbar_dep)
        
        # Start Thread
        threading.Thread(target=self.run_dep_download, daemon=True).start()
        self.dep_dialog.exec()

    def run_dep_download(self):
        success, msg = self.dep_manager.download_ffmpeg(self.signals.dep_progress.emit, self.signals.dep_status.emit)
        self.signals.dep_finished.emit(success, msg)

    def on_dep_progress(self, val): self.pbar_dep.setValue(val)
    def on_dep_status(self, msg): self.lbl_dep_status.setText(msg)
    
    def on_dep_finished(self, success, msg):
        if success:
            self.lbl_dep_status.setText("Done! Starting App...")
            time.sleep(1)
            self.dep_dialog.accept()
            self.start_clipboard_monitor()
        else:
            self.lbl_dep_status.setText(f"Error: {msg}")
            QMessageBox.critical(self, "Setup Failed", f"Could not download dependencies.\n{msg}\n\nPlease install FFmpeg manually.")
            self.dep_dialog.reject()

    # ================= UI SETUP HELPERS =================
    def setup_dashboard(self, parent):
        l = QVBoxLayout(parent); l.setAlignment(Qt.AlignmentFlag.AlignTop)
        g = QGroupBox("Quick Download"); v = QVBoxLayout(g)
        self.dash_input = QLineEdit(); self.dash_input.setPlaceholderText("Paste URL here..."); v.addWidget(self.dash_input)
        h = QHBoxLayout(); self.dash_fmt = QComboBox(); self.dash_fmt.addItems(["Video + Audio", "Audio Only"]); h.addWidget(self.dash_fmt)
        b = QPushButton("Start Download"); b.clicked.connect(lambda: self.start_download(self.dash_input, self.dash_fmt.currentText(), "Best")); h.addWidget(b)
        v.addLayout(h); l.addWidget(g)

    def setup_youtube(self, parent):
        l = QVBoxLayout(parent); l.setAlignment(Qt.AlignmentFlag.AlignTop)
        g = QGroupBox("YouTube Advanced"); v = QVBoxLayout(g)
        self.yt_input = QLineEdit(); self.yt_input.setPlaceholderText("YouTube Link..."); v.addWidget(self.yt_input)
        h = QHBoxLayout(); self.yt_res = QComboBox(); self.yt_res.addItems(["Best", "4K", "1080p", "720p", "480p"]); h.addWidget(QLabel("Resolution:")); h.addWidget(self.yt_res)
        self.yt_sub = QCheckBox("Embed Subtitles"); h.addWidget(self.yt_sub); self.yt_thumb = QCheckBox("Save Thumbnail"); h.addWidget(self.yt_thumb); v.addLayout(h)
        b = QPushButton("Download High Quality"); b.clicked.connect(lambda: self.start_download(self.yt_input, "Video + Audio", self.yt_res.currentText(), self.yt_sub.isChecked(), self.yt_thumb.isChecked())); v.addWidget(b); l.addWidget(g)

    def setup_thumbnails(self, parent):
        l = QVBoxLayout(parent); l.setAlignment(Qt.AlignmentFlag.AlignTop)
        g = QGroupBox("Thumbnail Extractor"); v = QVBoxLayout(g)
        v.addWidget(QLabel("Download High-Res Cover (JPG)")); self.thumb_input = QLineEdit(); self.thumb_input.setPlaceholderText("Paste Link..."); v.addWidget(self.thumb_input)
        b = QPushButton("Get Thumbnail"); b.clicked.connect(lambda: self.start_download(self.thumb_input, "", "", False, False, mode='thumbnail')); v.addWidget(b); l.addWidget(g)

    def setup_network(self, parent):
        l = QVBoxLayout(parent); l.setAlignment(Qt.AlignmentFlag.AlignTop)
        g = QGroupBox("Configuration"); v = QVBoxLayout(g)
        v.addWidget(QLabel("Proxy URL:")); self.net_proxy = QLineEdit(); self.net_proxy.setText(self.settings.get("proxy")); v.addWidget(self.net_proxy)
        v.addWidget(QLabel("Cookies File:")); h = QHBoxLayout(); self.net_cookie = QLineEdit(); self.net_cookie.setText(self.settings.get("cookies_path")); h.addWidget(self.net_cookie)
        bb = QPushButton("Browse"); bb.clicked.connect(self.browse_cookies); h.addWidget(bb); v.addLayout(h)
        bs = QPushButton("Save Settings"); bs.clicked.connect(self.save_settings); v.addWidget(bs); l.addWidget(g)
        
        gu = QGroupBox("Updates"); vu = QVBoxLayout(gu); hu = QHBoxLayout()
        self.btn_app_upd = QPushButton(f"Check for App Updates (v{core.VERSION})"); self.btn_app_upd.setStyleSheet("background-color: #004d40; border: 1px solid #00695c;")
        self.btn_app_upd.clicked.connect(self.check_app_updates); hu.addWidget(self.btn_app_upd); vu.addLayout(hu); l.addWidget(gu)

    def setup_tasks(self, parent):
        l = QVBoxLayout(parent); h = QHBoxLayout()
        h.addWidget(QLabel("Active Downloads")); b = QPushButton("Clear Finished"); b.clicked.connect(self.clear_finished_tasks); h.addWidget(b); l.addLayout(h)
        self.task_scroll = QScrollArea(); self.task_scroll.setWidgetResizable(True); self.task_container = QWidget(); self.task_layout = QVBoxLayout(self.task_container); self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_scroll.setWidget(self.task_container); l.addWidget(self.task_scroll)

    def setup_history(self, parent):
        l = QVBoxLayout(parent); h = QHBoxLayout(); b = QPushButton("Refresh"); b.clicked.connect(self.refresh_history); h.addWidget(b); l.addLayout(h)
        self.hist_scroll = QScrollArea(); self.hist_scroll.setWidgetResizable(True); self.hist_container = QWidget(); self.hist_layout = QVBoxLayout(self.hist_container); self.hist_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.hist_scroll.setWidget(self.hist_container); l.addWidget(self.hist_scroll); self.refresh_history()

    # ================= LOGIC & SLOTS =================
    def start_download(self, inp, fmt, res, sub=False, thm=False, mode='normal'):
        u = inp.text().strip(); 
        if not u: return
        inp.clear(); self.tabs.setCurrentWidget(self.tab_tasks); tid = str(uuid.uuid4())
        w = self.create_task_widget(tid, mode); self.task_layout.addWidget(w['frame'])
        opts = {'download_path': self.settings.get("download_path"), 'format': fmt, 'resolution': res, 'proxy': self.settings.get("proxy"), 'cookies_path': self.settings.get("cookies_path"), 'embed_subs': sub, 'save_thumbnail': thm, 'mode': mode}
        cb = {'progress': self.signals.progress.emit, 'finished': self.signals.finished.emit, 'log': self.signals.log.emit}
        t = core.DownloaderEngine(tid, u, opts, cb); self.active_tasks[tid] = {'thread': t, 'widget': w}; t.start()

    def create_task_widget(self, tid, mode):
        f = QFrame(); f.setStyleSheet("QFrame { background-color: #1E1E1E; border: 1px solid #333; border-radius: 5px; }"); l = QVBoxLayout(f)
        h = QHBoxLayout(); p = "[Thumb] " if mode=='thumbnail' else ""; title = QLabel(f"{p}Init..."); title.setStyleSheet("border:none;font-weight:bold"); h.addWidget(title)
        btn = QPushButton("Cancel"); btn.setStyleSheet("background-color: #8B0000; border: none;"); btn.setFixedWidth(60); btn.clicked.connect(lambda: self.cancel_task(tid)); h.addWidget(btn); l.addLayout(h)
        pb = QProgressBar(); pb.setValue(0); l.addWidget(pb); stat = QLabel("Waiting..."); stat.setStyleSheet("border:none;color:#888"); l.addWidget(stat)
        return {'frame': f, 'title': title, 'pbar': pb, 'status': stat, 'btn': btn}

    def on_task_progress(self, tid, pct, spd):
        if tid in self.active_tasks: self.active_tasks[tid]['widget']['pbar'].setValue(pct); self.active_tasks[tid]['widget']['status'].setText(f"Speed: {spd}")
    def on_task_log(self, tid, msg):
        if tid in self.active_tasks: self.active_tasks[tid]['widget']['title'].setText(msg[:60])
    def on_task_finished(self, tid, res, ok):
        if tid in self.active_tasks:
            w = self.active_tasks[tid]['widget']; w['btn'].setEnabled(False); w['btn'].setStyleSheet("background-color:#333")
            if ok: self.history.add(res); w['pbar'].setValue(100); w['status'].setText("Complete"); w['status'].setStyleSheet("border:none;color:#0078D7")
            else: w['status'].setText("Failed/Stopped"); w['status'].setStyleSheet("border:none;color:#FF0000")
    def cancel_task(self, tid): self.active_tasks[tid]['thread'].cancelled = True; self.active_tasks[tid]['widget']['status'].setText("Stopping...")
    def clear_finished_tasks(self):
        d = [k for k,v in self.active_tasks.items() if not v['thread'].is_alive()]
        for k in d: self.active_tasks[k]['widget']['frame'].deleteLater(); del self.active_tasks[k]
    
    # App Update
    def check_app_updates(self): self.btn_app_upd.setText("Checking..."); self.btn_app_upd.setEnabled(False); threading.Thread(target=self._check_worker, daemon=True).start()
    def _check_worker(self): f, v, u = self.updater.check_for_updates(); self.signals.app_update_found.emit(v, u) if f else self.signals.update_result.emit(False, "No updates.")
    def on_app_update_found(self, v, u):
        if QMessageBox.question(self, "Update", f"v{v} Available. Update now?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes: self.start_app_update(u)
        else: self.btn_app_upd.setEnabled(True); self.btn_app_upd.setText(f"Check Updates (v{core.VERSION})")
    def start_app_update(self, url):
        self.dl_d = QDialog(self); self.dl_d.setWindowTitle("Updating..."); self.dl_d.resize(300, 100); l = QVBoxLayout(self.dl_d); l.addWidget(QLabel("Downloading...")); self.dl_pb = QProgressBar(); l.addWidget(self.dl_pb); self.dl_d.show()
        threading.Thread(target=lambda: self.updater.download_and_install(url, self.update_dl_progress)).start()
    def update_dl_progress(self, v): self.dl_pb.setValue(v)
    def on_update_result(self, s, m): self.btn_app_upd.setEnabled(True); self.btn_app_upd.setText(f"Check Updates (v{core.VERSION})"); QMessageBox.information(self, "Info", m)

    # Utils
    def refresh_history(self):
        while self.hist_layout.count(): c=self.hist_layout.takeAt(0); c.widget().deleteLater() if c.widget() else None
        for i, it in enumerate(self.history.history):
            f=QFrame(); f.setStyleSheet("background:#1E1E1E;border-bottom:1px solid #333"); l=QHBoxLayout(f)
            lbl=QLabel(f"{it['title'][:50]}...\n{it.get('size','')} - {it.get('date','')}"); lbl.setStyleSheet("border:none"); l.addWidget(lbl)
            bo=QPushButton("Open"); bo.setFixedWidth(60); bo.clicked.connect(lambda _,p=it['path']:self.open_file(p)); l.addWidget(bo)
            bd=QPushButton("Del"); bd.setFixedWidth(60); bd.setStyleSheet("background:#550000"); bd.clicked.connect(lambda _,x=i:self.delete_history_item(x)); l.addWidget(bd)
            self.hist_layout.addWidget(f)
    def delete_history_item(self, i): self.history.delete(i); self.refresh_history()
    def browse_cookies(self): f,_=QFileDialog.getOpenFileName(self,"Cookies","","Text (*.txt)"); self.net_cookie.setText(f) if f else None
    def save_settings(self): self.settings.set("proxy", self.net_proxy.text()); self.settings.set("cookies_path", self.net_cookie.text()); QMessageBox.information(self,"Saved","Done")
    def open_file(self, p): os.startfile(p) if os.path.exists(p) and platform.system()=="Windows" else None
    def start_clipboard_monitor(self):
        def m():
            l=""; 
            while self.clipboard_monitor_active:
                try: t=pyperclip.paste().strip(); (lambda:None)() if t!=l and "http" in t else None; l=t
                except:pass; time.sleep(1)
        threading.Thread(target=m, daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyleSheet(STYLESHEET); w = OnyxApp(); w.show(); sys.exit(app.exec())

import os
import json
import math
import threading
import platform
import re
import sys
import subprocess
import time
import requests
import zipfile
import shutil
from datetime import datetime
import yt_dlp

# ================= CONSTANTS =================
APP_NAME = "Onyx Qt"
VERSION = "9.5 Auto-Setup"

# GITHUB CONFIG
GITHUB_USER = "TopiTAP"
GITHUB_REPO = "Onyx-Updates"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

# FFmpeg Direct Download Link
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "OnyxMedia")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
FFMPEG_EXE = os.path.join(BASE_DIR, "ffmpeg.exe")

# ================= UTILS =================
def clean_text(text):
    if not text: return ""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def format_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    return "%s %s" % (round(size_bytes / p, 2), size_name[i])

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def delete_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except: return False
    return False

def detect_platform(url):
    if "youtube" in url or "youtu.be" in url: return "YouTube"
    if "tiktok" in url: return "TikTok"
    if "instagram" in url: return "Instagram"
    return "Generic"

# ================= DEPENDENCY MANAGER =================
class DependencyManager:
    def is_ffmpeg_installed(self):
        return os.path.exists(FFMPEG_EXE)

    def download_ffmpeg(self, progress_callback, status_callback):
        try:
            status_callback("Downloading FFmpeg (Required for 1080p)...")
            zip_path = os.path.join(BASE_DIR, "ffmpeg_temp.zip")
            
            r = requests.get(FFMPEG_URL, stream=True)
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            p = int((downloaded / total_size) * 100)
                            progress_callback(p)
            
            status_callback("Extracting ffmpeg.exe...")
            found = False
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith("ffmpeg.exe"):
                        source = zip_ref.open(file)
                        target = open(FFMPEG_EXE, "wb")
                        shutil.copyfileobj(source, target)
                        source.close()
                        target.close()
                        found = True
                        break
            
            status_callback("Cleaning up...")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            if found:
                return True, "Installed Successfully"
            else:
                return False, "Could not find ffmpeg.exe in zip"

        except Exception as e:
            return False, str(e)

# ================= UPDATER =================
class SelfUpdater:
    def check_for_updates(self):
        try:
            r = requests.get(LATEST_RELEASE_API, timeout=10)
            if r.status_code == 200:
                data = r.json()
                remote_ver = data.get("tag_name", "").replace("v", "")
                if remote_ver != VERSION:
                    assets = data.get("assets", [])
                    for asset in assets:
                        if asset["name"].endswith(".exe"):
                            return True, remote_ver, asset["browser_download_url"]
            return False, VERSION, ""
        except: return False, VERSION, ""

    def download_and_install(self, url, progress_callback):
        try:
            local_filename = "Onyx_Update.exe"
            r = requests.get(url, stream=True)
            total = int(r.headers.get('content-length', 0))
            wrote = 0
            with open(local_filename, 'wb') as f:
                for d in r.iter_content(8192):
                    wrote += len(d)
                    f.write(d)
                    if total > 0: progress_callback(int((wrote / total) * 100))
            
            current = sys.executable
            bat = f'@echo off\ntimeout /t 2 /nobreak > NUL\ndel "{current}"\nmove "{local_filename}" "{current}"\nstart "" "{current}"\ndel "%~f0"'
            with open("updater.bat", "w") as b: b.write(bat)
            subprocess.Popen("updater.bat", shell=True)
            sys.exit(0)
        except Exception as e: return False, str(e)

# ================= MANAGERS =================
class SettingsManager:
    def __init__(self):
        self.config = {
            "download_path": DEFAULT_DOWNLOAD_DIR,
            "resolution": "Best",
            "format": "Video + Audio",
            "proxy": "",
            "cookies_path": "",
            "embed_subs": False,
            "save_thumbnail": False
        }
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    self.config.update(json.load(f))
            except: pass
        if not os.path.exists(self.config["download_path"]):
            try: os.makedirs(self.config["download_path"])
            except: pass

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except: pass

    def get(self, k): return self.config.get(k)
    def set(self, k, v): self.config[k] = v; self.save()

class HistoryManager:
    def __init__(self):
        self.history = []
        self.load()

    def load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    self.history = json.load(f)
            except: self.history = []

    def add(self, entry):
        self.history.insert(0, entry)
        self.save()

    def delete(self, index):
        if 0 <= index < len(self.history):
            delete_file(self.history[index]['path'])
            del self.history[index]
            self.save()

    def save(self):
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=4)
        except: pass

# ================= ENGINE =================
class DownloaderEngine(threading.Thread):
    def __init__(self, task_id, url, options, callbacks):
        super().__init__()
        self.task_id = task_id; self.url = url; self.options = options; self.callbacks = callbacks; self.cancelled = False 
    
    def run(self):
        save_path = self.options['download_path']
        mode = self.options.get('mode', 'normal')
        ydl_opts = {
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook],
            'logger': self,
            'ignoreerrors': True, 'no_warnings': True, 'quiet': True, 'nocolor': True, 'retries': 30,
            'ffmpeg_location': FFMPEG_EXE if os.path.exists(FFMPEG_EXE) else None
        }
        
        if mode == 'thumbnail':
            ydl_opts.update({'skip_download': True, 'writethumbnail': True, 'convert_thumbnails': 'jpg', 'outtmpl': os.path.join(save_path, '%(title)s')})
        else:
            ydl_opts.update({'writethumbnail': self.options.get('save_thumbnail', False), 'writesubtitles': self.options.get('embed_subs', False), 'concurrent_fragment_downloads': 16})
            if self.options['format'] == "Audio Only":
                ydl_opts['format'] = 'bestaudio/best'; ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]
            else:
                res = self.options.get('resolution', 'Best')
                if res == 'Best': ydl_opts['format'] = 'bestvideo+bestaudio/best'
                elif res == '4K': ydl_opts['format'] = 'bestvideo[height>=2160]+bestaudio/bestvideo[height>=1440]+bestaudio/best'
                elif res == '1080p': ydl_opts['format'] = 'bestvideo[height=1080]+bestaudio/bestvideo[height>=1080]+bestaudio/best'
                elif res == '720p': ydl_opts['format'] = 'bestvideo[height=720]+bestaudio/bestvideo[height>=720]+bestaudio/best'
                ydl_opts['merge_output_format'] = 'mp4'

        if self.options.get('proxy'): ydl_opts['proxy'] = self.options.get('proxy')
        if self.options.get('cookies_path'): ydl_opts['cookiefile'] = self.options.get('cookies_path')

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                title = info.get('title', 'Unknown Media')
                self.callbacks['log'](self.task_id, f"Found: {title}")
                if self.cancelled: raise Exception("Cancelled")
                ydl.download([self.url])
                
                if mode == 'thumbnail': fpath = os.path.join(save_path, f"{clean_filename(title)}.jpg")
                else:
                    fpath = ydl.prepare_filename(info)
                    if self.options['format'] == "Audio Only": fpath = os.path.splitext(fpath)[0] + ".mp3"
                
                if not self.cancelled: self.callbacks['finished'](self.task_id, {'title': title, 'platform': detect_platform(self.url), 'size': format_size(info.get('filesize', 0)), 'path': fpath, 'date': get_timestamp()}, True)
                else: self.callbacks['finished'](self.task_id, {}, False)
        except: 
            if not self.cancelled: self.callbacks['finished'](self.task_id, {}, False)

    def hook(self, d):
        if self.cancelled: raise Exception("Cancelled")
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            p = (downloaded / total * 100) if total > 0 else 0
            self.callbacks['progress'](self.task_id, int(p), clean_text(d.get('_speed_str', 'N/A')))
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def clean_filename(s): return "".join([c for c in s if c.isalpha() or c.isdigit() or c in " .-_"]).rstrip()

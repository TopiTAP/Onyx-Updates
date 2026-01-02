# 💎 Onyx Studio
> **The Next-Gen Media Downloader.**  
> *Built for Speed. Powered by Intelligence.*

![Version](https://img.shields.io/github/v/release/TopiTAP/Onyx-Updates?style=for-the-badge&color=0078D7)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?style=for-the-badge&logo=windows)
![Downloads](https://img.shields.io/github/downloads/TopiTAP/Onyx-Updates/total?style=for-the-badge&color=success)

---

## 🚀 Overview
**Onyx Studio** is a premium desktop application designed to download video and audio from thousands of websites (YouTube, TikTok, Instagram, etc.). 

It distinguishes itself with a **Smart Dependency System**—you don't need to manually configure anything. The app automatically detects missing components (like FFmpeg) and installs them for you, ensuring 4K/1080p quality works out of the box.

---

## ✨ Key Features

### 🧠 Smart & Automated
*   **Plug & Play:** No manual setup required. The app automatically downloads and configures `ffmpeg.exe` on the first run.
*   **Auto-Updater:** Built-in system checks GitHub for new versions and updates the app instantly.

### ⚡ Performance
*   **Turbo Engine:** Uses **16x Multi-threaded** fragmentation to utilize 100% of your internet speed.
*   **Anti-Throttling:** Bypasses speed limits imposed by streaming servers.

### 🛠️ Powerful Tools
*   **YouTube Pro:** Force download in **4K, 1080p, or 720p**. Supports embedding subtitles and thumbnails.
*   **Thumbnail Extractor:** Dedicated tool to grab high-resolution cover art (JPG).
*   **No Watermarks:** Downloads clean videos from TikTok and Instagram Reels.
*   **Task Manager:** Monitor real-time speed, pause/cancel downloads, and clear finished tasks.

---

## 📥 Installation

### 1. Download
Go to the **[Releases Page](../../releases)** and download the latest `Onyx_Studio.exe`.

### 2. Run
Double-click the file. 
*   *On the first run, if high-quality components are missing, Onyx will ask to download them automatically. Just wait for the green bar to finish!*

---

## 📖 User Guide

| Section | Function |
| :--- | :--- |
| **⚡ Dashboard** | **Universal Downloader.** Paste any link here for a quick "Best Quality" download. |
| **🚀 Tasks** | **Queue Manager.** View active downloads, check speeds, cancel tasks, or "Clear Finished" items. |
| **🎬 YouTube Pro** | **Advanced Mode.** Specifically for YouTube: Select resolution (4K/1080p), Embed Subs, etc. |
| **🖼️ Thumbnails** | **Image Grabber.** Download the thumbnail/cover image of a video without downloading the video itself. |
| **📡 Settings** | **Network & Updates.** Configure Proxies/Cookies or manually check for App/Engine updates. |
| **📂 History** | **Library.** A log of your downloads. Click "Open" to play or "Delete" to remove files. |

---

## 👨‍💻 Build from Source

If you are a developer and want to modify the code:

### Prerequisites
*   Python 3.10+
*   `pip install PyQt6 yt-dlp requests pyperclip pyinstaller`

### Compile to EXE
To build the standalone executable with compression and icon:

```cmd
pyinstaller --noconsole --onefile --clean --upx-dir=. --icon=icon.ico --name="Onyx_Studio" onyx_app.py
```

---

## 🔄 How Updates Work
Onyx Studio features a **Serverless Update Architecture**:
1.  The app queries this GitHub Repository via API.
2.  If a new **Release Tag** (e.g., `v9.6`) is found, it alerts the user.
3.  Upon confirmation, it auto-downloads the new binary, replaces the old one, and restarts.

---

### ❤️ Credits
*   Developed by **TopiTAP**.
*   Powered by **yt-dlp** and **FFmpeg**.
*   GUI built with **PyQt6**.

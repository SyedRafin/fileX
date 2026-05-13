# FileX 🚀

A lightweight, web-based file transfer tool for sharing files across devices on the **same Wi-Fi or local network** — no internet required, no accounts, no installation on the receiving device.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-black?style=flat-square&logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Features

- **No client install** — receivers just open a URL in any browser
- **Drag & drop** upload with real-time progress bar
- **Live updates** — all connected browsers see new files instantly via WebSocket
- **Any file type** — images, videos, documents, archives, code, anything
- **Up to 2 GB** per file (configurable)
- **File management** — delete files directly from the UI
- **Works on all platforms** — Windows, macOS, Linux, Android, iOS (browser only for receivers)

---

## How It Works

```
Your Machine (runs Python)          Other Devices (just a browser)
┌─────────────────────────┐         ┌──────────────────────────┐
│  python fileX.py      │  Wi-Fi  │  Open http://192.168.x.x │
│  → starts web server    │ ──────► │  → drag & drop files     │
│  → saves files to disk  │ ◄────── │  → download any file     │
└─────────────────────────┘         └──────────────────────────┘
```

Files are uploaded to the machine running the Python server and stored in a local `filex_files/` folder. Any device on the same network can download them.

---

## Requirements

- Python 3.8 or higher
- pip

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/SyedRafin/filex.git
cd filex
```

### 2. (Recommended) Create a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Start the server

```bash
python filex.py
```

You will see:

```
  ╔══════════════════════════════════════╗
  ║           Filex is running           ║
  ╠══════════════════════════════════════╣
  ║  Local:    http://127.0.0.1:5050     ║
  ║  Network:  http://192.168.1.x:5050   ║
  ╠══════════════════════════════════════╣
  ║  Share the Network URL with devices  ║
  ║  on the same Wi-Fi / LAN             ║
  ╚══════════════════════════════════════╝
```

### Send files

1. Open `http://127.0.0.1:5050` in your browser
2. Drag & drop files onto the upload zone (or click to browse)
3. Click **Upload to network**

### Receive files

1. Open the **Network URL** (e.g. `http://192.168.1.5:5050`) on any device connected to the same Wi-Fi
2. Click **Download** next to any file

> The Network URL is also shown and clickable inside the app's "Network info" card.

---

## Configuration

All settings are at the top of `filex.py`:

| Setting | Default | Description |
|---|---|---|
| `PORT` | `5050` | Port the server listens on |
| `UPLOAD_DIR` | `filex_files/` | Folder where files are saved |
| `MAX_CONTENT_LENGTH` | `2 GB` | Maximum file size per upload |

To change the port to 8080:
```python
PORT = 8080
```

To allow larger files (e.g. 10 GB):
```python
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 * 1024
```

---

## Stopping the Server

Press `Ctrl+C` in the terminal. Uploaded files in `filex_files/` are kept on disk.

---

## Security Notes

- FileX is designed for **trusted local networks** (home, office, classroom).
- There is **no authentication** — anyone on the same network can upload and download.
- Do **not** expose the server port to the public internet.
- Uploaded files are stored in plain text on the host machine.

---

## Project Structure

```
filex/
├── filex.py            # entire application (server + UI in one file)
├── requirements.txt    # Python dependencies
├── LICENSE             # MIT License
├── README.md           # this file
└── filex_files/        # created automatically on first run (gitignored)
```

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

Copyright (c) 2026 **srotx**

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software, as long as the original copyright notice is included.

---

## Acknowledgements

Built with [Flask](https://flask.palletsprojects.com/) and [Flask-SocketIO](https://flask-socketio.readthedocs.io/).

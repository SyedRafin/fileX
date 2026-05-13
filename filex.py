"""
FileX - Web-based LAN File Transfer
Run:  python filex.py
Then open the printed Network URL on any device on the same Wi-Fi / LAN.
"""

import os
import uuid
import socket
import threading
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO, emit

# pip install flask flask-socketio

UPLOAD_DIR = Path("filex_files")
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
#app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2 GB

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

files = {}
files_lock = threading.Lock()
PORT = 5050


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def format_size(b):
    if b < 1024:
        return f"{b} B"
    if b < 1024 ** 2:
        return f"{b / 1024:.1f} KB"
    if b < 1024 ** 3:
        return f"{b / 1024**2:.1f} MB"
    return f"{b / 1024**3:.2f} GB"


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FileX</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
  :root {
    --bg:#080b10;--surface:#0e1219;--surface2:#141822;--border:#1e2535;
    --accent:#3b82f6;--accent-dim:#1e3a5f;--green:#22c55e;--green-dim:#14532d;
    --red:#ef4444;--text:#e2e8f0;--muted:#64748b;
    --mono:'JetBrains Mono','Fira Code','Courier New',monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:var(--mono);font-size:13px;min-height:100vh;}
  a{color:var(--accent);text-decoration:none;}
  .shell{max-width:860px;margin:0 auto;padding:2rem 1rem 4rem;}
  .hdr{margin-bottom:2rem;}
  .hdr-top{display:flex;align-items:baseline;gap:1rem;}
  .logo{font-size:1.6rem;font-weight:700;letter-spacing:-1px;color:#fff;}
  .logo span{color:var(--accent);}
  .pill{font-size:10px;padding:3px 8px;border-radius:20px;background:var(--accent-dim);color:var(--accent);letter-spacing:1px;text-transform:uppercase;}
  .pill.green{background:var(--green-dim);color:var(--green);}
  .hdr-sub{font-size:11px;color:var(--muted);margin-top:6px;}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;}
  @media(max-width:640px){.grid{grid-template-columns:1fr;}}
  .full{grid-column:1/-1;}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.25rem;}
  .card-label{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--muted);margin-bottom:1rem;display:flex;align-items:center;gap:8px;}
  .card-label::after{content:'';flex:1;height:1px;background:var(--border);}
  .dropzone{border:2px dashed var(--border);border-radius:8px;padding:2.5rem 1rem;text-align:center;cursor:pointer;transition:border-color .2s,background .2s;}
  .dropzone:hover,.dropzone.over{border-color:var(--accent);background:#1e293b18;}
  .dz-icon{font-size:2rem;margin-bottom:.75rem;opacity:.4;}
  .dropzone:hover .dz-icon,.dropzone.over .dz-icon{opacity:1;}
  .dz-title{color:#94a3b8;margin-bottom:4px;}
  .dz-hint{color:var(--muted);font-size:11px;}
  #fileInput{display:none;}
  .queue{margin-top:.75rem;display:flex;flex-direction:column;gap:6px;}
  .qitem{background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;display:flex;align-items:center;gap:8px;}
  .qname{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#cbd5e1;}
  .qsize{color:var(--muted);font-size:11px;white-space:nowrap;}
  .qrm{background:none;border:none;color:#334155;cursor:pointer;font-size:14px;line-height:1;}
  .qrm:hover{color:var(--red);}
  .progress-bar{height:3px;background:var(--border);border-radius:2px;overflow:hidden;margin-top:6px;}
  .progress-fill{height:100%;background:var(--accent);border-radius:2px;width:0%;transition:width .25s;}
  .progress-label{font-size:10px;color:var(--muted);margin-top:3px;}
  .btn{width:100%;padding:10px;border-radius:7px;border:none;cursor:pointer;font-family:var(--mono);font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;transition:all .15s;margin-top:10px;}
  .btn-blue{background:var(--accent);color:#fff;}
  .btn-blue:hover{filter:brightness(1.15);}
  .btn-blue:disabled{background:var(--accent-dim);color:#334155;cursor:not-allowed;}
  .info-row{display:flex;align-items:center;gap:6px;padding:8px 10px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;margin-top:8px;font-size:11px;color:var(--muted);cursor:pointer;transition:border-color .2s;}
  .info-row:hover{border-color:var(--accent);color:var(--text);}
  .info-val{flex:1;color:var(--accent);word-break:break-all;}
  .filelist{display:flex;flex-direction:column;gap:6px;}
  .fitem{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px 12px;display:flex;align-items:center;gap:10px;transition:border-color .2s;}
  .fitem:hover{border-color:#2d3f60;}
  .ficon{font-size:1.25rem;opacity:.5;}
  .finfo{flex:1;min-width:0;}
  .fname{color:#cbd5e1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px;}
  .fmeta{font-size:10px;color:var(--muted);}
  .dl-btn{background:var(--accent-dim);color:var(--accent);border:1px solid #1e3a5f;border-radius:5px;padding:5px 10px;font-family:var(--mono);font-size:11px;cursor:pointer;white-space:nowrap;transition:background .15s;}
  .dl-btn:hover{background:#1e4a7a;}
  .del-btn{background:none;border:none;color:#334155;cursor:pointer;font-size:14px;line-height:1;padding:0 2px;}
  .del-btn:hover{color:var(--red);}
  .log-box{background:#050810;border:1px solid var(--border);border-radius:6px;padding:10px;height:130px;overflow-y:auto;font-size:11px;color:#334155;}
  .log-line{margin-bottom:3px;}
  .log-line.ok{color:#166534;}
  .log-line.err{color:#7f1d1d;}
  .log-line.hi{color:#1e40af;}
  #toast{position:fixed;bottom:1.5rem;right:1.5rem;background:var(--surface);border:1px solid var(--green);border-radius:8px;padding:10px 16px;font-size:12px;color:var(--green);opacity:0;transition:opacity .3s;pointer-events:none;z-index:99;}
  .divider{height:1px;background:var(--border);margin:1rem 0;}
  .stat-row{display:flex;gap:8px;}
  .stat{flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;}
  .stat-val{font-size:1.3rem;font-weight:700;color:var(--accent);}
  .stat-lbl{font-size:10px;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:1px;}
  .badge-new{font-size:9px;background:var(--green-dim);color:var(--green);border-radius:4px;padding:1px 5px;margin-left:6px;vertical-align:middle;}
</style>
</head>
<body>
<div class="shell">
  <div class="hdr">
    <div class="hdr-top">
      <div class="logo">File<span>X</span> by SRotX</div>
      <span class="pill" id="connPill">connecting...</span>
    </div>
    <div class="hdr-sub">Peer-to-peer file sharing over your local network - No internet required</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-label">Send files</div>
      <div class="dropzone" id="dropZone" onclick="document.getElementById('fileInput').click()">
        <div class="dz-icon">&#8679;</div>
        <div class="dz-title">Drop files here</div>
        <div class="dz-hint">or click to browse</div>
      </div>
      <input type="file" id="fileInput" multiple/>
      <div class="queue" id="queue"></div>
      <button class="btn btn-blue" id="sendBtn" disabled onclick="uploadFiles()">Upload to network</button>
    </div>

    <div class="card">
      <div class="card-label">Network info</div>
      <div style="color:var(--muted);font-size:11px;margin-bottom:8px;">Share this URL with anyone on the same Wi-Fi or LAN:</div>
      <div class="info-row" id="urlRow" onclick="copyURL()">
        <span>&#128279;</span>
        <span class="info-val" id="serverURL">-</span>
        <span>&#10697;</span>
      </div>
      <div class="divider"></div>
      <div class="stat-row">
        <div class="stat">
          <div class="stat-val" id="totalFiles">0</div>
          <div class="stat-lbl">Files available</div>
        </div>
        <div class="stat">
          <div class="stat-val" id="totalSize">0 B</div>
          <div class="stat-lbl">Total size</div>
        </div>
      </div>
      <div class="divider"></div>
      <div class="card-label" style="margin-bottom:.5rem;">Activity log</div>
      <div class="log-box" id="log"></div>
    </div>

    <div class="card full">
      <div class="card-label">Available files</div>
      <div class="filelist" id="filelist">
        <div style="color:var(--muted);font-size:12px;padding:1rem 0;">No files yet - upload something above.</div>
      </div>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
const socket = io();
let pendingFiles = [];

socket.on('connect', () => {
  document.getElementById('connPill').textContent = 'connected';
  document.getElementById('connPill').className = 'pill green';
  log('Connected to server', 'ok');
});
socket.on('disconnect', () => {
  document.getElementById('connPill').textContent = 'offline';
  document.getElementById('connPill').className = 'pill';
  log('Disconnected', 'err');
});
socket.on('file_added', (f) => {
  log('New file: ' + f.name + ' (' + f.size_str + ') from ' + f.uploader, 'hi');
  refreshFiles();
  toast('Received: ' + f.name);
});
socket.on('file_removed', () => refreshFiles());
socket.on('server_url', (d) => {
  document.getElementById('serverURL').textContent = d.url;
});

const dz = document.getElementById('dropZone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('over'); addToQueue([...e.dataTransfer.files]); });
document.getElementById('fileInput').addEventListener('change', e => { addToQueue([...e.target.files]); e.target.value = ''; });

function addToQueue(fs) {
  fs.forEach(f => { if (!pendingFiles.find(x => x.name === f.name && x.size === f.size)) pendingFiles.push(f); });
  renderQueue();
}

function renderQueue() {
  const el = document.getElementById('queue');
  document.getElementById('sendBtn').disabled = pendingFiles.length === 0;
  if (!pendingFiles.length) { el.innerHTML = ''; return; }
  el.innerHTML = pendingFiles.map((f, i) => '<div class="qitem"><span style="opacity:.4">&#128196;</span><span class="qname">' + f.name + '</span><span class="qsize">' + formatSize(f.size) + '</span><button class="qrm" onclick="removeQueue(' + i + ')">x</button></div>').join('');
}

function removeQueue(i) { pendingFiles.splice(i, 1); renderQueue(); }

async function uploadFiles() {
  if (!pendingFiles.length) return;
  document.getElementById('sendBtn').disabled = true;
  const files = [...pendingFiles];
  pendingFiles = []; renderQueue();
  for (const file of files) {
    const fd = new FormData();
    fd.append('file', file);
    const pid = 'up_' + Math.random().toString(36).slice(2, 6);
    addProgressUI(pid, file.name, file.size);
    try { await uploadWithProgress(fd, pid); }
    catch(e) { log('Upload failed: ' + file.name, 'err'); }
    removeProgressUI(pid);
  }
}

function addProgressUI(id, name, size) {
  const el = document.getElementById('queue');
  const div = document.createElement('div');
  div.id = id; div.className = 'qitem';
  div.innerHTML = '<span style="opacity:.4">&#8679;</span><div style="flex:1;min-width:0"><div class="qname">' + name + '</div><div class="progress-bar"><div class="progress-fill" id="' + id + '_bar"></div></div><div class="progress-label" id="' + id + '_lbl">0% - ' + formatSize(size) + '</div></div>';
  el.appendChild(div);
}

function removeProgressUI(id) { const e = document.getElementById(id); if (e) e.remove(); }

function uploadWithProgress(fd, pid) {
  return new Promise((res, rej) => {
    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = e => {
      if (!e.lengthComputable) return;
      const p = Math.round(e.loaded / e.total * 100);
      const bar = document.getElementById(pid + '_bar');
      const lbl = document.getElementById(pid + '_lbl');
      if (bar) bar.style.width = p + '%';
      if (lbl) lbl.textContent = p + '% - ' + formatSize(e.loaded) + ' / ' + formatSize(e.total);
    };
    xhr.onload = () => xhr.status < 300 ? res() : rej(new Error(xhr.statusText));
    xhr.onerror = () => rej(new Error('Network error'));
    xhr.open('POST', '/upload');
    xhr.send(fd);
  });
}

async function refreshFiles() {
  const res = await fetch('/files');
  const data = await res.json();
  const el = document.getElementById('filelist');
  document.getElementById('totalFiles').textContent = data.files.length;
  document.getElementById('totalSize').textContent = data.total_size_str;
  if (!data.files.length) { el.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:1rem 0;">No files yet - upload something above.</div>'; return; }
  el.innerHTML = data.files.map(f =>
    '<div class="fitem"><span class="ficon">' + fileIcon(f.name) + '</span><div class="finfo"><div class="fname">' + f.name + (f.is_new ? '<span class="badge-new">NEW</span>' : '') + '</div><div class="fmeta">' + f.size_str + ' - uploaded ' + f.age + ' - by ' + f.uploader + '</div></div><a href="/download/' + f.id + '" download="' + f.name + '"><button class="dl-btn">&#8681; Download</button></a><button class="del-btn" onclick="deleteFile(\'' + f.id + '\',\'' + f.name.replace(/'/g, "\\'") + '\')">x</button></div>'
  ).join('');
}

async function deleteFile(id, name) {
  if (!confirm('Remove "' + name + '" from the server?')) return;
  await fetch('/delete/' + id, { method: 'DELETE' });
  log('Deleted: ' + name, 'err');
}

function copyURL() {
  const url = document.getElementById('serverURL').textContent;
  if (url === '-') return;
  navigator.clipboard.writeText(url).then(() => toast('URL copied!'));
}

function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg; el.style.opacity = 1;
  clearTimeout(el._t); el._t = setTimeout(() => el.style.opacity = 0, 3000);
}

function log(msg, type) {
  const el = document.getElementById('log');
  const line = document.createElement('div');
  line.className = 'log-line ' + (type || '');
  line.textContent = '[' + new Date().toLocaleTimeString() + '] ' + msg;
  el.prepend(line);
}

function formatSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  if (b < 1073741824) return (b/1048576).toFixed(1) + ' MB';
  return (b/1073741824).toFixed(2) + ' GB';
}

function fileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  const m = {pdf:'PDF',jpg:'IMG',jpeg:'IMG',png:'IMG',gif:'IMG',webp:'IMG',svg:'IMG',mp4:'VID',mov:'VID',avi:'VID',mkv:'VID',mp3:'AUD',wav:'AUD',flac:'AUD',zip:'ZIP',rar:'ZIP',gz:'ZIP',tar:'ZIP',py:'CODE',js:'CODE',ts:'CODE',html:'CODE',css:'CODE',json:'CODE',txt:'TXT',md:'TXT',doc:'DOC',docx:'DOC',xls:'XLS',xlsx:'XLS'};
  return m[ext] || 'FILE';
}

refreshFiles();
setInterval(refreshFiles, 10000);
</script>
</body>
</html>"""


@app.route("/")
def index():
    return HTML


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    file_id = str(uuid.uuid4())
    safe_name = f.filename.replace("/", "_").replace("\\", "_")
    dest = UPLOAD_DIR / (file_id + "_" + safe_name)
    f.save(str(dest))
    size = dest.stat().st_size
    uploader = request.remote_addr or "unknown"
    with files_lock:
        files[file_id] = {
            "id": file_id,
            "name": safe_name,
            "path": str(dest),
            "size": size,
            "size_str": format_size(size),
            "uploader": uploader,
            "uploaded_at": time.time(),
        }
    socketio.emit("file_added", {"id": file_id, "name": safe_name, "size_str": format_size(size), "uploader": uploader})
    return jsonify({"id": file_id, "name": safe_name}), 201


@app.route("/files")
def list_files():
    now = time.time()
    result = []
    with files_lock:
        for fid, meta in files.items():
            age_s = now - meta["uploaded_at"]
            age = f"{int(age_s)}s ago" if age_s < 60 else (f"{int(age_s/60)}m ago" if age_s < 3600 else f"{int(age_s/3600)}h ago")
            result.append({**meta, "age": age, "is_new": age_s < 30})
    result.sort(key=lambda x: x["uploaded_at"], reverse=True)
    total = sum(f["size"] for f in result)
    return jsonify({"files": result, "total_size_str": format_size(total)})


@app.route("/download/<file_id>")
def download(file_id):
    with files_lock:
        meta = files.get(file_id)
    if not meta:
        return "File not found", 404
    return send_file(meta["path"], as_attachment=True, download_name=meta["name"])


@app.route("/delete/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    with files_lock:
        meta = files.pop(file_id, None)
    if not meta:
        return jsonify({"error": "Not found"}), 404
    try:
        os.remove(meta["path"])
    except OSError:
        pass
    socketio.emit("file_removed", {"id": file_id, "name": meta["name"]})
    return jsonify({"ok": True})


@socketio.on("connect")
def on_connect():
    emit("server_url", {"url": f"http://{get_local_ip()}:{PORT}"})


if __name__ == "__main__":
    ip = get_local_ip()
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║          FileX is running          ║")
    print("  ╠══════════════════════════════════════╣")
    print(f"  ║  Local:    http://127.0.0.1:{PORT}      ║")
    print(f"  ║  Network:  http://{ip}:{PORT}    ║")
    print("  ╠══════════════════════════════════════╣")
    print("  ║  Share the Network URL with devices  ║")
    print("  ║  on the same Wi-Fi / LAN             ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print("  Files saved to: ./filex_files/")
    print("  Press Ctrl+C to stop.")
    print()
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False)

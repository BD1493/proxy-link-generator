import threading
import time
import requests
from flask import Flask, render_template_string, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# --- SETTINGS ---
PROXY_FILE = "proxies.txt"
WORKING_FILE = "working_proxies.txt"
TEST_URL = "http://httpbin.org/ip"
CHECK_INTERVAL = 300  # Re-check every 5 minutes
TIMEOUT = 3

# Global variable to store live results
live_results = []

def check_single_proxy(proxy):
    proxy = proxy.strip()
    if not proxy: return None
    try:
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        r = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT)
        if r.status_code == 200:
            return proxy
    except:
        pass
    return None

def background_checker():
    """Loops forever, checking proxies and saving working ones."""
    global live_results
    while True:
        print("[*] Starting background proxy check...")
        try:
            with open(PROXY_FILE, "r") as f:
                proxies = f.readlines()
        except FileNotFoundError:
            print(f"[!] {PROXY_FILE} not found.")
            time.sleep(60)
            continue

        working = []
        new_results = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            check_tasks = {executor.submit(check_single_proxy, p): p for p in proxies}
            for future in check_tasks:
                proxy_addr = check_tasks[future]
                result = future.result()
                if result:
                    working.append(result)
                    new_results.append({"ip": result, "status": "Online", "color": "#2ecc71"})
                else:
                    new_results.append({"ip": proxy_addr.strip(), "status": "Offline", "color": "#e74c3c"})

        # Save only the working ones to the new file
        with open(WORKING_FILE, "w") as f:
            f.write("\n".join(working))
            
        live_results = new_results
        print(f"[*] Check complete. Found {len(working)} working proxies. Saved to {WORKING_FILE}")
        time.sleep(CHECK_INTERVAL)

@app.route('/')
def dashboard():
    # Stealth Google Drive Template
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Drive - Google Drive</title>
        <link rel="icon" href="https://ssl.gstatic.com/docs/doclist/images/infinite_arrow_favicon_5.ico">
        <style>
            body { font-family: 'Segoe UI', Arial; background: #f8f9fa; margin: 0; display: flex; }
            .sidebar { width: 240px; padding: 20px; background: #f8f9fa; height: 100vh; border-right: 1px solid #dadce0; }
            .main { flex-grow: 1; padding: 20px; overflow-y: auto; }
            .card { background: white; border-radius: 8px; border: 1px solid #dadce0; padding: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { text-align: left; color: #5f6368; font-size: 14px; border-bottom: 1px solid #dadce0; padding: 10px; }
            td { padding: 12px 10px; border-bottom: 1px solid #eee; font-size: 14px; }
            .badge { padding: 4px 12px; border-radius: 20px; color: white; font-size: 12px; font-weight: bold; }
            .btn { background: #1a73e8; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 13px; }
            .btn-stealth { background: #34a853; margin-left: 10px; }
            .btn:hover { opacity: 0.9; }
            .stealth-warning { font-size: 12px; color: #5f6368; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <img src="https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_logo.svg" width="40" style="margin-bottom:20px">
            <div style="color:#3c4043; font-weight:500">My Drive</div>
            <div style="color:#5f6368; margin-top:15px; font-size:14px">📁 Proxies</div>
            <div style="color:#5f6368; margin-top:10px; font-size:14px">⚙️ Settings</div>
        </div>
        <div class="main">
            <div class="card">
                <h2>Proxy Manager</h2>
                <p class="stealth-warning">All links opened via "Stealth Tab" will appear as <b>about:blank</b> in history.</p>
                <table>
                    <thead>
                        <tr><th>Address</th><th>Status</th><th>Actions</th></tr>
                    </thead>
                    <tbody id="proxy-table">
                        {% for p in results %}
                        <tr>
                            <td><code>{{ p.ip }}</code></td>
                            <td><span class="badge" style="background-color: {{ p.color }}">{{ p.status }}</span></td>
                            <td>
                                <a href="http://{{ p.ip }}" target="_blank" class="btn">Normal Open</a>
                                <button onclick="openStealth('http://{{ p.ip }}')" class="btn btn-stealth">Stealth Open</button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            function openStealth(url) {
                var win = window.open();
                win.document.body.style.margin = '0';
                win.document.body.style.height = '100vh';
                var iframe = win.document.createElement('iframe');
                iframe.style.border = 'none';
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.margin = '0';
                iframe.src = url;
                win.document.body.appendChild(iframe);
            }
            
            // Auto-refresh the page every 60 seconds to show latest background check results
            setTimeout(function(){ location.reload(); }, 60000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html, results=live_results)

if __name__ == '__main__':
    # Start the background thread
    threading.Thread(target=background_checker, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)

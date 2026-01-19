import random
import re
import requests
import base64
import threading
import time
from flask import Flask, request, Response
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# --- CONFIGURATION ---
PROXY_FILE = 'proxies.txt'
TEST_URL = "http://httpbin.org/ip"
TIMEOUT = 3
CHECK_INTERVAL = 300  # Re-check every 5 minutes
LIVE_POOL = []        # This will be updated by the background thread

def load_all_proxies():
    try:
        with open(PROXY_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def check_single_node(proxy):
    """Tests if a proxy is alive."""
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT)
        if r.status_code == 200:
            return proxy
    except:
        pass
    return None

def proxy_monitor_thread():
    """Background task that keeps the LIVE_POOL fresh."""
    global LIVE_POOL
    while True:
        all_nodes = load_all_proxies()
        if not all_nodes:
            print("[!] proxies.txt is empty. Waiting...")
            time.sleep(30)
            continue
            
        print(f"[*] Checking {len(all_nodes)} nodes...")
        valid_nodes = []
        
        # Use 20 threads to check the list quickly
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(check_single_node, all_nodes))
            valid_nodes = [r for r in results if r is not None]
            
        LIVE_POOL = valid_nodes
        print(f"[*] Update Complete. {len(LIVE_POOL)} nodes are currently ONLINE.")
        time.sleep(CHECK_INTERVAL)

def get_random_proxy():
    """Selects a proxy only from the LIVE_POOL."""
    if not LIVE_POOL: 
        # Fallback to a random one if the pool hasn't loaded yet
        all_nodes = load_all_proxies()
        if not all_nodes: return None
        proxy = random.choice(all_nodes)
    else:
        proxy = random.choice(LIVE_POOL)
        
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

def rewrite_content(content, base_url, proxy_host):
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='ignore')
    
    soup = BeautifulSoup(content, 'html.parser')
    tags = {'a': 'href', 'link': 'href', 'img': 'src', 'script': 'src', 'form': 'action', 'source': 'src'}
    
    for tag_name, attr in tags.items():
        for tag in soup.find_all(tag_name):
            val = tag.get(attr)
            if val and not val.startswith(('data:', 'javascript:')):
                abs_url = urljoin(base_url, val)
                encoded_url = base64.b64encode(abs_url.encode()).decode()
                tag[attr] = f"{proxy_host}/proxy?url={encoded_url}"
    
    return soup.prettify()

@app.route('/')
def home():
    # Show how many nodes are live in the UI
    live_count = len(LIVE_POOL)
    return f'''
    <body style="background:#111; color:white; font-family:sans-serif; text-align:center; padding:100px;">
        <div style="position:fixed; top:20px; right:20px; background:#222; padding:10px; border-radius:5px; font-size:12px; border:1px solid #333;">
            Status: <span style="color:#00ff00;">● Online</span> ({live_count} Nodes)
        </div>
        <h1>Ghost Proxy</h1>
        <p style="color:#666;">URLs are encrypted and opened in about:blank to hide history.</p>
        <input type="text" id="url" placeholder="Enter website address..." style="padding:12px; width:400px; border-radius:5px; border:none; outline:none; background:#222; color:white;">
        <button onclick="launch()" style="padding:12px 20px; cursor:pointer; border-radius:5px; background:#007bff; color:white; border:none; font-weight:bold;">Launch Stealth Mode</button>

        <script>
            function launch() {{
                let target = document.getElementById('url').value;
                if(!target) return;
                if(!target.startsWith('http')) target = 'https://' + target;
                
                let scrambled = btoa(target);
                let proxyUrl = window.location.origin + '/proxy?url=' + scrambled;

                let win = window.open('about:blank', '_blank');
                win.document.body.style.margin = '0';
                win.document.body.style.height = '100vh';
                let iframe = win.document.createElement('iframe');
                iframe.src = proxyUrl;
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                win.document.body.appendChild(iframe);
            }}
        </script>
    </body>
    '''

@app.route('/proxy')
def proxy():
    encoded_url = request.args.get('url')
    if not encoded_url: return "No URL", 400

    try:
        target_url = base64.b64decode(encoded_url).decode()
    except:
        return "Invalid Encoded URL", 400

    proxy_host = request.host_url.rstrip('/')
    selected_proxy = get_random_proxy()

    try:
        headers = {{'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
        # If the first selected proxy fails, the next refresh or use will pick a new live one from the pool
        resp = requests.get(target_url, proxies=selected_proxy, headers=headers, timeout=10, verify=False)
        
        content_type = resp.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            output = rewrite_content(resp.content, target_url, proxy_host)
            return Response(output, mimetype='text/html')
        
        return Response(resp.content, content_type=content_type)

    except Exception as e:
        return f"Node Error: {{e}}<br><br>Tip: Refreshing usually picks a new working node.", 502

if __name__ == '__main__':
    # Start the background checker thread
    threading.Thread(target=proxy_monitor_thread, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)

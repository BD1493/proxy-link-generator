import random
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
TIMEOUT = 4            # Short timeout to keep retries snappy
CHECK_INTERVAL = 300   # Re-check proxy health every 5 minutes
LIVE_POOL = []         # This is updated by the background thread
MAX_RETRIES = 3        # Attempts to find a working proxy per request

def load_all_proxies():
    """Reads the raw proxy list from file."""
    try:
        with open(PROXY_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def check_single_node(proxy):
    """Tests if a specific proxy is responsive."""
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT)
        if r.status_code == 200:
            return proxy
    except:
        pass
    return None

def proxy_monitor_thread():
    """Background task that keeps the LIVE_POOL updated with working IPs."""
    global LIVE_POOL
    while True:
        all_nodes = load_all_proxies()
        if not all_nodes:
            print("[!] proxies.txt is empty. Monitoring paused.")
            time.sleep(30)
            continue
            
        print(f"[*] Verifying {len(all_nodes)} nodes...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(check_single_node, all_nodes))
            valid_nodes = [r for r in results if r is not None]
            
        LIVE_POOL = valid_nodes
        print(f"[*] Monitor Update: {len(LIVE_POOL)} nodes are currently ONLINE.")
        time.sleep(CHECK_INTERVAL)

def get_random_proxy():
    """Picks a proxy from the live pool; falls back to raw list if pool is empty."""
    if not LIVE_POOL: 
        all_nodes = load_all_proxies()
        return random.choice(all_nodes) if all_nodes else None
    return random.choice(LIVE_POOL)

def rewrite_content(content, base_url, proxy_host):
    """Rewrites HTML links so they continue to pass through your proxy."""
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='ignore')
    
    soup = BeautifulSoup(content, 'html.parser')
    # List of attributes to rewrite
    tags = {'a': 'href', 'link': 'href', 'img': 'src', 'script': 'src', 'form': 'action', 'source': 'src'}
    
    for tag_name, attr in tags.items():
        for tag in soup.find_all(tag_name):
            val = tag.get(attr)
            if val and not val.startswith(('data:', 'javascript:', '#')):
                abs_url = urljoin(base_url, val)
                # Encrypt/Scramble the URL for the next layer
                encoded_url = base64.b64encode(abs_url.encode()).decode()
                tag[attr] = f"{proxy_host}/proxy?url={encoded_url}"
    
    return soup.prettify()

@app.route('/')
def home():
    live_count = len(LIVE_POOL)
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Drive - Google Drive</title>
        <link rel="icon" href="https://ssl.gstatic.com/docs/doclist/images/infinite_arrow_favicon_5.ico">
        <style>
            body {{ background:#111; color:white; font-family: 'Segoe UI', sans-serif; text-align:center; padding:100px; margin:0; }}
            .status {{ position:fixed; top:20px; right:20px; background:#222; padding:10px; border-radius:5px; font-size:12px; border:1px solid #333; }}
            h1 {{ font-size: 3em; margin-bottom: 10px; }}
            .desc {{ color:#666; margin-bottom: 30px; }}
            input {{ padding:15px; width:450px; border-radius:8px; border:1px solid #333; outline:none; background:#1a1a1a; color:white; font-size: 16px; }}
            button {{ padding:15px 25px; cursor:pointer; border-radius:8px; background:#1a73e8; color:white; border:none; font-weight:bold; font-size: 16px; margin-left: 10px; transition: 0.3s; }}
            button:hover {{ background: #1557b0; box-shadow: 0 0 15px rgba(26, 115, 232, 0.4); }}
        </style>
    </head>
    <body>
        <div class="status">
            Nodes: <span style="color:#00ff00;">● Online</span> ({live_count})
        </div>
        <h1>Ghost Proxy</h1>
        <p class="desc">Encrypted traffic & history cloaking enabled.</p>
        <input type="text" id="url" placeholder="Paste a link or type a URL..." onkeydown="if(event.key==='Enter') launch()">
        <button onclick="launch()">Launch Stealth Mode</button>

        <script>
            function launch() {{
                let target = document.getElementById('url').value;
                if(!target) return;
                if(!target.startsWith('http')) target = 'https://' + target;
                
                // Base64 encode the target URL
                let scrambled = btoa(target);
                let proxyUrl = window.location.origin + '/proxy?url=' + scrambled;

                // Open about:blank to hide history
                let win = window.open('about:blank', '_blank');
                win.document.title = "My Drive - Google Drive";
                
                // Style the about:blank page and inject the proxy iframe
                win.document.body.style.margin = '0';
                win.document.body.style.height = '100vh';
                win.document.body.style.overflow = 'hidden';
                
                let iframe = win.document.createElement('iframe');
                iframe.src = proxyUrl;
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                iframe.style.margin = '0';
                
                win.document.body.appendChild(iframe);
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/proxy')
def proxy():
    encoded_url = request.args.get('url')
    if not encoded_url: return "No URL provided", 400

    try:
        target_url = base64.b64decode(encoded_url).decode()
    except:
        return "Invalid Encoded URL", 400

    proxy_host = request.host_url.rstrip('/')
    last_error = ""

    # --- AUTO-RETRY LOOP ---
    for attempt in range(MAX_RETRIES):
        selected_ip = get_random_proxy()
        if not selected_ip:
            return "Critical Error: No proxy nodes found in proxies.txt", 500
            
        proxies = {"http": f"http://{selected_ip}", "https": f"http://{selected_ip}"}
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            resp = requests.get(target_url, proxies=proxies, headers=headers, timeout=TIMEOUT, verify=False)
            
            content_type = resp.headers.get('Content-Type', '')
            
            # If it's a website, rewrite the links
            if 'text/html' in content_type:
                output = rewrite_content(resp.content, target_url, proxy_host)
                return Response(output, mimetype='text/html')
            
            # Otherwise (images, CSS, JS), return the raw content
            return Response(resp.content, content_type=content_type)

        except Exception as e:
            last_error = str(e)
            print(f"[!] Node {selected_ip} failed. Attempt {attempt + 1}/{MAX_RETRIES}...")
            continue 

    return f'''
    <div style="font-family:sans-serif; text-align:center; padding-top:50px;">
        <h2>All Proxy Nodes Failed</h2>
        <p style="color:red;">Error: {last_error}</p>
        <button onclick="location.reload()" style="padding:10px 20px; cursor:pointer;">Retry with New Nodes</button>
    </div>
    ''', 502

if __name__ == '__main__':
    # Start the monitor in a separate thread so the website stays fast
    threading.Thread(target=proxy_monitor_thread, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)

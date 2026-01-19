# =================================================================
# COPYRIGHT NOTICE
# Copyright (c) 2026 BD. All rights reserved.
# 
# This software is protected under the Permission-Only Open License (2026).
# Unauthorized use, modification, or distribution is strictly prohibited.
# For usage permission, visit: https://forms.gle/j6sjiAs7qfL3Jvnf8
# =================================================================

import random
import re
import requests
import base64
import os
from flask import Flask, request, Response
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

# --- PROXY POOL LOAD ---
def load_proxies():
    """Reads IPs from proxies.txt in the root directory."""
    proxies = []
    if os.path.exists('proxies.txt'):
        with open('proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
    return proxies

PROXY_POOL = load_proxies()

def get_random_proxy():
    """Selects a random IP from the pool for rotation."""
    if not PROXY_POOL: return None
    proxy = random.choice(PROXY_POOL)
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

# --- REWRITING ENGINE ---
def rewrite_content(content, base_url, proxy_host):
    """Parses HTML and rewrites tags to route through the proxy."""
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='ignore')
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Update HTML tags: href, src, action
    tags = {'a': 'href', 'link': 'href', 'img': 'src', 'script': 'src', 'form': 'action', 'source': 'src', 'video': 'src'}
    for tag_name, attr in tags.items():
        for tag in soup.find_all(tag_name):
            val = tag.get(attr)
            if val and not val.startswith(('data:', 'javascript:', '#')):
                abs_url = urljoin(base_url, val)
                # Scramble the URL with Base64 to hide it from history
                encoded_url = base64.b64encode(abs_url.encode()).decode()
                tag[attr] = f"{proxy_host}/proxy?url={encoded_url}"
    
    html_str = soup.prettify()

    # Update CSS url() imports via Regex
    pattern = r'url\((["\']?)([^)]+)\1\)'
    def replace_css(match):
        quote, url = match.group(1), match.group(2)
        if url.startswith('data:'): return match.group(0)
        abs_url = urljoin(base_url, url)
        encoded_url = base64.b64encode(abs_url.encode()).decode()
        return f'url({quote}{proxy_host}/proxy?url={encoded_url}{quote})'

    return re.sub(pattern, replace_css, html_str)

# --- ROUTES ---
@app.route('/')
def home():
    """Disguised landing page with about:blank injector."""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>My Drive - Google Drive</title>
        <link rel="icon" href="https://ssl.gstatic.com/images/branding/product/1x/drive_2020q4_32dp.png">
        <style>
            body { background: #202124; color: #e8eaed; font-family: 'Roboto', arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .container { text-align: center; }
            input { padding: 14px 20px; width: 450px; border-radius: 24px; border: 1px solid #5f6368; background: #303134; color: white; outline: none; font-size: 16px; margin-bottom: 20px; }
            button { padding: 10px 24px; border-radius: 4px; border: none; background: #8ab4f8; color: #202124; font-weight: 500; cursor: pointer; font-size: 14px; }
            button:hover { background: #aecbfa; }
            p { color: #9aa0a6; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <img src="https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg" width="80" style="margin-bottom:20px;">
            <h1>My Drive</h1>
            <input type="text" id="url" placeholder="Search in Drive...">
            <br>
            <button onclick="launch()">Open File</button>
            <p>Access your files securely from any node.</p>
        </div>

        <script>
            function launch() {
                let target = document.getElementById('url').value;
                if(!target) return;
                if(!target.startsWith('http')) target = 'https://' + target;
                
                // Base64 Scramble the URL
                let encoded = btoa(target);
                let proxyUrl = window.location.origin + '/proxy?url=' + encoded;

                // Stealth Launch: Create about:blank and inject iframe
                let win = window.open('about:blank', '_blank');
                win.document.body.style.margin = '0';
                win.document.body.style.padding = '0';
                win.document.body.style.height = '100vh';
                win.document.title = 'Loading File...';
                
                let iframe = win.document.createElement('iframe');
                iframe.style.border = 'none';
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.src = proxyUrl;
                win.document.body.appendChild(iframe);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/proxy')
def proxy():
    """The engine that fetches content using rotated IPs."""
    encoded_url = request.args.get('url')
    if not encoded_url: return "URL Required", 400

    try:
        target_url = base64.b64decode(encoded_url).decode()
    except:
        return "Invalid Data Stream", 400

    proxy_host = request.host_url.rstrip('/')
    selected_node = get_random_proxy()

    try:
        # Standard headers to look like a real browser
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        
        # Request with rotation
        resp = requests.get(target_url, proxies=selected_node, headers=headers, timeout=12, verify=False)
        
        content_type = resp.headers.get('Content-Type', '')

        # HTML Processing
        if 'text/html' in content_type:
            output = rewrite_content(resp.content, target_url, proxy_host)
            return Response(output, mimetype='text/html')
        
        # Binary/Static Processing (Images, CSS, JS)
        return Response(resp.content, mimetype=content_type)

    except Exception as e:
        return f"Node Connection Failed. Refresh to rotate. <br>System Message: {e}", 502

if __name__ == '__main__':
    # Defaulting to 10000 for Render compatibility
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

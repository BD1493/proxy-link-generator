import random
import re
import requests
import base64
import os
from flask import Flask, request, Response
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

# Load IPs
def load_proxies():
    proxies = []
    if os.path.exists('proxies.txt'):
        with open('proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
    return proxies

PROXY_POOL = load_proxies()

def get_random_proxy():
    if not PROXY_POOL: return None
    proxy = random.choice(PROXY_POOL)
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

def rewrite_content(content, base_url, proxy_host):
    # Decode content safely
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='ignore')
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # 1. Update HTML tags to point to proxy
    tags = {'a': 'href', 'link': 'href', 'img': 'src', 'script': 'src', 'form': 'action', 'source': 'src'}
    for tag_name, attr in tags.items():
        for tag in soup.find_all(tag_name):
            val = tag.get(attr)
            if val and not val.startswith(('data:', 'javascript:', '#')):
                abs_url = urljoin(base_url, val)
                encoded_url = base64.b64encode(abs_url.encode()).decode()
                tag[attr] = f"{proxy_host}/proxy?url={encoded_url}"
    
    html_str = soup.prettify()

    # 2. Update CSS url() links
    pattern = r'url\((["\']?)([^)]+)\1\)'
    def replace_css(match):
        quote, url = match.group(1), match.group(2)
        if url.startswith('data:'): return match.group(0)
        abs_url = urljoin(base_url, url)
        encoded_url = base64.b64encode(abs_url.encode()).decode()
        return f'url({quote}{proxy_host}/proxy?url={encoded_url}{quote})'

    return re.sub(pattern, replace_css, html_str)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Google Drive</title> <link rel="icon" href="https://ssl.gstatic.com/images/branding/product/1x/drive_2020q4_32dp.png">
        <style>
            body { background: #202124; color: #e8eaed; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            input { padding: 15px; width: 400px; border-radius: 24px; border: 1px solid #5f6368; background: #303134; color: white; outline: none; font-size: 16px; }
            button { margin-top: 20px; padding: 10px 25px; border-radius: 4px; border: none; background: #8ab4f8; color: #202124; font-weight: bold; cursor: pointer; }
            button:hover { background: #aecbfa; }
        </style>
    </head>
    <body>
        <h1>My Drive</h1>
        <input type="text" id="url" placeholder="Search Drive...">
        <button onclick="launch()">Open File</button>

        <script>
            function launch() {
                let target = document.getElementById('url').value;
                if(!target) return;
                if(!target.startsWith('http')) target = 'https://' + target;
                
                // Encode the URL
                let encoded = btoa(target);
                let proxyUrl = window.location.origin + '/proxy?url=' + encoded;

                // Open about:blank and inject iframe
                let win = window.open();
                win.document.body.style.margin = '0';
                win.document.body.style.height = '100vh';
                let iframe = win.document.createElement('iframe');
                iframe.style.border = 'none';
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.margin = '0';
                iframe.src = proxyUrl;
                win.document.body.appendChild(iframe);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/proxy')
def proxy():
    encoded_url = request.args.get('url')
    if not encoded_url: return "Missing URL", 400

    try:
        target_url = base64.b64decode(encoded_url).decode()
    except:
        return "Invalid URL Encoding", 400

    proxy_host = request.host_url.rstrip('/')
    selected_proxy = get_random_proxy()

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(target_url, proxies=selected_proxy, headers=headers, timeout=10, verify=False)
        
        content_type = resp.headers.get('Content-Type', '')

        # Rewrite HTML
        if 'text/html' in content_type:
            output = rewrite_content(resp.content, target_url, proxy_host)
            return Response(output, mimetype='text/html')
        
        # Rewrite CSS
        elif 'text/css' in content_type:
            # Simple CSS rewrite logic here if needed, or return raw
            return Response(resp.content, mimetype=content_type)

        # Return everything else (Images, JS) raw
        return Response(resp.content, mimetype=content_type)

    except Exception as e:
        return f"Error fetching {target_url} via proxy. <br>Details: {e}", 502

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

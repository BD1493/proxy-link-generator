import requests
import concurrent.futures

INPUT_FILE = 'proxies.txt'
OUTPUT_FILE = 'valid_proxies.txt'

def check(proxy):
    try:
        print(f"Checking {proxy}...", end='\r')
        r = requests.get("https://www.google.com", proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=5)
        if r.status_code == 200:
            return proxy
    except:
        pass
    return None

def main():
    print("Starting check...")
    with open(INPUT_FILE, 'r') as f:
        proxies = [l.strip() for l in f if l.strip()]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(check, proxies))
    
    valid = [p for p in results if p]
    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(valid))
    print(f"\nDone! Found {len(valid)} working IPs. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

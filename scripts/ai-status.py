import urllib.request
import urllib.error
import urllib.parse
import socket
import json
import time
import os
from dotenv import load_dotenv

# Load the .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# --- CONFIGURATION ---
SERVICES = [
    {
        "name": "Qwen3-Coder-30B",
        "url": f"{os.getenv('NEXT_PUBLIC_AI_API_URL', '')}/chat/completions",
        "key": os.getenv('NEXT_PUBLIC_AI_API_KEY', ''),
        "model": os.getenv('NEXT_PUBLIC_AI_MODEL', '')
    },
    {
        "name": "Hermes-3-Llama-3.1",
        "url": f"{os.getenv('AI_API_URL_2', '')}/chat/completions",
        "key": os.getenv('AI_API_KEY_2', ''),
        "model": os.getenv('AI_MODEL_2', '')
    },
    {
        "name": "Qwen3-Coder-Plus (iflow)",
        "url": f"{os.getenv('AI_API_URL_3', '')}/chat/completions",
        "key": os.getenv('AI_API_KEY_3', ''),
        "model": os.getenv('AI_MODEL_3', '')
    }
]

def get_connection_time(url):
    """Measures the pure TCP connection time to the host server in seconds."""
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    
    start = time.time()
    try:
        with socket.create_connection((hostname, port), timeout=5):
            # Removed * 1000 to keep it in seconds
            return time.time() - start 
    except Exception:
        return -1

def check_services():
    print(f"🤖 AI API HEALTH CHECK")
    print("=" * 80)
    print(f"{'SERVICE NAME':<20} | {'STATUS':<11} | {'CONN':<7} | {'RESP':<7} | {'INFO'}")
    print("-" * 80)

    for svc in SERVICES:
        if not svc["key"] or not svc["model"] or svc["url"] == "/chat/completions":
            print(f"{svc['name']:<20} | {'[!] ERROR':<11} | {'N/A':<7} | {'N/A':<7} | Missing .env config")
            continue

        # 1. Measure raw network connection time
        conn_latency = get_connection_time(svc["url"])
        # Formatted to 2 decimal places with an 's'
        conn_str = f"{conn_latency:.2f}s" if conn_latency != -1 else "FAIL"

        # 2. Measure actual API/Model response time
        payload = json.dumps({
            "model": svc["model"],
            "messages": [{"role": "user", "content": "Ping"}],
            "max_tokens": 1
        }).encode('utf-8')
        
        req = urllib.request.Request(svc["url"], data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {svc["key"]}')
        
        start_time = time.time()
        resp_latency = 0
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                # Removed * 1000
                resp_latency = time.time() - start_time
                if response.status == 200:
                    status = "[O] ONLINE "
                    info = "OK"
                else:
                    status = "[?] UNKNOWN"
                    info = f"HTTP {response.status}"
                    
        except urllib.error.HTTPError as e:
            resp_latency = time.time() - start_time
            status = "[!] ERROR  "
            info = f"HTTP {e.code}: {e.reason}" 
            
        except Exception as e:
            status = "[X] OFFLINE"
            info = "Connection Failed"
            
        # Formatted to 2 decimal places with an 's'
        resp_str = f"{resp_latency:.2f}s" if resp_latency > 0 else "FAIL"
            
        print(f"{svc['name']:<20} | {status:<11} | {conn_str:<7} | {resp_str:<7} | {info[:20]}")

    print("=" * 80)

if __name__ == "__main__":
    check_services()
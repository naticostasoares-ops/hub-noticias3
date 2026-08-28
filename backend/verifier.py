import os
import json
import urllib.request
import urllib.error
import ssl
import datetime
import concurrent.futures

# Disable SSL verification for check
ssl_context = ssl._create_unverified_context()

def check_link(source_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # Try HEAD first
        req = urllib.request.Request(source_url, headers=headers, method='HEAD')
        with urllib.request.urlopen(req, context=ssl_context, timeout=8) as resp:
            if resp.status in [200, 301, 302, 307, 308]:
                return True
    except Exception:
        # Fallback to GET
        try:
            req = urllib.request.Request(source_url, headers=headers)
            with urllib.request.urlopen(req, context=ssl_context, timeout=8) as resp:
                if resp.status in [200, 301, 302, 307, 308]:
                    return True
        except urllib.error.HTTPError as e:
            # 403/401 may mean bot blocks but page still exists
            return e.code in [403, 401]
        except Exception:
            return False
    return False

def verify_all_links():
    db_path = "../frontend/database.json"
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado.", flush=True)
        return
        
    with open(db_path, "r", encoding="utf-8") as f:
        articles = json.load(f)
        
    print(f"Verificando integridade de links para {len(articles)} artigos...", flush=True)
    
    # Collect all unique sources to check
    links_to_check = []
    for art in articles:
        for src in art.get("sources", []):
            links_to_check.append(src["link"])
            
    # De-duplicate links to check
    unique_links = list(set(links_to_check))
    link_status = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_link, url): url for url in unique_links}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                is_up = future.result()
                link_status[url] = is_up
            except Exception:
                link_status[url] = False
                
    # Update articles state
    updated_count = 0
    for art in articles:
        valid = True
        for src in art.get("sources", []):
            url = src["link"]
            if not link_status.get(url, False):
                valid = False
                break
        
        art["link_valid"] = valid
        art["link_last_checked"] = datetime.datetime.utcnow().isoformat()
        updated_count += 1
        
    # Write back to database
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
        
    print(f"Verificação concluída! {updated_count} artigos atualizados.", flush=True)

if __name__ == "__main__":
    verify_all_links()

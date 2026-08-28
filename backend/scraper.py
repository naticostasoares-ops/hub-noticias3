import os
import re
import json
import ssl
import sys
import datetime
import urllib.request
import feedparser
from bs4 import BeautifulSoup
import google.generativeai as genai
from gtts import gTTS

# Disable SSL verification for scraper
ssl._create_default_https_context = ssl._create_unverified_context

SOURCES = [
    {"country": "Argentina", "name": "Clarín", "url": "https://www.clarin.com/", "nature": "grande imprensa", "feed": "https://www.clarin.com/rss/lo-ultimo/"},
    {"country": "Argentina", "name": "La Prensa", "url": "https://www.laprensa.com.ar/", "nature": "grande imprensa", "feed": "https://www.laprensa.com.ar/Suscripciones/Rss.ashx?Id=0"},
    {"country": "Argentina", "name": "La Nación", "url": "https://www.lanacion.com.ar/", "nature": "grande imprensa", "feed": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml"},
    {"country": "Argentina", "name": "Y Ahora Qué", "url": "https://yahoraque.com.ar/", "nature": "imprensa alternativa", "feed": "https://yahoraque.com.ar/feed/"},
    {"country": "Bolívia", "name": "La Época", "url": "https://www.la-epoca.com.bo/", "nature": "imprensa alternativa", "feed": "https://www.la-epoca.com.bo/feed/"},
    {"country": "Brasil", "name": "UOL", "url": "https://www.uol.com.br/", "nature": "grande imprensa", "feed": "https://noticias.uol.com.br/ultimas-noticias/index.xml"},
    {"country": "Brasil", "name": "Veja", "url": "https://veja.abril.com.br/", "nature": "grande imprensa", "feed": "https://veja.abril.com.br/feed"},
    {"country": "Brasil", "name": "Estadão", "url": "https://www.estadao.com.br/", "nature": "grande imprensa", "feed": "https://www.estadao.com.br/arc/outboundfeeds/rss/"},
    {"country": "Brasil", "name": "Valor Econômico", "url": "https://valor.globo.com/", "nature": "grande imprensa", "feed": "https://valor.globo.com/rss/valor/"},
    {"country": "Brasil", "name": "InfoMoney", "url": "https://www.infomoney.com.br/", "nature": "grande imprensa", "feed": "https://www.infomoney.com.br/feed/"},
    {"country": "Brasil", "name": "O Globo", "url": "https://oglobo.globo.com/", "nature": "grande imprensa", "feed": "https://oglobo.globo.com/rss.xml"},
    {"country": "Brasil", "name": "G1", "url": "https://g1.globo.com/", "nature": "grande imprensa", "feed": "https://g1.globo.com/dinamico/rss-atrelado/g1/mundo/rss.xml"},
    {"country": "Brasil", "name": "CNN Brasil", "url": "https://www.cnnbrasil.com.br/", "nature": "grande imprensa", "feed": "https://www.cnnbrasil.com.br/feed/"},
    {"country": "Brasil", "name": "DW Brasil", "url": "https://www.dw.com/pt-br/", "nature": "grande imprensa", "feed": "https://rss.dw.com/rdf/rss-br-all"},
    {"country": "Brasil", "name": "CartaCapital", "url": "https://www.cartacapital.com.br/", "nature": "imprensa alternativa", "feed": "https://www.cartacapital.com.br/feed/"},
    {"country": "Brasil", "name": "Brasil de Fato", "url": "https://www.brasildefato.com.br/", "nature": "imprensa alternativa", "feed": "https://www.brasildefato.com.br/rss2.xml"},
    {"country": "Brasil", "name": "ICL Notícias", "url": "https://iclnoticias.com.br/", "nature": "imprensa alternativa", "feed": "https://iclnoticias.com.br/feed/"},
    {"country": "Brasil", "name": "OPEU", "url": "https://www.opeu.org.br/", "nature": "publicação de análise", "feed": "https://www.opeu.org.br/feed/"},
    {"country": "Brasil", "name": "INEU", "url": "https://www.ineu.org.br/", "nature": "publicação de análise", "feed": "https://www.ineu.org.br/feed/"},
    {"country": "Brasil", "name": "Blog da Boitempo", "url": "https://blogdaboitempo.com.br/", "nature": "publicação de análise", "feed": "https://blogdaboitempo.com.br/feed/"},
    {"country": "Brasil", "name": "A Terra é Redonda", "url": "https://aterraeredonda.com.br/", "nature": "publicação de análise", "feed": "https://aterraeredonda.com.br/feed/"},
    {"country": "Brasil", "name": "Le Monde Diplomatique Brasil", "url": "https://diplomatique.org.br/", "nature": "publicação de análise", "feed": "https://diplomatique.org.br/feed/"},
    {"country": "Brasil", "name": "Portal do STF", "url": "https://portal.stf.jus.br/", "nature": "fonte oficial", "feed": "https://portal.stf.jus.br/noticias/rss.asp"},
    {"country": "Catar", "name": "Al Jazeera", "url": "https://www.aljazeera.com/", "nature": "grande imprensa", "feed": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"country": "China", "name": "People's Daily", "url": "https://en.people.cn/", "nature": "veículo estatal", "feed": "https://en.people.cn/rss/90777.xml"},
    {"country": "China", "name": "China Daily", "url": "https://www.chinadaily.com.cn/", "nature": "veículo estatal", "feed": "https://www.chinadaily.com.cn/rss/index.xml"},
    {"country": "China", "name": "China Economic Net", "url": "http://en.ce.cn/", "nature": "veículo estatal", "feed": None}, # Need manual scraping
    {"country": "China", "name": "China Military", "url": "http://eng.chinamil.com.cn/", "nature": "veículo estatal", "feed": "http://eng.chinamil.com.cn/rss.xml"},
    {"country": "Espanha", "name": "El País América", "url": "https://elpais.com/america/", "nature": "grande imprensa", "feed": "https://elpais.com/rss/america/portada.xml"},
    {"country": "Estados Unidos", "name": "Reuters", "url": "https://www.reuters.com/", "nature": "agência de notícias", "feed": None}, # Need manual scraping
    {"country": "Estados Unidos", "name": "Foreign Affairs", "url": "https://www.foreignaffairs.com/", "nature": "publicação de análise", "feed": "https://www.foreignaffairs.com/rss.xml"},
    {"country": "Estados Unidos", "name": "Casa Branca (Briefings)", "url": "https://www.whitehouse.gov/briefings-statements/", "nature": "fonte oficial", "feed": "https://www.whitehouse.gov/feed/"},
    {"country": "Estados Unidos", "name": "Comitê Judiciário da Câmara", "url": "https://judiciary.house.gov/", "nature": "fonte oficial", "feed": "https://judiciary.house.gov/rss.xml"},
    {"country": "Reino Unido", "name": "BBC", "url": "https://www.bbc.com/", "nature": "grande imprensa", "feed": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"country": "Reino Unido", "name": "The Sun", "url": "https://www.thesun.co.uk/", "nature": "tabloide", "feed": "https://www.thesun.co.uk/feed/"},
    {"country": "Venezuela", "name": "El Universal", "url": "https://www.eluniversal.com/", "nature": "grande imprensa", "feed": "https://www.eluniversal.com/rss/index.xml"},
    {"country": "Venezuela", "name": "El Nacional", "url": "https://www.elnacional.com/", "nature": "grande imprensa", "feed": "https://www.elnacional.com/feed/"}
]

def fetch_feed(source):
    url = source["feed"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print(f"Buscando feed RSS de {source['name']}...", flush=True)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            data = response.read()
            feed = feedparser.parse(data)
            articles = []
            for entry in feed.entries[:8]: # Limit to 8 most recent
                title = entry.get("title", "")
                link = entry.get("link", "")
                
                # Try parsing date
                pub_date = None
                date_fields = ["published_parsed", "updated_parsed", "created_parsed"]
                for field in date_fields:
                    if entry.get(field):
                        t = entry.get(field)
                        pub_date = datetime.datetime(*t[:6]).isoformat()
                        break
                
                if not pub_date and entry.get("published"):
                    # Basic string fallback
                    pub_date = entry.get("published")
                    
                desc = entry.get("summary", "") or entry.get("description", "")
                # Clean html tags from description
                desc = BeautifulSoup(desc, "html.parser").get_text() if desc else ""
                
                articles.append({
                    "title": title,
                    "link": link,
                    "published_at": pub_date or "",
                    "description": desc.strip(),
                    "source": source["name"],
                    "country": source["country"],
                    "nature": source["nature"]
                })
            return articles
    except Exception as e:
        print(f"Erro ao buscar feed de {source['name']}: {e}", flush=True)
        return []

def scrape_manual(source):
    print(f"Raspando home page manualmente para {source['name']}...", flush=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        req = urllib.request.Request(source["url"], headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read()
            soup = BeautifulSoup(html, "html.parser")
            articles = []
            
            # Custom simple scrapers for Reuters and China Economic Net
            if "reuters.com" in source["url"]:
                links = soup.find_all("a", href=True)
                seen_links = set()
                for a in links:
                    href = a["href"]
                    # Match news links e.g. /world/china/some-article-slug/
                    if ("/world/" in href or "/business/" in href) and len(href.split("/")) > 4:
                        full_link = href if href.startswith("http") else "https://www.reuters.com" + href
                        if full_link not in seen_links:
                            seen_links.add(full_link)
                            title = a.get_text().strip()
                            if len(title) > 20:
                                articles.append({
                                    "title": title,
                                    "link": full_link,
                                    "published_at": datetime.datetime.utcnow().isoformat(), # Fallback but mark it
                                    "description": "",
                                    "source": source["name"],
                                    "country": source["country"],
                                    "nature": source["nature"]
                                })
                            if len(articles) >= 8:
                                break
            elif "ce.cn" in source["url"]:
                links = soup.find_all("a", href=True)
                seen_links = set()
                for a in links:
                    href = a["href"]
                    if href.endswith(".shtml") and len(href.split("/")) > 3:
                        full_link = href if href.startswith("http") else "http://en.ce.cn" + href
                        if full_link not in seen_links:
                            seen_links.add(full_link)
                            title = a.get_text().strip()
                            if len(title) > 15:
                                articles.append({
                                    "title": title,
                                    "link": full_link,
                                    "published_at": "", # Leave empty if unknown
                                    "description": "",
                                    "source": source["name"],
                                    "country": source["country"],
                                    "nature": source["nature"]
                                })
                            if len(articles) >= 8:
                                break
            return articles
    except Exception as e:
        print(f"Erro ao raspar manualmente {source['name']}: {e}", flush=True)
        return []

def classify_and_summarize_batch(articles, api_key):
    if not api_key:
        print("Aviso: GEMINI_API_KEY não configurada. Usando fallback local sem IA.", flush=True)
        # Fallback processing if no API key
        processed = []
        for a in articles:
            processed.append({
                "title": a["title"],
                "sources": [{"name": a["source"], "country": a["country"], "nature": a["nature"], "link": a["link"]}],
                "published_at": a["published_at"],
                "type": "indefinido",
                "subject_primary": "Indefinido",
                "subjects_secondary": [],
                "relevance_brazil": 1,
                "relevance_intl": 1,
                "summary": f"Notícia de {a['source']}: {a['title']}. (Resumo automático indisponível sem chave de API)."
            })
        return processed

    print(f"Processando {len(articles)} artigos com o Gemini...", flush=True)
    genai.configure(api_key=api_key)
    
    # We send articles in batches to avoid token or rate limit issues
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = """
Você é um assistente especialista em curadoria de notícias de Relações Internacionais.
Sua tarefa é processar uma lista de artigos coletados. Para cada artigo, você deve:
1. Traduzir o título para o Português caso esteja em outro idioma.
2. Agrupar artigos idênticos/repetidos (que relatam o exato mesmo fato) em um único item, unificando suas fontes em uma lista de fontes.
3. Classificar o tipo de texto estritamente entre: "reportagem com apuração própria", "análise assinada", "artigo de opinião", "comunicado oficial" ou "indefinido" (NUNCA use "notícia factual").
4. Classificar a matéria usando a Taxonomia Rígida abaixo. Defina OBRIGATORIAMENTE 1 Categoria Principal (subject_primary) e, se necessário, até 2 secundárias (subjects_secondary).
   Siga estritamente a REGRA DE PRECEDÊNCIA:
   - Temas específicos (Esporte, Economia, Justiça, Saúde, Ciência e Tecnologia, Meio Ambiente, Trabalho, Cultura, Entretenimento e Mídia, Defesa e Segurança) SEMPRE têm prioridade absoluta sobre "Política" ou "Relações Internacionais".
   - Só rotule como "Política" ou "Relações Internacionais" se o fato central não se encaixar em nenhuma outra categoria temática específica.
   - O fato de o portal ser sobre Relações Internacionais NÃO autoriza rotular economia, esporte, tecnologia ou cultura como "política" ou "relações internacionais" (só rotule como política se houver intervenção governamental direta descrita no texto).
   - Se houver dúvida insolúvel na categoria principal, marque como "Indefinido".
   Taxonomia Rígida de categorias:
   - "Esporte"
   - "Economia"
   - "Justiça"
   - "Saúde"
   - "Ciência e Tecnologia"
   - "Meio Ambiente"
   - "Trabalho"
   - "Cultura"
   - "Entretenimento e Mídia"
   - "Política"
   - "Relações Internacionais"
   - "Defesa e Segurança"
   - "Indefinido"
5. Atribuir relevância para o Brasil (relevance_brazil) de 1 a 5, e relevância Internacional (relevance_intl) de 1 a 5.
6. Escrever um resumo curto em Português de exatamente 3 linhas, com suas próprias palavras, baseado no título e descrição fornecidos (nunca apenas no título).

Retorne os resultados em um JSON estruturado seguindo esta lista de objetos:
[
  {
    "title": "Título traduzido em português",
    "sources": [
      {"name": "Nome do veículo", "country": "País", "nature": "natureza do veículo", "link": "url original"}
    ],
    "published_at": "data original do artigo",
    "type": "tipo de texto",
    "subject_primary": "Categoria Principal",
    "subjects_secondary": ["Categoria secundária 1", "Categoria secundária 2"],
    "relevance_brazil": 3,
    "relevance_intl": 4,
    "summary": "Resumo em português contendo exatamente 3 linhas."
  }
]

Aqui está a lista de artigos a processar:
"""
    
    # Send all articles serialized as JSON inside the prompt
    articles_data = []
    for a in articles:
        articles_data.append({
            "title": a["title"],
            "description": a["description"],
            "source": a["source"],
            "country": a["country"],
            "nature": a["nature"],
            "link": a["link"],
            "published_at": a["published_at"]
        })
        
    full_prompt = prompt + "\n" + json.dumps(articles_data, ensure_ascii=False, indent=2)
    
    try:
        response = model.generate_content(full_prompt)
        # Parse JSON output from model response
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"Erro ao chamar API do Gemini ou processar JSON: {e}", flush=True)
        # Simple fallback
        return []

def generate_daily_audio(top_articles, output_path):
    print("Gerando roteiro de áudio para as 5 notícias mais importantes...", flush=True)
    if not top_articles:
        return
        
    script = "Olá. Aqui está o resumo das notícias mais importantes do dia. "
    for i, art in enumerate(top_articles[:5]):
        sources_str = ", e ".join([s["name"] for s in art["sources"]])
        script += f"Notícia {i+1}: {art['title']}. Publicada por {sources_str}. O resumo indica que: {art['summary']} "
        
    script += "Este foi o resumo diário de notícias de Relações Internacionais."
    
    try:
        # Save text summary script
        text_path = output_path.replace(".mp3", ".txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        # Generate MP3 using gTTS
        tts = gTTS(text=script, lang='pt', slow=False)
        tts.save(output_path)
        print(f"Resumo de áudio gerado com sucesso em {output_path}", flush=True)
    except Exception as e:
        print(f"Erro ao gerar áudio TTS: {e}", flush=True)

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 1. Fetch raw articles
    raw_articles = []
    for src in SOURCES:
        if src["feed"]:
            raw_articles.extend(fetch_feed(src))
        else:
            raw_articles.extend(scrape_manual(src))
            
    if not raw_articles:
        print("Nenhum artigo encontrado.", flush=True)
        return
        
    print(f"Total de {len(raw_articles)} artigos brutos coletados.", flush=True)
    
    # 2. Batch classify using Gemini (limit batches of max 15 articles to stay safe)
    batch_size = 15
    processed_articles = []
    for i in range(0, len(raw_articles), batch_size):
        batch = raw_articles[i:i+batch_size]
        processed_batch = classify_and_summarize_batch(batch, api_key)
        processed_articles.extend(processed_batch)
        
    # 3. Read existing database and merge
    db_path = "../frontend/database.json"
    existing_articles = []
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                existing_articles = json.load(f)
        except Exception as e:
            print(f"Erro ao ler banco de dados existente: {e}", flush=True)
            
    # Merge strategy: avoid duplicates based on original links
    existing_links = set()
    for art in existing_articles:
        for src in art.get("sources", []):
            existing_links.add(src["link"])
            
    new_merged = list(existing_articles)
    for art in processed_articles:
        # Check if this new article links are already present
        is_duplicate = False
        for src in art.get("sources", []):
            if src["link"] in existing_links:
                is_duplicate = True
                break
        if not is_duplicate:
            # Mark link validation state initially as up/active
            art["link_valid"] = True
            art["link_last_checked"] = datetime.datetime.utcnow().isoformat()
            new_merged.append(art)
            
    # Save updated database
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(new_merged, f, ensure_ascii=False, indent=2)
        
    # 4. Generate summary audio for the top 5 relevant articles in 'Hoje'
    # Calculate score = relevance_brazil + relevance_intl + (len(sources) - 1)
    def get_score(a):
        return a.get("relevance_brazil", 1) + a.get("relevance_intl", 1) + len(a.get("sources", [])) - 1
        
    sorted_top = sorted(processed_articles, key=get_score, reverse=True)
    audio_path = "../frontend/summary.mp3"
    generate_daily_audio(sorted_top, audio_path)

if __name__ == "__main__":
    main()

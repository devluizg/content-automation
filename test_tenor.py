# test_tenor.py

import requests
import os
from dotenv import load_dotenv

# Carrega o .env
load_dotenv()

def test_tenor_api():
    api_key = os.getenv("TENOR_API_KEY")
    
    # Verifica se a chave existe
    if not api_key:
        print("❌ ERRO: TENOR_API_KEY não encontrada no .env")
        return False
    
    print(f"🔑 API Key encontrada: {api_key[:10]}...")
    
    # Faz requisição de teste
    url = "https://tenor.googleapis.com/v2/search"
    params = {
        "q": "happy",
        "key": api_key,
        "limit": 3
    }
    
    try:
        print("📡 Fazendo requisição ao Tenor...")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            print(f"✅ SUCESSO! API funcionando!")
            print(f"📊 Stickers encontrados: {len(results)}")
            
            # Mostra os resultados
            for i, sticker in enumerate(results):
                title = sticker.get("content_description", "Sem título")
                url_gif = sticker["media_formats"]["gif"]["url"]
                print(f"\n   {i+1}. {title[:50]}")
                print(f"      URL: {url_gif[:60]}...")
            
            return True
        else:
            print(f"❌ ERRO: Status {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TESTE DA API TENOR")
    print("=" * 50)
    test_tenor_api()
    print("=" * 50)
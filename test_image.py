"""
Teste rápido do gerador de imagens
ATUALIZADO - Novo endpoint HuggingFace
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

# Verifica se a chave foi carregada
hf_token = os.getenv("HF_TOKEN", "")

print("\n" + "="*50)
print("TESTE DE CONFIGURAÇÃO")
print("="*50)

if hf_token:
    print(f"✓ HF_TOKEN encontrado: {hf_token[:15]}...")
else:
    print("✗ HF_TOKEN NÃO encontrado!")
    print("  Verifique seu arquivo .env")
    exit()

# Teste de geração
print("\n" + "="*50)
print("TESTE DE GERAÇÃO")
print("="*50 + "\n")

import requests
from PIL import Image
import io

# NOVO ENDPOINT!
model = "stabilityai/stable-diffusion-xl-base-1.0"
url = f"https://router.huggingface.co/hf-inference/models/{model}"

headers = {
    "Authorization": f"Bearer {hf_token}",
    "Content-Type": "application/json"
}

payload = {
    "inputs": "a cute robot painting a picture, cartoon style, colorful, pixar style",
    "parameters": {
        "width": 512,
        "height": 512,
    }
}

print("🎨 Gerando imagem de teste...")
print("   (pode demorar 30-60 segundos na primeira vez)\n")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=180)
    
    if response.status_code == 200:
        # Salva imagem
        Path("output/test").mkdir(parents=True, exist_ok=True)
        
        img = Image.open(io.BytesIO(response.content))
        img.save("output/test/teste_huggingface.png")
        
        print("✓ SUCESSO!")
        print(f"  Imagem salva em: output/test/teste_huggingface.png")
        print(f"  Tamanho: {img.size}")
        
    elif response.status_code == 503:
        print("⏳ Modelo carregando... tente novamente em 30 segundos")
        
    elif response.status_code == 401:
        print("✗ Token inválido! Verifique sua HF_TOKEN")
        
    else:
        print(f"✗ Erro: {response.status_code}")
        print(f"  {response.text[:300]}")
        
except Exception as e:
    print(f"✗ Erro: {e}")

print("\n" + "="*50)
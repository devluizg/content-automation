"""
Teste individual de cada chave Google
Gera 1 imagem com cada chave para verificar se funcionam
"""
import os
import requests
import base64
from pathlib import Path
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

# Carrega as chaves
keys = []
for i in range(1, 11):
    key = os.getenv(f"GOOGLE_API_KEY_{i}") or os.getenv(f"GEMINI_API_KEY_{i}")
    if key:
        keys.append((i, key))

# Se não encontrou numeradas, tenta a padrão
if not keys:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if key:
        keys.append((1, key))

print(f"\n{'='*60}")
print(f"🔑 TESTE INDIVIDUAL DE CHAVES GOOGLE")
print(f"{'='*60}")
print(f"Chaves encontradas: {len(keys)}")
print(f"{'='*60}\n")

if not keys:
    print("❌ Nenhuma chave encontrada no .env!")
    print("   Adicione: GOOGLE_API_KEY_1=sua_chave")
    exit(1)

# Cria pasta de saída
output_dir = Path("output/images/test_keys")
output_dir.mkdir(parents=True, exist_ok=True)

# Testa cada chave
results = []

for idx, (key_num, api_key) in enumerate(keys):
    print(f"\n{'='*50}")
    print(f"🔑 TESTANDO CHAVE {key_num}")
    print(f"   Key: {'*' * 20}...{api_key[-4:]}")
    print(f"{'='*50}")
    
    try:
        import google.generativeai as genai
        
        # Configura com esta chave específica
        genai.configure(api_key=api_key)
        
        # Prompt de teste único para cada chave
        prompts_test = [
            "a happy stick figure waving hello, white lines on black background, simple doodle",
            "a stick figure having an idea with lightbulb, white chalk on black, minimalist",
            "two stick figures talking, simple line drawing, white on black background",
        ]
        
        prompt = prompts_test[idx % len(prompts_test)]
        
        print(f"   Prompt: {prompt[:50]}...")
        print(f"   Gerando imagem...")
        
        # Tenta com Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content(
            f"Generate an image: {prompt}",
        )
        
        # Verifica resposta
        image_found = False
        
        if response and hasattr(response, 'candidates'):
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Encontrou imagem!
                            image_data = base64.b64decode(part.inline_data.data)
                            image = Image.open(io.BytesIO(image_data))
                            
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            
                            # Salva
                            save_path = output_dir / f"chave_{key_num}_teste.png"
                            image.save(save_path)
                            
                            print(f"\n   ✅ SUCESSO!")
                            print(f"   📁 Salvo: {save_path}")
                            print(f"   📐 Tamanho: {image.size}")
                            
                            results.append({
                                "chave": key_num,
                                "status": "✅ OK",
                                "arquivo": str(save_path)
                            })
                            image_found = True
                            break
                if image_found:
                    break
        
        if not image_found:
            # Gemini não retornou imagem, tenta texto como fallback
            if response and response.text:
                print(f"\n   ⚠️ Gemini respondeu texto, não imagem")
                print(f"   Resposta: {response.text[:100]}...")
            
            # Tenta Imagen REST API
            print(f"\n   🔄 Tentando Imagen REST API...")
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
            
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "1:1",
                }
            }
            
            resp = requests.post(url, json=payload, timeout=60)
            
            if resp.status_code == 200:
                data = resp.json()
                if "predictions" in data and data["predictions"]:
                    img_b64 = data["predictions"][0].get("bytesBase64Encoded")
                    if img_b64:
                        image_data = base64.b64decode(img_b64)
                        image = Image.open(io.BytesIO(image_data))
                        
                        save_path = output_dir / f"chave_{key_num}_imagen.png"
                        image.save(save_path)
                        
                        print(f"\n   ✅ SUCESSO (Imagen API)!")
                        print(f"   📁 Salvo: {save_path}")
                        
                        results.append({
                            "chave": key_num,
                            "status": "✅ OK (Imagen)",
                            "arquivo": str(save_path)
                        })
                        image_found = True
            
            if not image_found:
                print(f"\n   ❌ Não conseguiu gerar imagem")
                print(f"   Status: {resp.status_code if 'resp' in dir() else 'N/A'}")
                results.append({
                    "chave": key_num,
                    "status": "❌ Falhou",
                    "arquivo": None
                })
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n   ❌ ERRO: {error_msg[:100]}")
        
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            status = "⚠️ Limite atingido"
        elif "invalid" in error_msg.lower() or "api" in error_msg.lower():
            status = "❌ Chave inválida"
        elif "permission" in error_msg.lower():
            status = "❌ Sem permissão"
        else:
            status = f"❌ Erro: {error_msg[:30]}"
        
        results.append({
            "chave": key_num,
            "status": status,
            "arquivo": None
        })

# Resumo final
print(f"\n\n{'='*60}")
print(f"📊 RESUMO DO TESTE")
print(f"{'='*60}")

ok_count = 0
for r in results:
    print(f"\n   Chave {r['chave']}: {r['status']}")
    if r['arquivo']:
        print(f"            📁 {r['arquivo']}")
        ok_count += 1

print(f"\n{'='*60}")
print(f"✅ Chaves funcionando: {ok_count}/{len(results)}")
print(f"📁 Imagens salvas em: {output_dir}")
print(f"{'='*60}\n")

if ok_count > 0:
    print(f"🎉 Você tem ~{ok_count * 25} imagens/dia com Google!")
    print(f"   + Pollinations ilimitado como fallback")
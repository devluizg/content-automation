"""
Gerador de imagens usando Pollinations.ai
100% GRATUITO - Otimizado para STICKMAN
VERSÃO CORRIGIDA - Melhor tratamento de erros
"""
import requests
from pathlib import Path
from PIL import Image
import io
import time
import urllib.parse
import sys
import random
import hashlib

sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.watermark_remover import WatermarkRemover
    from utils.image_resizer import ImageResizer, SIZES
except ImportError:
    SIZES = {
        "short": {"width": 1080, "height": 1920},
        "youtube": {"width": 1920, "height": 1080},
        "square": {"width": 1080, "height": 1080},
    }
    
    class WatermarkRemover:
        def remove_by_crop(self, path, crop_bottom=80):
            img = Image.open(path)
            w, h = img.size
            img = img.crop((0, 0, w, h - crop_bottom))
            img.save(path)
    
    class ImageResizer:
        def resize(self, path, format="short", method="cover"):
            if format in SIZES:
                img = Image.open(path)
                img = img.resize((SIZES[format]["width"], SIZES[format]["height"]), Image.LANCZOS)
                img.save(path)


# ============================================
# ESTILOS STICKMAN OTIMIZADOS
# ============================================

STYLES = {
    "stickman": (
        "simple white stick figure on pure black background, "
        "minimalist line drawing, extremely simple stick people with circle heads, "
        "thin white lines only, no shading, no gradients, no details, "
        "basic stick body with straight lines for arms and legs, "
        "hand-drawn doodle style, black void background, clean simple illustration"
    ),
    "stickman_cute": (
        "cute simple white stick figure on solid black background, "
        "round circle head with simple dot eyes and curved smile, "
        "thin white lines, stick body, adorable simple expression, "
        "minimalist kawaii doodle, pure black background, white outlines only"
    ),
    "stickman_comic": (
        "stick figure comic style, white lines on black background, "
        "expressive simple characters, minimal line art, xkcd webcomic style"
    ),
    "stickman_chat": (
        "two white stick figures having conversation on black background, "
        "simple circle heads with basic expressions, thin white lines"
    ),
    "stickman_action": (
        "white stick figure in action pose on black background, "
        "dynamic movement, motion lines, simple white lines, circle head"
    ),
    "stickman_thinking": (
        "white stick figure thinking on black background, "
        "thought bubble or lightbulb above head, simple white lines"
    ),
    "stickman_confused": (
        "confused white stick figure on black background, "
        "question marks around head, simple expression, white lines only"
    ),
    "stickman_happy": (
        "happy white stick figure celebrating on black background, "
        "arms raised in joy, big smile, simple white lines"
    ),
    "whiteboard": (
        "simple black stick figure on white background, "
        "marker drawing style, hand-drawn doodle, thin black lines"
    ),
    "chalkboard": (
        "white chalk stick figure on dark green chalkboard, "
        "chalk texture, hand-drawn classroom style"
    ),
    "notebook": (
        "blue pen stick figure on lined notebook paper, "
        "casual doodle, margin drawing style"
    ),
    "cartoon": "cartoon style, colorful, pixar style, vibrant",
    "anime": "anime style, japanese animation, vibrant colors",
    "sketch": "pencil sketch, black and white, detailed linework",
    "flat": "flat design, minimal, vector art, clean lines",
    "neon": "neon glow, bright colors on dark background, cyberpunk",
}

STICKMAN_ACTIONS = [
    "standing", "walking", "talking", "pointing", "thinking",
    "sitting", "running", "waving", "celebrating", "confused",
    "happy", "sad", "excited", "surprised", "explaining"
]


class ImageGenerator:
    """Gerador de imagens Pollinations.ai - 100% Gratuito"""
    
    def __init__(self, style: str = "stickman", remove_watermark: bool = True, 
                 auto_resize: bool = True, crop_bottom: int = 80):
        
        self.base_url = "https://image.pollinations.ai/prompt/"
        self.style_name = style if style in STYLES else "stickman"
        self.style = STYLES[self.style_name]
        self.remove_watermark = remove_watermark
        self.auto_resize = auto_resize
        self.crop_bottom = crop_bottom
        
        self.watermark_remover = WatermarkRemover() if remove_watermark else None
        self.resizer = ImageResizer() if auto_resize else None
        
        self.used_prompts = set()
        self.counter = 0
        
        print(f"\n{'='*50}")
        print(f"🎨 STICKMAN GENERATOR (Pollinations.ai)")
        print(f"{'='*50}")
        print(f"✓ 100% Gratuito")
        print(f"✓ Estilo: {self.style_name}")
        print(f"{'='*50}\n")
    
    def _seed(self) -> int:
        self.counter += 1
        return int(hashlib.md5(f"{time.time()}_{self.counter}_{random.random()}".encode()).hexdigest()[:8], 16)
    
    def _detect_context(self, prompt: str) -> str:
        """Detecta o contexto do prompt"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["talk", "chat", "convers", "friend", "discuss"]):
            return "talking"
        elif any(word in prompt_lower for word in ["think", "idea", "lightbulb", "ponder"]):
            return "thinking"
        elif any(word in prompt_lower for word in ["confus", "puzzle", "lost", "question"]):
            return "confused"
        elif any(word in prompt_lower for word in ["happy", "celebrat", "joy", "excit", "win"]):
            return "happy"
        elif any(word in prompt_lower for word in ["sad", "disappoint", "cry", "upset"]):
            return "sad"
        elif any(word in prompt_lower for word in ["work", "computer", "desk", "office"]):
            return "working"
        elif any(word in prompt_lower for word in ["present", "explain", "teach", "show"]):
            return "presenting"
        elif any(word in prompt_lower for word in ["run", "jump", "danc", "move"]):
            return "action"
        
        return "talking"
    
    def _enhance_prompt(self, prompt: str) -> str:
        """Otimiza prompt para stickman"""
        
        # Remove palavras problemáticas
        remove_words = [
            "realistic", "photorealistic", "detailed", "complex", 
            "photograph", "photo", "real", "human", "person",
            "high quality", "4k", "hd", "ultra", "beautiful"
        ]
        
        clean = prompt.lower()
        for word in remove_words:
            clean = clean.replace(word, "")
        
        # Garante que menciona stick figure
        if "stick figure" not in clean:
            clean = f"stick figure {clean}"
        
        # Adiciona estilo
        enhanced = f"{clean.strip()}, {self.style}"
        
        return enhanced
    
    def _ensure_unique(self, prompt: str) -> str:
        """Garante prompt único"""
        for i in range(20):
            unique = f"{prompt}, variation {random.randint(1000, 9999)}"
            if unique not in self.used_prompts:
                self.used_prompts.add(unique)
                return unique
        return f"{prompt}, unique {random.randint(10000, 99999)}"
    
    def generate(self, prompt: str, format: str = "short", width: int = None, 
                 height: int = None, save_path: str = None) -> str:
        """Gera uma imagem stickman"""
        
        # Dimensões
        if not width or not height:
            size = SIZES.get(format, SIZES["short"])
            width, height = size["width"], size["height"]
        
        # Gera maior para compensar crop
        gen_h = height + self.crop_bottom + 50 if self.remove_watermark else height
        
        # Prepara prompt
        enhanced = self._enhance_prompt(prompt)
        unique_prompt = self._ensure_unique(enhanced)
        
        # Parâmetros
        seed = self._seed()
        nonce = int(time.time() * 1000)
        
        # Codifica URL
        encoded = urllib.parse.quote(unique_prompt)
        url = f"{self.base_url}{encoded}?width={width}&height={gen_h}&seed={seed}&nologo=true&nonce={nonce}"
        
        print(f"\n🎨 Gerando stickman: {prompt[:50]}...")
        print(f"   URL: {url[:80]}...")
        
        # Headers
        headers = {
            'Accept': 'image/png,image/jpeg,image/*',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'
        }
        
        for attempt in range(3):
            try:
                print(f"   Tentativa {attempt + 1}/3...")
                
                # Faz requisição
                resp = requests.get(url, timeout=120, headers=headers)
                
                print(f"   Status: {resp.status_code}")
                print(f"   Content-Type: {resp.headers.get('content-type', 'N/A')}")
                print(f"   Content-Length: {len(resp.content)} bytes")
                
                # Verifica status
                if resp.status_code != 200:
                    print(f"   ❌ Status não é 200")
                    time.sleep(5)
                    continue
                
                # Verifica content-type
                content_type = resp.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    print(f"   ❌ Resposta não é imagem: {content_type}")
                    print(f"   Conteúdo: {resp.text[:200]}...")
                    time.sleep(5)
                    continue
                
                # Verifica tamanho mínimo (imagens válidas têm mais de 1KB)
                if len(resp.content) < 1000:
                    print(f"   ❌ Resposta muito pequena: {len(resp.content)} bytes")
                    time.sleep(5)
                    continue
                
                # Tenta abrir como imagem
                try:
                    img = Image.open(io.BytesIO(resp.content))
                    print(f"   ✓ Imagem válida: {img.size}, modo: {img.mode}")
                except Exception as img_err:
                    print(f"   ❌ Erro ao abrir imagem: {img_err}")
                    time.sleep(5)
                    continue
                
                # Converte para RGB se necessário
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Salva se tiver caminho
                if save_path:
                    # Garante que tem extensão .png
                    save_path = str(save_path)
                    if not save_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        save_path = save_path + '.png'
                    
                    # Cria diretório
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                    
                    # Salva imagem original
                    img.save(save_path, 'PNG')
                    print(f"   ✓ Salvo: {save_path}")
                    
                    # Remove watermark (crop inferior)
                    if self.remove_watermark and self.watermark_remover:
                        try:
                            self.watermark_remover.remove_by_crop(save_path, self.crop_bottom)
                            print(f"   ✓ Watermark removido")
                        except Exception as e:
                            print(f"   ⚠️ Erro ao remover watermark: {e}")
                    
                    # Redimensiona para tamanho final
                    try:
                        img_final = Image.open(save_path)
                        if img_final.size != (width, height):
                            img_final = img_final.resize((width, height), Image.LANCZOS)
                            img_final.save(save_path, 'PNG')
                            print(f"   ✓ Redimensionado: {width}x{height}")
                    except Exception as e:
                        print(f"   ⚠️ Erro ao redimensionar: {e}")
                    
                    print(f"   ✅ Sucesso!")
                    return save_path
                
                return img
                
            except requests.exceptions.Timeout:
                print(f"   ⚠️ Timeout na tentativa {attempt + 1}")
                time.sleep(5)
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ Erro de requisição: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"   ⚠️ Erro: {type(e).__name__}: {e}")
                time.sleep(5)
        
        print(f"   ❌ Falhou após 3 tentativas")
        return None
    
    def generate_batch(self, prompts: list, output_dir: str, format: str = "short", 
                       delay: float = 3.0) -> list:
        """Gera múltiplas imagens"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.used_prompts.clear()
        
        size = SIZES.get(format, SIZES["short"])
        
        print(f"\n{'='*50}")
        print(f"🎨 GERANDO {len(prompts)} STICKMAN")
        print(f"{'='*50}")
        print(f"📁 Saída: {output_dir}")
        print(f"📐 Formato: {format} ({size['width']}x{size['height']})")
        print(f"🎭 Estilo: {self.style_name}")
        print(f"{'='*50}")
        
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"\n[{i+1}/{len(prompts)}] {prompt[:45]}...")
            
            # Garante extensão .png no save_path
            save_path = output_dir / f"image_{i+1:02d}.png"
            
            result = self.generate(
                prompt=prompt, 
                format=format, 
                save_path=str(save_path)
            )
            
            if result:
                results.append(str(save_path))
            
            # Delay entre imagens
            if i < len(prompts) - 1:
                wait = delay + random.uniform(1, 3)
                print(f"   ⏳ Aguardando {wait:.1f}s...")
                time.sleep(wait)
        
        print(f"\n{'='*50}")
        print(f"✅ {len(results)}/{len(prompts)} imagens geradas!")
        print(f"📁 Pasta: {output_dir}")
        print(f"{'='*50}\n")
        
        return results
    
    def set_style(self, style: str):
        if style in STYLES:
            self.style_name = style
            self.style = STYLES[style]
            print(f"✓ Estilo: {style}")
        else:
            print(f"❌ Estilo não encontrado")
    
    def list_styles(self):
        print("\n🎨 ESTILOS:")
        for name in STYLES:
            marker = " ◄" if name == self.style_name else ""
            print(f"   {name:20}{marker}")


# ============================================
# TESTE
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTE: Stickman Generator (Pollinations)")
    print("="*60)
    
    gen = ImageGenerator(style="stickman")
    gen.list_styles()
    
    # Teste com um prompt simples
    prompts = [
        "two friends talking",
        "person with idea lightbulb",
        "confused at computer",
    ]
    
    results = gen.generate_batch(
        prompts=prompts,
        output_dir="output/images/test_stickman",
        format="short",
        delay=4.0
    )
    
    if results:
        print(f"\n🎉 {len(results)} stickman gerados!")
        print(f"📁 Verifique: output/images/test_stickman/")
    else:
        print("\n❌ Nenhuma imagem gerada")
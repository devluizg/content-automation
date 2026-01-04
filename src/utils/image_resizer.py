"""
Redimensionador de Imagens
Garante que todas as imagens fiquem no tamanho correto para cada plataforma
"""
from PIL import Image
from pathlib import Path


# ============================================
# TAMANHOS PADRÃO DAS PLATAFORMAS
# ============================================

SIZES = {
    # Vídeos Verticais (9:16)
    "short": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": 9/16,
        "description": "YouTube Shorts, TikTok, Reels"
    },
    "reels": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": 9/16,
        "description": "Instagram Reels"
    },
    "tiktok": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": 9/16,
        "description": "TikTok"
    },
    "story": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": 9/16,
        "description": "Instagram/Facebook Stories"
    },
    
    # Vídeos Horizontais (16:9)
    "youtube": {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": 16/9,
        "description": "YouTube vídeo longo horizontal"
    },
    "youtube_hd": {
        "width": 1280,
        "height": 720,
        "aspect_ratio": 16/9,
        "description": "YouTube HD 720p"
    },
    "youtube_4k": {
        "width": 3840,
        "height": 2160,
        "aspect_ratio": 16/9,
        "description": "YouTube 4K"
    },
    "thumbnail": {
        "width": 1280,
        "height": 720,
        "aspect_ratio": 16/9,
        "description": "Thumbnail YouTube"
    },
    
    # Quadrado (1:1)
    "square": {
        "width": 1080,
        "height": 1080,
        "aspect_ratio": 1/1,
        "description": "Instagram Feed, Facebook"
    },
    
    # Outros
    "pinterest": {
        "width": 1000,
        "height": 1500,
        "aspect_ratio": 2/3,
        "description": "Pinterest Pin"
    },
    "twitter": {
        "width": 1200,
        "height": 675,
        "aspect_ratio": 16/9,
        "description": "Twitter/X Post"
    },
    "linkedin": {
        "width": 1200,
        "height": 627,
        "aspect_ratio": 1.91/1,
        "description": "LinkedIn Post"
    }
}


class ImageResizer:
    """Redimensiona imagens para tamanhos específicos de plataformas"""
    
    def __init__(self):
        self.sizes = SIZES
    
    def get_size(self, format: str) -> tuple:
        """
        Retorna (largura, altura) para um formato
        
        Args:
            format: Nome do formato (short, youtube, square, etc)
        """
        if format not in self.sizes:
            raise ValueError(f"Formato '{format}' não existe. Use: {list(self.sizes.keys())}")
        
        size = self.sizes[format]
        return (size["width"], size["height"])
    
    def resize(self,
               image_path: str,
               output_path: str = None,
               format: str = "short",
               method: str = "cover",
               background_color: tuple = (0, 0, 0)) -> str:
        """
        Redimensiona uma imagem para o tamanho da plataforma
        
        Args:
            image_path: Caminho da imagem original
            output_path: Caminho de saída (se None, sobrescreve)
            format: Formato alvo (short, youtube, square, etc)
            method: Método de redimensionamento:
                    - "cover": Preenche todo o espaço (pode cortar)
                    - "contain": Mantém toda a imagem (pode ter barras)
                    - "stretch": Estica para caber (pode distorcer)
                    - "fill": Preenche com cor de fundo
            background_color: Cor RGB para fundo (usado em contain/fill)
            
        Returns:
            Caminho da imagem redimensionada
        """
        target_width, target_height = self.get_size(format)
        
        img = Image.open(image_path)
        original_width, original_height = img.size
        
        # Converter para RGB se necessário
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        if method == "cover":
            result = self._resize_cover(img, target_width, target_height)
        elif method == "contain":
            result = self._resize_contain(img, target_width, target_height, background_color)
        elif method == "stretch":
            result = self._resize_stretch(img, target_width, target_height)
        elif method == "fill":
            result = self._resize_fill(img, target_width, target_height, background_color)
        else:
            result = self._resize_cover(img, target_width, target_height)
        
        output_path = output_path or image_path
        result.save(output_path, quality=95)
        
        return output_path
    
    def _resize_cover(self, img: Image, target_w: int, target_h: int) -> Image:
        """
        COVER: Preenche todo o espaço, cortando se necessário
        (Melhor para vídeos - sem barras pretas)
        """
        img_w, img_h = img.size
        
        # Calcula proporções
        ratio_w = target_w / img_w
        ratio_h = target_h / img_h
        
        # Usa a maior proporção para cobrir tudo
        ratio = max(ratio_w, ratio_h)
        
        # Novo tamanho
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        # Redimensiona
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Corta o centro
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        right = left + target_w
        bottom = top + target_h
        
        return img.crop((left, top, right, bottom))
    
    def _resize_contain(self, img: Image, target_w: int, target_h: int, bg_color: tuple) -> Image:
        """
        CONTAIN: Mantém toda a imagem, adiciona barras se necessário
        """
        img_w, img_h = img.size
        
        # Calcula proporções
        ratio_w = target_w / img_w
        ratio_h = target_h / img_h
        
        # Usa a menor proporção para caber tudo
        ratio = min(ratio_w, ratio_h)
        
        # Novo tamanho
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        # Redimensiona
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Cria fundo
        result = Image.new('RGB', (target_w, target_h), bg_color)
        
        # Centraliza imagem
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        result.paste(img, (x, y))
        
        return result
    
    def _resize_stretch(self, img: Image, target_w: int, target_h: int) -> Image:
        """
        STRETCH: Estica para caber exatamente (pode distorcer)
        """
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    def _resize_fill(self, img: Image, target_w: int, target_h: int, bg_color: tuple) -> Image:
        """
        FILL: Preenche com blur da própria imagem como fundo
        (Efeito estilo TikTok/Reels)
        """
        from PIL import ImageFilter
        
        # Cria fundo com a imagem borrada e escurecida
        bg = img.copy()
        bg = self._resize_cover(bg, target_w, target_h)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        
        # Escurece o fundo
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.4)
        
        # Redimensiona imagem principal para caber
        img_w, img_h = img.size
        ratio = min(target_w / img_w, target_h / img_h) * 0.9  # 90% do tamanho
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Centraliza sobre o fundo
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        bg.paste(img, (x, y))
        
        return bg
    
    def resize_batch(self,
                     image_paths: list,
                     format: str = "short",
                     method: str = "cover") -> list:
        """
        Redimensiona múltiplas imagens
        
        Args:
            image_paths: Lista de caminhos
            format: Formato alvo
            method: Método de redimensionamento
            
        Returns:
            Lista de caminhos processados
        """
        processed = []
        
        for img_path in image_paths:
            try:
                self.resize(img_path, format=format, method=method)
                processed.append(img_path)
                print(f"✅ Redimensionado: {Path(img_path).name}")
            except Exception as e:
                print(f"❌ Erro em {img_path}: {e}")
                processed.append(img_path)
        
        return processed
    
    def check_size(self, image_path: str, format: str) -> dict:
        """
        Verifica se a imagem está no tamanho correto
        
        Returns:
            Dict com informações sobre a imagem
        """
        img = Image.open(image_path)
        current_w, current_h = img.size
        target_w, target_h = self.get_size(format)
        
        is_correct = (current_w == target_w and current_h == target_h)
        
        return {
            "path": image_path,
            "current_size": (current_w, current_h),
            "target_size": (target_w, target_h),
            "format": format,
            "is_correct": is_correct,
            "needs_resize": not is_correct
        }
    
    def list_formats(self):
        """Lista todos os formatos disponíveis"""
        print("\n📐 FORMATOS DISPONÍVEIS:\n")
        print(f"{'Formato':<15} {'Tamanho':<15} {'Descrição'}")
        print("-" * 60)
        
        for name, info in self.sizes.items():
            size_str = f"{info['width']}x{info['height']}"
            print(f"{name:<15} {size_str:<15} {info['description']}")


# ============================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================

def resize_for_short(image_path: str, output_path: str = None) -> str:
    """Redimensiona para YouTube Shorts/TikTok/Reels (1080x1920)"""
    resizer = ImageResizer()
    return resizer.resize(image_path, output_path, format="short", method="cover")


def resize_for_youtube(image_path: str, output_path: str = None) -> str:
    """Redimensiona para YouTube horizontal (1920x1080)"""
    resizer = ImageResizer()
    return resizer.resize(image_path, output_path, format="youtube", method="cover")


def resize_for_square(image_path: str, output_path: str = None) -> str:
    """Redimensiona para formato quadrado (1080x1080)"""
    resizer = ImageResizer()
    return resizer.resize(image_path, output_path, format="square", method="cover")


def resize_for_thumbnail(image_path: str, output_path: str = None) -> str:
    """Redimensiona para thumbnail do YouTube (1280x720)"""
    resizer = ImageResizer()
    return resizer.resize(image_path, output_path, format="thumbnail", method="cover")


# ============================================
# TESTE
# ============================================

if __name__ == "__main__":
    resizer = ImageResizer()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║          REDIMENSIONADOR DE IMAGENS                       ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Métodos disponíveis:                                     ║
║  • cover   - Preenche tudo (pode cortar) ⭐ Recomendado   ║
║  • contain - Mantém tudo (pode ter barras)                ║
║  • stretch - Estica (pode distorcer)                      ║
║  • fill    - Fundo blur estilo TikTok                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Lista formatos
    resizer.list_formats()
    
    # Testa se existe imagem
    test_image = "output/images/teste.png"
    
    if Path(test_image).exists():
        print(f"\n🧪 Testando com: {test_image}\n")
        
        # Verifica tamanho atual
        info = resizer.check_size(test_image, "short")
        print(f"Tamanho atual: {info['current_size']}")
        print(f"Tamanho alvo: {info['target_size']}")
        print(f"Precisa redimensionar: {info['needs_resize']}")
        
        # Testa diferentes métodos
        from shutil import copy
        
        methods = ["cover", "contain", "fill"]
        
        for method in methods:
            output = f"output/images/teste_resize_{method}.png"
            copy(test_image, output)
            resizer.resize(output, format="short", method=method)
            print(f"✅ Gerado: teste_resize_{method}.png")
        
        print("\n📁 Verifique as imagens em output/images/")
    else:
        print(f"\n⚠️ Imagem de teste não encontrada: {test_image}")
        print("Execute primeiro: python src/generators/image_generator.py")

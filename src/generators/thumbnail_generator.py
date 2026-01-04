"""
Gerador de Thumbnails com IA
Cria thumbnails atraentes para vídeos do YouTube
v1.0
"""
import os
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import textwrap
import random

# Configurações
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720


class ThumbnailGenerator:
    """
    Gera thumbnails atraentes para YouTube
    - Usa IA para gerar imagem de fundo (opcional)
    - Cria thumbnails estilizadas com texto
    - Otimizado para 1280x720 (padrão YouTube)
    """
    
    def __init__(self, output_dir: str = "output/thumbnails"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.width = THUMBNAIL_WIDTH
        self.height = THUMBNAIL_HEIGHT
        
        # Tenta carregar API keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.stability_key = os.getenv("STABILITY_API_KEY")
        
        # Encontra fontes
        self.font_bold = self._find_font("bold")
        self.font_regular = self._find_font("regular")
        
        # Estilos de thumbnail
        self.styles = {
            "gradient_fire": {
                "colors": [(255, 94, 58), (255, 149, 0)],
                "text_color": (255, 255, 255),
                "shadow": True
            },
            "gradient_ocean": {
                "colors": [(0, 212, 255), (9, 9, 121)],
                "text_color": (255, 255, 255),
                "shadow": True
            },
            "gradient_purple": {
                "colors": [(131, 58, 180), (253, 29, 29)],
                "text_color": (255, 255, 255),
                "shadow": True
            },
            "gradient_green": {
                "colors": [(46, 204, 113), (39, 174, 96)],
                "text_color": (255, 255, 255),
                "shadow": True
            },
            "gradient_gold": {
                "colors": [(255, 215, 0), (255, 165, 0)],
                "text_color": (0, 0, 0),
                "shadow": False
            },
            "dark_dramatic": {
                "colors": [(20, 20, 20), (60, 60, 60)],
                "text_color": (255, 255, 255),
                "shadow": True,
                "glow": (255, 215, 0)
            },
            "neon_pink": {
                "colors": [(25, 25, 35), (45, 45, 65)],
                "text_color": (255, 0, 128),
                "shadow": True,
                "glow": (255, 0, 128)
            },
            "clean_white": {
                "colors": [(255, 255, 255), (240, 240, 240)],
                "text_color": (30, 30, 30),
                "shadow": False,
                "border": (255, 94, 58)
            }
        }
        
        print(f"✓ ThumbnailGenerator inicializado")
        print(f"  Diretório: {self.output_dir}")
    
    def _find_font(self, style: str = "bold") -> str:
        """Encontra fonte no sistema"""
        
        if style == "bold":
            paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/impact.ttf",
            ]
        else:
            paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        
        for p in paths:
            if Path(p).exists():
                return p
        
        return None
    
    def _create_gradient(self, color1: tuple, color2: tuple, 
                         direction: str = "vertical") -> Image.Image:
        """Cria imagem com gradiente"""
        
        img = Image.new('RGB', (self.width, self.height), color1)
        draw = ImageDraw.Draw(img)
        
        if direction == "vertical":
            for y in range(self.height):
                ratio = y / self.height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        elif direction == "horizontal":
            for x in range(self.width):
                ratio = x / self.width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.line([(x, 0), (x, self.height)], fill=(r, g, b))
        
        elif direction == "diagonal":
            for y in range(self.height):
                for x in range(self.width):
                    ratio = (x + y) / (self.width + self.height)
                    r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                    g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                    b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                    draw.point((x, y), fill=(r, g, b))
        
        return img
    
    def _add_text_with_shadow(self, img: Image.Image, text: str, 
                              position: tuple, font: ImageFont.FreeTypeFont,
                              text_color: tuple, shadow: bool = True,
                              shadow_color: tuple = (0, 0, 0),
                              shadow_offset: int = 4) -> Image.Image:
        """Adiciona texto com sombra"""
        
        draw = ImageDraw.Draw(img)
        x, y = position
        
        if shadow:
            # Sombra
            for offset in range(1, shadow_offset + 1):
                alpha = int(150 * (1 - offset / shadow_offset))
                shadow_fill = (*shadow_color[:3], alpha) if len(shadow_color) == 3 else shadow_color
                draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
        
        # Texto principal
        draw.text(position, text, font=font, fill=text_color)
        
        return img
    
    def _add_glow_effect(self, img: Image.Image, text: str,
                         position: tuple, font: ImageFont.FreeTypeFont,
                         glow_color: tuple, intensity: int = 10) -> Image.Image:
        """Adiciona efeito de glow no texto"""
        
        # Cria camada de glow
        glow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        
        x, y = position
        
        # Desenha múltiplas camadas para criar glow
        for i in range(intensity, 0, -2):
            alpha = int(30 * (1 - i / intensity))
            glow_draw.text((x - i, y), text, font=font, fill=(*glow_color, alpha))
            glow_draw.text((x + i, y), text, font=font, fill=(*glow_color, alpha))
            glow_draw.text((x, y - i), text, font=font, fill=(*glow_color, alpha))
            glow_draw.text((x, y + i), text, font=font, fill=(*glow_color, alpha))
        
        # Blur no glow
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=5))
        
        # Combina com imagem original
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        img = Image.alpha_composite(img, glow_layer)
        
        return img
    
    def _wrap_text(self, text: str, max_chars: int = 25) -> list:
        """Quebra texto em linhas"""
        
        # Remove emojis e caracteres especiais para cálculo de largura
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if len(test_line) <= max_chars:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines[:3]  # Máximo 3 linhas
    
    def _get_optimal_font_size(self, text: str, max_width: int, 
                               max_height: int) -> int:
        """Calcula tamanho ideal da fonte"""
        
        if not self.font_bold:
            return 60
        
        lines = self._wrap_text(text, max_chars=20)
        num_lines = len(lines)
        
        # Começa grande e reduz até caber
        for size in range(120, 30, -5):
            try:
                font = ImageFont.truetype(self.font_bold, size)
                
                # Calcula altura total
                total_height = size * num_lines * 1.2
                
                # Calcula largura máxima
                max_line_width = 0
                for line in lines:
                    bbox = font.getbbox(line)
                    line_width = bbox[2] - bbox[0]
                    max_line_width = max(max_line_width, line_width)
                
                if max_line_width <= max_width and total_height <= max_height:
                    return size
                    
            except:
                continue
        
        return 40
    
    def _add_emoji_decoration(self, img: Image.Image, 
                              emojis: list, positions: str = "corners") -> Image.Image:
        """Adiciona emojis decorativos (como imagens de placeholder)"""
        
        # Por enquanto, adiciona círculos coloridos como placeholder
        # Em produção, você pode usar imagens de emoji reais
        
        draw = ImageDraw.Draw(img)
        
        emoji_colors = [
            (255, 94, 58),   # Vermelho
            (255, 215, 0),   # Dourado
            (0, 212, 255),   # Azul
            (46, 204, 113),  # Verde
        ]
        
        if positions == "corners":
            coords = [
                (50, 50),                           # Top-left
                (self.width - 80, 50),              # Top-right
                (50, self.height - 80),             # Bottom-left
                (self.width - 80, self.height - 80) # Bottom-right
            ]
        else:
            coords = [(50, 50), (self.width - 80, 50)]
        
        for i, (x, y) in enumerate(coords[:len(emojis)]):
            color = emoji_colors[i % len(emoji_colors)]
            # Desenha círculo decorativo
            draw.ellipse([x, y, x + 60, y + 60], fill=color, outline=(255, 255, 255), width=3)
        
        return img
    
    def _add_border(self, img: Image.Image, color: tuple, 
                    width: int = 8) -> Image.Image:
        """Adiciona borda na imagem"""
        
        draw = ImageDraw.Draw(img)
        
        # Borda externa
        draw.rectangle(
            [0, 0, self.width - 1, self.height - 1],
            outline=color,
            width=width
        )
        
        return img
    
    def _add_badge(self, img: Image.Image, text: str,
                   position: str = "top-right",
                   bg_color: tuple = (255, 0, 0),
                   text_color: tuple = (255, 255, 255)) -> Image.Image:
        """Adiciona badge/etiqueta na thumbnail"""
        
        draw = ImageDraw.Draw(img)
        
        # Fonte para badge
        try:
            font = ImageFont.truetype(self.font_bold, 28)
        except:
            font = ImageFont.load_default()
        
        # Calcula tamanho do texto
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = 15
        badge_width = text_width + padding * 2
        badge_height = text_height + padding * 2
        
        # Posição do badge
        if position == "top-right":
            x = self.width - badge_width - 20
            y = 20
        elif position == "top-left":
            x = 20
            y = 20
        elif position == "bottom-right":
            x = self.width - badge_width - 20
            y = self.height - badge_height - 20
        else:
            x = 20
            y = self.height - badge_height - 20
        
        # Desenha badge
        draw.rounded_rectangle(
            [x, y, x + badge_width, y + badge_height],
            radius=10,
            fill=bg_color
        )
        
        # Texto do badge
        draw.text(
            (x + padding, y + padding - 5),
            text,
            font=font,
            fill=text_color
        )
        
        return img
    
    def generate(self, 
                 title: str,
                 style: str = "gradient_fire",
                 subtitle: str = None,
                 badge_text: str = None,
                 output_name: str = None,
                 background_image: str = None) -> str:
        """
        Gera thumbnail completa
        
        Args:
            title: Texto principal da thumbnail
            style: Estilo visual (gradient_fire, gradient_ocean, etc.)
            subtitle: Texto secundário opcional
            badge_text: Texto do badge (ex: "NOVO", "TOP 5")
            output_name: Nome do arquivo de saída
            background_image: Caminho para imagem de fundo (opcional)
        
        Returns:
            Caminho do arquivo gerado
        """
        
        print(f"\n🎨 Gerando thumbnail...")
        print(f"   Título: {title[:40]}...")
        print(f"   Estilo: {style}")
        
        # Obtém configurações do estilo
        style_config = self.styles.get(style, self.styles["gradient_fire"])
        
        # Cria ou carrega fundo
        if background_image and Path(background_image).exists():
            img = Image.open(background_image)
            img = img.resize((self.width, self.height), Image.LANCZOS)
            # Escurece um pouco para texto ficar legível
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.6)
        else:
            # Cria gradiente
            direction = random.choice(["vertical", "diagonal"])
            img = self._create_gradient(
                style_config["colors"][0],
                style_config["colors"][1],
                direction
            )
        
        # Prepara texto
        lines = self._wrap_text(title.upper(), max_chars=18)
        
        # Calcula tamanho da fonte
        font_size = self._get_optimal_font_size(
            title.upper(),
            max_width=self.width - 100,
            max_height=self.height - 200
        )
        
        try:
            font = ImageFont.truetype(self.font_bold, font_size)
            font_small = ImageFont.truetype(self.font_bold, int(font_size * 0.5))
        except:
            font = ImageFont.load_default()
            font_small = font
        
        # Calcula posição central do texto
        total_text_height = len(lines) * font_size * 1.2
        start_y = (self.height - total_text_height) / 2
        
        # Adiciona glow se configurado
        if style_config.get("glow"):
            for i, line in enumerate(lines):
                bbox = font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                x = (self.width - line_width) / 2
                y = start_y + (i * font_size * 1.2)
                
                img = img.convert('RGBA')
                img = self._add_glow_effect(
                    img, line, (x, y), font,
                    style_config["glow"], intensity=15
                )
        
        # Adiciona texto principal
        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            x = (self.width - line_width) / 2
            y = start_y + (i * font_size * 1.2)
            
            img = self._add_text_with_shadow(
                img, line, (x, y), font,
                style_config["text_color"],
                shadow=style_config.get("shadow", True)
            )
        
        # Adiciona subtitle se existir
        if subtitle:
            sub_y = start_y + total_text_height + 30
            bbox = font_small.getbbox(subtitle)
            sub_width = bbox[2] - bbox[0]
            sub_x = (self.width - sub_width) / 2
            
            img = self._add_text_with_shadow(
                img, subtitle, (sub_x, sub_y), font_small,
                style_config["text_color"],
                shadow=True
            )
        
        # Adiciona badge se existir
        if badge_text:
            img = self._add_badge(img, badge_text, position="top-right")
        
        # Adiciona borda se configurada
        if style_config.get("border"):
            img = self._add_border(img, style_config["border"])
        
        # Converte para RGB se necessário
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (0, 0, 0))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        # Salva
        if output_name is None:
            output_name = f"thumbnail_{title[:20].replace(' ', '_')}"
        
        output_path = self.output_dir / f"{output_name}.jpg"
        img.save(output_path, "JPEG", quality=95)
        
        print(f"   ✅ Thumbnail salva: {output_path}")
        
        return str(output_path)
    
    def generate_from_topic(self, topic: str, video_type: str = "education") -> str:
        """
        Gera thumbnail automaticamente baseado no tópico
        
        Args:
            topic: Tema do vídeo
            video_type: Tipo (education, entertainment, tech, lifestyle)
        
        Returns:
            Caminho da thumbnail
        """
        
        # Escolhe estilo baseado no tipo
        style_map = {
            "education": ["gradient_ocean", "clean_white", "gradient_purple"],
            "entertainment": ["gradient_fire", "neon_pink", "gradient_gold"],
            "tech": ["dark_dramatic", "gradient_purple", "neon_pink"],
            "lifestyle": ["gradient_green", "gradient_ocean", "clean_white"],
            "curiosity": ["dark_dramatic", "gradient_fire", "gradient_purple"],
        }
        
        styles = style_map.get(video_type, style_map["entertainment"])
        style = random.choice(styles)
        
        # Badge baseado no tipo
        badges = {
            "education": ["APRENDA", "DICAS", "📚"],
            "entertainment": ["INCRÍVEL", "WOW", "🔥"],
            "tech": ["TECH", "NOVO", "⚡"],
            "lifestyle": ["TOP", "LIFE", "✨"],
            "curiosity": ["FATOS", "SABIA?", "🤯"],
        }
        
        badge = random.choice(badges.get(video_type, badges["entertainment"]))
        
        return self.generate(
            title=topic,
            style=style,
            badge_text=badge
        )


# ===========================================
# TESTE
# ===========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTE: ThumbnailGenerator")
    print("="*60 + "\n")
    
    gen = ThumbnailGenerator()
    
    # Teste 1: Thumbnail simples
    print("\n📸 Teste 1: Thumbnail com gradiente fire")
    path1 = gen.generate(
        title="5 Hábitos que vão mudar sua vida",
        style="gradient_fire",
        badge_text="TOP 5"
    )
    
    # Teste 2: Thumbnail estilo escuro
    print("\n📸 Teste 2: Thumbnail dark dramatic")
    path2 = gen.generate(
        title="O segredo que ninguém conta",
        style="dark_dramatic",
        subtitle="Descubra agora!",
        badge_text="NOVO"
    )
    
    # Teste 3: Thumbnail neon
    print("\n📸 Teste 3: Thumbnail neon pink")
    path3 = gen.generate(
        title="Curiosidades incríveis",
        style="neon_pink",
        badge_text="🤯"
    )
    
    # Teste 4: Automático
    print("\n📸 Teste 4: Geração automática")
    path4 = gen.generate_from_topic(
        "Por que o céu é azul?",
        video_type="curiosity"
    )
    
    print("\n" + "="*60)
    print("✅ Testes concluídos!")
    print(f"   Thumbnails em: output/thumbnails/")
    print("="*60 + "\n")
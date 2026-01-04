"""
Gerador de Legendas Estilo TikTok/Shorts
- 2-3 palavras por vez
- Troca rápida
- Centralizada
- Borda preta
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import numpy as np


class SubtitleGenerator:
    """Gera legendas estilo TikTok/Reels"""
    
    def __init__(self):
        # Configuracoes padrao
        self.font_size = 70
        self.words_per_subtitle = 3  # 2-3 palavras por legenda
        self.font_color = "white"
        self.highlight_color = "#FFFF00"  # Amarelo para destaque
        self.stroke_color = "black"
        self.stroke_width = 4
        
        # Tenta carregar fonte
        self.font_path = self._find_font()
    
    def _find_font(self) -> str:
        """Encontra uma fonte bold no sistema"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        ]
        
        for path in font_paths:
            if Path(path).exists():
                return path
        
        return None
    
    def split_text_into_chunks(self, text: str, words_per_chunk: int = None) -> list:
        """
        Divide texto em chunks de 2-3 palavras
        
        Args:
            text: Texto completo
            words_per_chunk: Palavras por chunk (padrao: 3)
        
        Returns:
            Lista de chunks
        """
        words_per_chunk = words_per_chunk or self.words_per_subtitle
        
        # Remove quebras de linha extras e limpa
        text = ' '.join(text.split())
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), words_per_chunk):
            chunk = ' '.join(words[i:i + words_per_chunk])
            chunks.append(chunk)
        
        return chunks
    
    def calculate_timings(self, chunks: list, total_duration: float) -> list:
        """
        Calcula timing de cada legenda
        
        Returns:
            Lista de {"text": "...", "start": 0.0, "end": 1.5}
        """
        if not chunks:
            return []
        
        duration_per_chunk = total_duration / len(chunks)
        
        timings = []
        for i, chunk in enumerate(chunks):
            timings.append({
                "text": chunk,
                "start": i * duration_per_chunk,
                "end": (i + 1) * duration_per_chunk,
                "duration": duration_per_chunk
            })
        
        return timings
    
    def create_subtitle_image(self, 
                              text: str, 
                              width: int, 
                              height: int,
                              font_size: int = None,
                              color: str = None,
                              highlight_word: int = None) -> np.ndarray:
        """
        Cria imagem da legenda com fundo transparente
        
        Args:
            text: Texto da legenda
            width: Largura do frame
            height: Altura do frame
            font_size: Tamanho da fonte
            color: Cor do texto
            highlight_word: Indice da palavra a destacar em amarelo
        
        Returns:
            Array numpy RGBA
        """
        font_size = font_size or self.font_size
        color = color or self.font_color
        
        # Cria imagem transparente
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Carrega fonte
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Calcula posicao central
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2 + 200  # Um pouco abaixo do centro
        
        # Desenha borda preta (stroke)
        for dx in range(-self.stroke_width, self.stroke_width + 1):
            for dy in range(-self.stroke_width, self.stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=self.stroke_color)
        
        # Desenha texto principal
        if highlight_word is not None:
            # Desenha palavra por palavra com destaque
            words = text.split()
            current_x = x
            
            for i, word in enumerate(words):
                word_color = self.highlight_color if i == highlight_word else color
                
                # Borda da palavra
                for dx in range(-self.stroke_width, self.stroke_width + 1):
                    for dy in range(-self.stroke_width, self.stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((current_x + dx, y + dy), word + " ", 
                                      font=font, fill=self.stroke_color)
                
                # Palavra
                draw.text((current_x, y), word + " ", font=font, fill=word_color)
                
                # Avanca posicao
                word_bbox = draw.textbbox((0, 0), word + " ", font=font)
                current_x += word_bbox[2] - word_bbox[0]
        else:
            draw.text((x, y), text, font=font, fill=color)
        
        return np.array(img)
    
    def generate_subtitle_clips(self, 
                                text: str, 
                                total_duration: float,
                                width: int,
                                height: int,
                                words_per_subtitle: int = 3) -> list:
        """
        Gera lista de clips de legenda para o MoviePy
        
        Args:
            text: Texto completo da narracao
            total_duration: Duracao total do audio
            width: Largura do video
            height: Altura do video
            words_per_subtitle: Palavras por legenda
        
        Returns:
            Lista de dicts com info para criar TextClips
        """
        chunks = self.split_text_into_chunks(text, words_per_subtitle)
        timings = self.calculate_timings(chunks, total_duration)
        
        return timings


# Funcao de conveniencia
def create_subtitles(text: str, duration: float, words_per_sub: int = 3) -> list:
    """
    Cria lista de legendas a partir do texto
    
    Returns:
        Lista de {"text": "...", "start": 0.0, "end": 1.5}
    """
    gen = SubtitleGenerator()
    chunks = gen.split_text_into_chunks(text, words_per_sub)
    return gen.calculate_timings(chunks, duration)


if __name__ == "__main__":
    # Teste
    text = """Voce sabia que o cerebro humano tem mais conexoes neurais 
    do que estrelas na Via Lactea? Isso mesmo, cerca de 100 trilhoes 
    de conexoes permitem que voce pense, sinta e se mova."""
    
    gen = SubtitleGenerator()
    chunks = gen.split_text_into_chunks(text, 3)
    
    print("Legendas geradas:")
    print("-" * 40)
    for i, chunk in enumerate(chunks):
        print(f"{i+1}. {chunk}")
    
    timings = gen.calculate_timings(chunks, 30.0)  # 30 segundos
    
    print("\nTimings:")
    print("-" * 40)
    for t in timings:
        print(f"{t['start']:.1f}s - {t['end']:.1f}s: {t['text']}")

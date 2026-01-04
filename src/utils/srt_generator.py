"""
Gerador de Legendas SRT Sincronizadas
- 2 palavras por legenda
- Tempo calculado por velocidade de fala
- Sincronizacao precisa
"""
from pathlib import Path
import re


class SRTGenerator:
    """Gera arquivos SRT sincronizados com audio"""
    
    def __init__(self, words_per_subtitle: int = 2):
        """
        Args:
            words_per_subtitle: Palavras por legenda (padrao: 2)
        """
        self.words_per_subtitle = words_per_subtitle
        
        # Velocidade media de fala em portugues: 150 palavras por minuto
        # Ou seja, ~2.5 palavras por segundo
        # Para 2 palavras: ~0.8 segundos por legenda
        self.words_per_second = 2.5
    
    def estimate_word_duration(self, word: str) -> float:
        """
        Estima duracao de uma palavra baseado no tamanho
        Palavras maiores demoram mais para falar
        """
        base_duration = 0.3  # duracao minima
        
        # Adiciona tempo baseado no tamanho
        extra = len(word) * 0.03
        
        return base_duration + extra
    
    def split_into_chunks(self, text: str) -> list:
        """Divide texto em chunks de 2 palavras"""
        
        # Limpa o texto
        text = ' '.join(text.split())
        text = re.sub(r'[^\w\s.,!?áéíóúâêîôûãõàèìòùäëïöüç-]', '', text, flags=re.IGNORECASE)
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.words_per_subtitle):
            chunk = ' '.join(words[i:i + self.words_per_subtitle])
            chunks.append({
                "text": chunk,
                "words": words[i:i + self.words_per_subtitle]
            })
        
        return chunks
    
    def calculate_timings(self, text: str, total_duration: float) -> list:
        """
        Calcula timing preciso para cada legenda
        
        Args:
            text: Texto completo da narracao
            total_duration: Duracao total do audio em segundos
        
        Returns:
            Lista de {"text", "start", "end", "duration"}
        """
        chunks = self.split_into_chunks(text)
        
        if not chunks:
            return []
        
        # Calcula peso de cada chunk baseado no tamanho das palavras
        total_weight = 0
        for chunk in chunks:
            weight = sum(len(word) for word in chunk["words"])
            chunk["weight"] = max(weight, 3)  # minimo de peso
            total_weight += chunk["weight"]
        
        # Distribui o tempo proporcionalmente
        timings = []
        current_time = 0.0
        
        for i, chunk in enumerate(chunks):
            # Duracao proporcional ao peso
            duration = (chunk["weight"] / total_weight) * total_duration
            
            # Minimo de 0.4s, maximo de 1.5s por legenda
            duration = max(0.4, min(duration, 1.5))
            
            timings.append({
                "index": i + 1,
                "text": chunk["text"],
                "start": current_time,
                "end": current_time + duration,
                "duration": duration
            })
            
            current_time += duration
        
        # Ajusta para fechar exatamente com a duracao total
        if timings:
            scale = total_duration / current_time
            current_time = 0.0
            
            for timing in timings:
                timing["start"] = current_time
                timing["duration"] *= scale
                timing["end"] = current_time + timing["duration"]
                current_time = timing["end"]
            
            # Garante que o ultimo termine exatamente no final
            timings[-1]["end"] = total_duration
        
        return timings
    
    def format_time_srt(self, seconds: float) -> str:
        """Formata tempo para formato SRT: 00:00:00,000"""
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def generate_srt(self, text: str, total_duration: float, output_path: str = None) -> str:
        """
        Gera conteudo do arquivo SRT
        
        Args:
            text: Texto completo
            total_duration: Duracao do audio
            output_path: Caminho para salvar (opcional)
        
        Returns:
            Conteudo SRT como string
        """
        timings = self.calculate_timings(text, total_duration)
        
        srt_content = ""
        
        for timing in timings:
            start_str = self.format_time_srt(timing["start"])
            end_str = self.format_time_srt(timing["end"])
            
            srt_content += f"{timing['index']}\n"
            srt_content += f"{start_str} --> {end_str}\n"
            srt_content += f"{timing['text'].upper()}\n"
            srt_content += "\n"
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(srt_content, encoding='utf-8')
        
        return srt_content
    
    def parse_srt(self, srt_path: str) -> list:
        """Le arquivo SRT e retorna lista de legendas"""
        
        content = Path(srt_path).read_text(encoding='utf-8')
        
        # Regex para parsear SRT
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\n|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        subtitles = []
        for match in matches:
            index, start, end, text = match
            
            subtitles.append({
                "index": int(index),
                "start": self._parse_time(start),
                "end": self._parse_time(end),
                "text": text.strip()
            })
        
        return subtitles
    
    def _parse_time(self, time_str: str) -> float:
        """Converte tempo SRT para segundos"""
        
        # 00:00:00,000
        parts = time_str.replace(',', ':').split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        millis = int(parts[3])
        
        return hours * 3600 + minutes * 60 + seconds + millis / 1000


def generate_srt_from_text(text: str, duration: float, output_path: str = None) -> list:
    """
    Funcao de conveniencia para gerar legendas
    
    Returns:
        Lista de timings
    """
    gen = SRTGenerator(words_per_subtitle=2)
    
    if output_path:
        gen.generate_srt(text, duration, output_path)
    
    return gen.calculate_timings(text, duration)


if __name__ == "__main__":
    # Teste
    text = """Voce sabia que o cerebro humano tem mais conexoes neurais 
    do que estrelas na Via Lactea? Sao cerca de cem trilhoes de conexoes 
    que permitem voce pensar, sentir e se mover. Incrivel nao e mesmo?
    Deixe seu like e siga para mais curiosidades."""
    
    gen = SRTGenerator(words_per_subtitle=2)
    
    print("=" * 60)
    print("TESTE DE GERACAO DE LEGENDAS")
    print("=" * 60)
    print(f"\nTexto: {text[:100]}...")
    print(f"Duracao simulada: 30 segundos")
    print(f"Palavras por legenda: 2")
    print()
    
    timings = gen.calculate_timings(text, 30.0)
    
    print("LEGENDAS GERADAS:")
    print("-" * 60)
    
    for t in timings:
        print(f"{t['start']:5.2f}s - {t['end']:5.2f}s ({t['duration']:.2f}s): {t['text'].upper()}")
    
    print()
    print("ARQUIVO SRT:")
    print("-" * 60)
    
    srt = gen.generate_srt(text, 30.0)
    print(srt[:500])

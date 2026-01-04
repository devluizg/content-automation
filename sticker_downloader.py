"""
Sticker/GIF Downloader - Tenor + Pixabay
Baixa GIFs animados e imagens para usar nos vídeos
"""

import os
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class StickerDownloader:
    """Baixa stickers animados do Tenor e imagens do Pixabay"""
    
    def __init__(self):
        self.tenor_key = os.getenv("TENOR_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        
        if not self.tenor_key:
            logger.warning("⚠️ TENOR_API_KEY não configurada")
        if not self.pixabay_key:
            logger.warning("⚠️ PIXABAY_API_KEY não configurada")
    
    # ===========================================
    # GERAÇÃO DE TERMOS DE BUSCA
    # ===========================================
    
    def generate_search_term(self, prompt: str, topic: str, style: str = "stickman") -> str:
        """
        Converte o prompt da IA em um termo de busca otimizado para Tenor
        
        Args:
            prompt: Prompt original (ex: "pessoa pensando sobre o universo")
            topic: Tema do vídeo
            style: Estilo desejado (stickman, cartoon, etc)
        """
        
        # Mapeamento de ações/emoções comuns para termos de busca
        action_mappings = {
            # Português -> Inglês (Tenor tem mais resultados em inglês)
            "pensando": "thinking",
            "pensar": "thinking",
            "andando": "walking",
            "andar": "walking",
            "correndo": "running",
            "correr": "running",
            "falando": "talking",
            "falar": "talking",
            "apontando": "pointing",
            "apontar": "pointing",
            "dançando": "dancing",
            "dançar": "dancing",
            "escrevendo": "writing",
            "escrever": "writing",
            "digitando": "typing",
            "digitar": "typing",
            "pulando": "jumping",
            "pular": "jumping",
            "chorando": "crying",
            "chorar": "crying",
            "rindo": "laughing",
            "rir": "laughing",
            "surpreso": "surprised",
            "surpresa": "surprised",
            "chocado": "shocked",
            "confuso": "confused",
            "feliz": "happy",
            "triste": "sad",
            "animado": "excited",
            "nervoso": "nervous",
            "com medo": "scared",
            "bravo": "angry",
            "dormindo": "sleeping",
            "acordando": "waking up",
            "comendo": "eating",
            "bebendo": "drinking",
            "trabalhando": "working",
            "estudando": "studying",
            "lendo": "reading",
            "olhando": "looking",
            "procurando": "searching",
            "esperando": "waiting",
            "comemorando": "celebrating",
            "aplaudindo": "clapping",
            "acenando": "waving",
        }
        
        # Mapeamento de objetos/conceitos
        concept_mappings = {
            "dinheiro": "money",
            "cérebro": "brain",
            "coração": "heart",
            "ideia": "idea lightbulb",
            "pergunta": "question",
            "resposta": "answer",
            "sucesso": "success",
            "fracasso": "fail",
            "amor": "love",
            "ódio": "hate",
            "tempo": "time clock",
            "universo": "universe space",
            "planeta": "planet",
            "terra": "earth",
            "sol": "sun",
            "lua": "moon",
            "estrela": "star",
            "fogo": "fire",
            "água": "water",
            "ar": "air wind",
            "comida": "food",
            "casa": "house home",
            "carro": "car",
            "computador": "computer",
            "celular": "phone",
            "livro": "book",
            "música": "music",
            "filme": "movie",
            "jogo": "game",
        }
        
        # Prefixos baseados no estilo
        style_prefixes = {
            "stickman": "stick figure",
            "stickman_cute": "cute stick figure",
            "stickman_comic": "stick figure comic",
            "cartoon": "cartoon character",
            "anime": "anime character",
            "meme": "meme reaction",
        }
        
        # Limpa o prompt
        prompt_lower = prompt.lower()
        
        # Encontra ações no prompt
        found_actions = []
        for pt_word, en_word in action_mappings.items():
            if pt_word in prompt_lower:
                found_actions.append(en_word)
        
        # Encontra conceitos no prompt
        found_concepts = []
        for pt_word, en_word in concept_mappings.items():
            if pt_word in prompt_lower:
                found_concepts.append(en_word)
        
        # Monta o termo de busca
        prefix = style_prefixes.get(style, "stick figure")
        
        search_parts = [prefix]
        
        # Adiciona ações encontradas (máximo 2)
        if found_actions:
            search_parts.extend(found_actions[:2])
        
        # Adiciona conceitos encontrados (máximo 1)
        if found_concepts:
            search_parts.append(found_concepts[0])
        
        # Se não encontrou nada específico, usa palavras do prompt
        if len(search_parts) == 1:
            # Remove stopwords e pega palavras relevantes
            stopwords = [
                "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos",
                "em", "na", "no", "nas", "nos", "para", "por", "com", "sem",
                "que", "se", "é", "são", "foi", "era", "será", "está", "estão",
                "muito", "mais", "menos", "bem", "mal", "aqui", "ali", "lá",
                "isso", "isto", "esse", "este", "essa", "esta", "qual", "quais",
                "como", "quando", "onde", "porque", "porquê", "scene", "showing",
                "image", "depicting", "illustration", "about", "the", "and"
            ]
            
            words = prompt_lower.split()
            relevant_words = [w for w in words if w not in stopwords and len(w) > 3]
            
            if relevant_words:
                search_parts.extend(relevant_words[:2])
        
        search_term = " ".join(search_parts)
        
        print(f"    🔍 Prompt: '{prompt[:50]}...'")
        print(f"    🎯 Busca: '{search_term}'")
        
        return search_term
    
    # ===========================================
    # TENOR - GIFs ANIMADOS
    # ===========================================
    
    def search_tenor(self, query: str, limit: int = 10) -> list:
        """Busca GIFs no Tenor"""
        if not self.tenor_key:
            return []
        
        try:
            url = "https://tenor.googleapis.com/v2/search"
            params = {
                "q": query,
                "key": self.tenor_key,
                "limit": limit,
                "media_filter": "mp4,gif",  # Prioriza MP4 (melhor para vídeo)
                "contentfilter": "medium"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                logger.error(f"Tenor erro: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Tenor exceção: {e}")
            return []
    
    def download_tenor_clip(self, result: dict, output_path: str) -> dict:
        """
        Baixa um clipe do Tenor (prefere MP4)
        
        Returns:
            dict com 'path', 'type' (video/gif), 'duration'
        """
        try:
            media_formats = result.get("media_formats", {})
            
            # Prioridade: MP4 > GIF (MP4 é melhor para edição de vídeo)
            if "mp4" in media_formats:
                media_url = media_formats["mp4"].get("url")
                media_type = "video"
                output_path = output_path.rsplit(".", 1)[0] + ".mp4"
            elif "gif" in media_formats:
                media_url = media_formats["gif"].get("url")
                media_type = "gif"
                output_path = output_path.rsplit(".", 1)[0] + ".gif"
            else:
                logger.error("Nenhum formato adequado encontrado")
                return None
            
            # Baixa o arquivo
            response = requests.get(media_url, timeout=60)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                # Obtém duração do clipe
                duration = self._get_media_duration(output_path)
                
                return {
                    "path": output_path,
                    "type": media_type,
                    "duration": duration,
                    "source": "tenor"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao baixar do Tenor: {e}")
            return None
    
    # ===========================================
    # PIXABAY - IMAGENS ESTÁTICAS (FALLBACK)
    # ===========================================
    
    def search_pixabay(self, query: str, limit: int = 5, orientation: str = "vertical") -> list:
        """Busca imagens no Pixabay (fallback)"""
        if not self.pixabay_key:
            return []
        
        try:
            url = "https://pixabay.com/api/"
            params = {
                "key": self.pixabay_key,
                "q": query,
                "per_page": limit,
                "orientation": orientation,
                "image_type": "illustration",
                "safesearch": "true"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json().get("hits", [])
            return []
            
        except Exception as e:
            logger.error(f"Pixabay exceção: {e}")
            return []
    
    def download_pixabay_image(self, result: dict, output_path: str) -> dict:
        """Baixa imagem do Pixabay"""
        try:
            image_url = result.get("largeImageURL") or result.get("webformatURL")
            
            if not image_url:
                return None
            
            output_path = output_path.rsplit(".", 1)[0] + ".jpg"
            
            response = requests.get(image_url, timeout=60)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                return {
                    "path": output_path,
                    "type": "image",
                    "duration": 0,  # Imagens não têm duração
                    "source": "pixabay"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao baixar do Pixabay: {e}")
            return None
    
    # ===========================================
    # FUNÇÕES AUXILIARES
    # ===========================================
    
    def _get_media_duration(self, file_path: str) -> float:
        """Obtém a duração de um vídeo/GIF usando ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.stdout.strip():
                return float(result.stdout.strip())
        except:
            pass
        
        return 2.0  # Duração padrão se não conseguir detectar
    
    def convert_to_video(self, input_path: str, output_path: str, 
                         duration: float, width: int, height: int) -> str:
        """
        Converte GIF/imagem para vídeo MP4 com duração específica
        
        - Se for GIF: faz loop até atingir a duração
        - Se for imagem: cria vídeo estático
        """
        try:
            output_path = output_path.rsplit(".", 1)[0] + ".mp4"
            
            # Detecta se é GIF ou imagem
            is_gif = input_path.lower().endswith(".gif")
            is_video = input_path.lower().endswith(".mp4")
            
            if is_video:
                # Já é vídeo, só redimensiona e ajusta duração
                cmd = [
                    'ffmpeg', '-y',
                    '-stream_loop', '-1',  # Loop infinito
                    '-i', input_path,
                    '-t', str(duration),  # Duração desejada
                    '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
                           f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-an',  # Remove áudio do GIF
                    output_path
                ]
            elif is_gif:
                # Converte GIF para vídeo com loop
                cmd = [
                    'ffmpeg', '-y',
                    '-ignore_loop', '0',  # Respeita loop do GIF
                    '-i', input_path,
                    '-t', str(duration),
                    '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
                           f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p',
                    '-an',
                    output_path
                ]
            else:
                # Imagem estática -> vídeo
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1',
                    '-i', input_path,
                    '-t', str(duration),
                    '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
                           f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p',
                    '-an',
                    output_path
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"FFmpeg erro: {result.stderr[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao converter para vídeo: {e}")
            return None
    
    # ===========================================
    # MÉTODO PRINCIPAL
    # ===========================================
    
    def get_clips_for_scenes(
        self,
        topic: str,
        prompts: list,
        output_dir: str,
        width: int = 1080,
        height: int = 1920,
        duration_per_clip: float = 5.0,
        style: str = "stickman"
    ) -> list:
        """
        Busca e baixa clipes para cada cena do vídeo
        
        Args:
            topic: Tema principal do vídeo
            prompts: Lista de prompts/descrições das cenas
            output_dir: Diretório para salvar os clipes
            width: Largura do vídeo
            height: Altura do vídeo
            duration_per_clip: Duração de cada clipe em segundos
            style: Estilo dos stickers
        
        Returns:
            Lista de caminhos dos clipes (MP4)
        """
        clips = []
        os.makedirs(output_dir, exist_ok=True)
        
        used_tenor_ids = set()  # Evita repetir GIFs
        
        for i, prompt in enumerate(prompts):
            print(f"\n  📍 Cena {i+1}/{len(prompts)}")
            
            # Gera termo de busca otimizado
            search_term = self.generate_search_term(prompt, topic, style)
            
            clip_info = None
            
            # 1️⃣ Tenta Tenor primeiro (GIFs animados)
            tenor_results = self.search_tenor(search_term, limit=10)
            
            # Filtra resultados já usados
            tenor_results = [r for r in tenor_results if r.get("id") not in used_tenor_ids]
            
            if tenor_results:
                result = tenor_results[0]
                used_tenor_ids.add(result.get("id"))
                
                temp_path = os.path.join(output_dir, f"tenor_{i+1:02d}")
                clip_info = self.download_tenor_clip(result, temp_path)
                
                if clip_info:
                    print(f"    ✅ Tenor: {clip_info['type']} ({clip_info['duration']:.1f}s)")
            
            # 2️⃣ Fallback: Pixabay (imagens estáticas)
            if not clip_info:
                print(f"    ⚠️ Tenor não encontrou, tentando Pixabay...")
                
                # Ajusta busca para Pixabay (mais genérico)
                pixabay_term = search_term.replace("stick figure", "illustration")
                pixabay_results = self.search_pixabay(pixabay_term, limit=5)
                
                if not pixabay_results:
                    # Tenta busca mais genérica
                    pixabay_results = self.search_pixabay(topic, limit=5)
                
                if pixabay_results:
                    result = pixabay_results[i % len(pixabay_results)]
                    
                    temp_path = os.path.join(output_dir, f"pixabay_{i+1:02d}")
                    clip_info = self.download_pixabay_image(result, temp_path)
                    
                    if clip_info:
                        print(f"    ✅ Pixabay: imagem estática")
            
            # 3️⃣ Converte para vídeo MP4 padronizado
            if clip_info:
                final_path = os.path.join(output_dir, f"clip_{i+1:02d}.mp4")
                
                converted = self.convert_to_video(
                    input_path=clip_info["path"],
                    output_path=final_path,
                    duration=duration_per_clip,
                    width=width,
                    height=height
                )
                
                if converted:
                    clips.append(converted)
                    print(f"    🎬 Clipe final: {os.path.basename(converted)}")
                    
                    # Remove arquivo temporário
                    try:
                        if clip_info["path"] != converted:
                            os.remove(clip_info["path"])
                    except:
                        pass
                else:
                    print(f"    ❌ Erro ao converter clipe {i+1}")
            else:
                print(f"    ❌ Nenhuma mídia encontrada para cena {i+1}")
        
        return clips


# ===========================================
# TESTE
# ===========================================

if __name__ == "__main__":
    downloader = StickerDownloader()
    
    # Teste de geração de termos
    print("\n🧪 Teste de Termos de Busca:\n")
    
    test_prompts = [
        "Uma pessoa pensando sobre o universo",
        "Alguém correndo muito rápido",
        "Pessoa surpresa com uma descoberta",
        "Comemorando uma vitória",
        "Pessoa confusa sem entender nada",
    ]
    
    for prompt in test_prompts:
        term = downloader.generate_search_term(prompt, "curiosidades", "stickman")
        print()
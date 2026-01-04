"""
Bot Telegram - Gerador Automático de Vídeos + Upload YouTube
CONTENT-AUTOMATION v4.5 - CORRIGIDO
Com integração Tenor API - GIFs ANIMADOS + Busca Otimizada
CORREÇÕES: target_duration, is_short, formato de imagens
"""

import os
import asyncio
import logging
import subprocess
import tempfile
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Carrega variáveis
load_dotenv()

# Imports do projeto
from config.settings import (
    TELEGRAM_BOT_TOKEN,
    AUTHORIZED_USERS,
    OUTPUT_PROJECTS,
    print_config_status
)
from src.generators.text_generator import TextGenerator
from src.generators.image_generator import ImageGenerator
from src.generators.audio_generator import AudioGenerator
from src.generators.video_generator import VideoGenerator
from src.platforms.youtube_uploader import YouTubeUploader

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===========================================
# STICKER DOWNLOADER - VERSÃO v4.5 (COM VALIDAÇÃO + FORMATO)
# ===========================================

class StickerDownloader:
    """
    Baixa stickers e GIFs do Tenor + Pixabay
    v4.5: Com validação de arquivos e suporte a formato
    """
    
    def __init__(self):
        self.tenor_key = os.getenv("TENOR_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        
        if not self.tenor_key:
            logger.warning("⚠️ TENOR_API_KEY não encontrada no .env")
        if not self.pixabay_key:
            logger.warning("⚠️ PIXABAY_API_KEY não encontrada no .env")
        
        # Mapeamento de ações/emoções PT → EN
        self.action_mappings = {
            "pensando": "thinking",
            "pensar": "thinking",
            "refletindo": "thinking pondering",
            "andando": "walking",
            "andar": "walking",
            "correndo": "running",
            "correr": "running fast",
            "falando": "talking speaking",
            "falar": "talking",
            "apontando": "pointing",
            "apontar": "pointing finger",
            "dançando": "dancing",
            "dançar": "dancing happy",
            "escrevendo": "writing",
            "escrever": "writing pen",
            "digitando": "typing keyboard",
            "digitar": "typing computer",
            "pulando": "jumping",
            "pular": "jumping excited",
            "chorando": "crying sad",
            "chorar": "crying tears",
            "rindo": "laughing",
            "rir": "laughing funny",
            "gargalhando": "laughing hard lol",
            "surpreso": "surprised shocked",
            "surpresa": "surprised wow",
            "chocado": "shocked omg",
            "confuso": "confused thinking",
            "feliz": "happy smiling",
            "triste": "sad crying",
            "animado": "excited happy",
            "nervoso": "nervous anxious",
            "com medo": "scared afraid",
            "assustado": "scared frightened",
            "bravo": "angry mad",
            "irritado": "angry frustrated",
            "dormindo": "sleeping zzz",
            "acordando": "waking up morning",
            "comendo": "eating food",
            "bebendo": "drinking",
            "trabalhando": "working busy",
            "estudando": "studying reading",
            "lendo": "reading book",
            "olhando": "looking watching",
            "procurando": "searching looking",
            "esperando": "waiting bored",
            "comemorando": "celebrating party",
            "aplaudindo": "clapping applause",
            "acenando": "waving hello",
            "explicando": "explaining teaching",
            "mostrando": "showing presenting",
            "descobrindo": "discovering eureka",
            "aprendendo": "learning studying",
            "perguntando": "asking question",
            "respondendo": "answering",
            "concordando": "agreeing nodding yes",
            "discordando": "disagreeing no",
            "duvidando": "doubting hmm",
            "amando": "loving heart",
            "odiando": "hating angry",
            "ignorando": "ignoring whatever",
            "fugindo": "running away escape",
            "chegando": "arriving coming",
            "saindo": "leaving bye",
            "começando": "starting begin",
            "terminando": "finishing done",
            "ganhando": "winning victory",
            "perdendo": "losing fail",
        }
        
        # Mapeamento de conceitos/objetos PT → EN
        self.concept_mappings = {
            "dinheiro": "money cash",
            "rico": "rich money",
            "pobre": "poor broke",
            "cérebro": "brain smart",
            "inteligente": "smart genius",
            "burro": "dumb confused",
            "coração": "heart love",
            "amor": "love heart romantic",
            "ódio": "hate angry",
            "ideia": "idea lightbulb eureka",
            "pergunta": "question confused",
            "resposta": "answer solution",
            "sucesso": "success winner",
            "fracasso": "fail loser",
            "vitória": "victory winning",
            "derrota": "defeat losing",
            "tempo": "time clock",
            "rápido": "fast speed",
            "devagar": "slow waiting",
            "universo": "universe space galaxy",
            "espaço": "space astronaut",
            "planeta": "planet earth world",
            "terra": "earth world globe",
            "sol": "sun sunny bright",
            "lua": "moon night",
            "estrela": "star shining",
            "fogo": "fire burning hot",
            "água": "water splash",
            "ar": "wind air blow",
            "comida": "food eating hungry",
            "fome": "hungry starving",
            "casa": "house home",
            "família": "family together",
            "carro": "car driving",
            "avião": "airplane flying",
            "computador": "computer typing",
            "celular": "phone texting",
            "internet": "internet online",
            "livro": "book reading",
            "escola": "school studying",
            "trabalho": "work office busy",
            "música": "music dancing",
            "filme": "movie watching",
            "jogo": "game playing",
            "esporte": "sports athletic",
            "animal": "animal cute",
            "cachorro": "dog puppy",
            "gato": "cat kitty",
            "pessoa": "person human",
            "homem": "man guy",
            "mulher": "woman girl",
            "criança": "child kid",
            "bebê": "baby cute",
            "velho": "old elderly",
            "jovem": "young teenager",
            "amigo": "friend buddy",
            "inimigo": "enemy rival",
            "incrível": "amazing wow awesome",
            "impressionante": "impressive wow",
            "curioso": "curious wondering",
            "interessante": "interesting hmm",
            "chato": "boring bored",
            "divertido": "funny fun",
            "perigoso": "danger warning",
            "seguro": "safe secure",
            "importante": "important attention",
            "secreto": "secret mystery shh",
            "misterioso": "mystery suspicious",
            "verdade": "true real",
            "mentira": "lie false",
            "problema": "problem trouble",
            "solução": "solution fixed",
            "começar": "start begin",
            "fim": "end finish",
            "primeiro": "first number one",
            "último": "last final",
            "maior": "bigger large",
            "menor": "smaller tiny",
            "melhor": "better best",
            "pior": "worse worst",
        }
        
        # Variações para evitar repetição
        self.scene_variations = [
            "excited", "dramatic", "funny", "serious", "cute",
            "cool", "epic", "crazy", "surprised", "happy",
            "sad", "angry", "confused", "thinking", "celebrating",
        ]
        
        # Prefixos por estilo
        self.style_prefixes = {
            "tenor_sticker": "stick figure",
            "tenor_stickman": "stick figure",
            "tenor_gif": "",
            "tenor_meme": "meme reaction funny",
            "stickman": "stick figure",
            "stickman_cute": "cute stick figure",
            "stickman_comic": "stick figure comic",
        }
    
    def validate_media_file(self, file_path: str) -> bool:
        """
        Valida se o arquivo de mídia está íntegro e pode ser usado
        
        Returns:
            True se válido, False se corrompido
        """
        if not os.path.exists(file_path):
            return False
        
        # Verifica tamanho mínimo (arquivos muito pequenos geralmente são inválidos)
        file_size = os.path.getsize(file_path)
        if file_size < 1000:  # Menos de 1KB
            print(f"      ⚠️ Arquivo muito pequeno: {file_size} bytes")
            return False
        
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.mp4', '.webm', '.mov']:
            # Valida vídeo usando ffprobe
            try:
                result = subprocess.run([
                    'ffprobe', '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height,duration,nb_frames',
                    '-of', 'csv=p=0',
                    file_path
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    print(f"      ⚠️ ffprobe erro: {result.stderr[:100] if result.stderr else 'unknown'}")
                    return False
                
                output = result.stdout.strip()
                if not output:
                    print(f"      ⚠️ Sem informações de stream de vídeo")
                    return False
                
                # Verifica se tem dimensões válidas
                parts = output.split(',')
                if len(parts) >= 2:
                    try:
                        width = int(parts[0]) if parts[0] else 0
                        height = int(parts[1]) if parts[1] else 0
                        if width < 10 or height < 10:
                            print(f"      ⚠️ Dimensões inválidas: {width}x{height}")
                            return False
                    except ValueError:
                        pass
                
                return True
                
            except subprocess.TimeoutExpired:
                print(f"      ⚠️ Timeout ao validar vídeo")
                return False
            except FileNotFoundError:
                # ffprobe não encontrado, assume válido
                logger.warning("ffprobe não encontrado, pulando validação")
                return True
            except Exception as e:
                print(f"      ⚠️ Erro ao validar vídeo: {e}")
                return False
        
        elif ext == '.gif':
            # Para GIFs, verificação básica com PIL
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    # Tenta carregar o primeiro frame
                    img.load()
                    # Verifica dimensões
                    if img.width < 10 or img.height < 10:
                        print(f"      ⚠️ GIF muito pequeno: {img.width}x{img.height}")
                        return False
                return True
            except Exception as e:
                print(f"      ⚠️ GIF inválido: {e}")
                return False
        
        elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
            # Para imagens
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    img.load()
                    if img.width < 10 or img.height < 10:
                        return False
                return True
            except Exception as e:
                print(f"      ⚠️ Imagem inválida: {e}")
                return False
        
        # Tipo desconhecido, assume válido
        return True
    
    def generate_search_term(self, prompt: str, topic: str, style: str = "tenor_sticker", scene_index: int = 0) -> str:
        """Converte o prompt da IA em termo de busca otimizado para Tenor"""
        prompt_lower = prompt.lower()
        
        found_actions = []
        for pt_word, en_word in self.action_mappings.items():
            if pt_word in prompt_lower:
                found_actions.append(en_word)
        
        found_concepts = []
        for pt_word, en_word in self.concept_mappings.items():
            if pt_word in prompt_lower:
                found_concepts.append(en_word)
        
        prefix = self.style_prefixes.get(style, "stick figure")
        search_parts = []
        
        if prefix:
            search_parts.append(prefix)
        
        if found_actions:
            action_idx = scene_index % len(found_actions)
            search_parts.append(found_actions[action_idx])
        
        if found_concepts:
            concept_idx = scene_index % len(found_concepts)
            search_parts.append(found_concepts[concept_idx])
        
        if len(search_parts) <= 1:
            stopwords = [
                "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos",
                "em", "na", "no", "nas", "nos", "para", "por", "com", "sem",
                "que", "se", "é", "são", "foi", "era", "será", "está", "estão",
                "muito", "mais", "menos", "bem", "mal", "aqui", "ali", "lá",
                "isso", "isto", "esse", "este", "essa", "esta", "qual", "quais",
                "como", "quando", "onde", "porque", "porquê", "scene", "showing",
                "image", "depicting", "illustration", "about", "the", "and",
                "cena", "mostrando", "imagem", "sobre", "dramatic", "high", "quality",
                "parte", "primeiro", "segundo", "terceiro", "número"
            ]
            
            words = prompt_lower.split()
            relevant_words = [w for w in words if w not in stopwords and len(w) > 3]
            
            if relevant_words:
                word_idx = scene_index % max(1, len(relevant_words))
                search_parts.append(relevant_words[word_idx])
                
                if len(relevant_words) > 1:
                    word_idx2 = (scene_index + 1) % len(relevant_words)
                    if word_idx2 != word_idx:
                        search_parts.append(relevant_words[word_idx2])
        
        if len(search_parts) <= 2:
            variation = self.scene_variations[scene_index % len(self.scene_variations)]
            search_parts.append(variation)
        
        if len(search_parts) <= 1:
            topic_words = topic.lower().split()[:2]
            search_parts.extend(topic_words)
            variation = self.scene_variations[scene_index % len(self.scene_variations)]
            search_parts.append(variation)
        
        return " ".join(search_parts)
    
    def search_tenor(self, query: str, limit: int = 20) -> list:
        """Busca GIFs/MP4 no Tenor"""
        if not self.tenor_key:
            return []
        
        try:
            url = "https://tenor.googleapis.com/v2/search"
            params = {
                "q": query,
                "key": self.tenor_key,
                "limit": limit,
                "media_filter": "mp4,gif",
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
    
    def search_tenor_stickers(self, query: str, limit: int = 20) -> list:
        """Busca especificamente stickers no Tenor"""
        if not self.tenor_key:
            return []
        
        try:
            url = "https://tenor.googleapis.com/v2/search"
            params = {
                "q": query,
                "key": self.tenor_key,
                "limit": limit,
                "searchfilter": "sticker",
                "media_filter": "mp4,gif,tinygif"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json().get("results", [])
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar stickers: {e}")
            return []
    
    def search_pixabay(self, query: str, limit: int = 10, orientation: str = "vertical") -> list:
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
    
    def download_tenor_media(self, result: dict, output_path: str) -> dict:
        """
        Baixa mídia do Tenor COM VALIDAÇÃO
        Tenta múltiplos formatos se um falhar
        """
        try:
            media_formats = result.get("media_formats", {})
            
            # Lista de formatos em ordem de preferência
            format_priority = [
                ("mp4", "mp4"),
                ("gif", "gif"),
                ("mediumgif", "gif"),
                ("tinygif", "gif"),
                ("nanogif", "gif"),
            ]
            
            for format_key, ext in format_priority:
                if format_key not in media_formats:
                    continue
                
                media_url = media_formats[format_key].get("url")
                if not media_url:
                    continue
                
                final_path = output_path.rsplit(".", 1)[0] + f".{ext}"
                
                try:
                    response = requests.get(media_url, timeout=60)
                    
                    if response.status_code != 200:
                        continue
                    
                    # Verifica se recebeu dados
                    if len(response.content) < 500:
                        print(f"      ⚠️ Formato {format_key}: resposta muito pequena")
                        continue
                    
                    # Salva o arquivo
                    with open(final_path, "wb") as f:
                        f.write(response.content)
                    
                    # VALIDA o arquivo baixado
                    if self.validate_media_file(final_path):
                        return {
                            "path": final_path,
                            "type": ext,
                            "id": result.get("id"),
                            "source": "tenor",
                            "format_used": format_key
                        }
                    else:
                        # Remove arquivo inválido e tenta próximo formato
                        print(f"      🗑️ Formato {format_key} inválido, tentando outro...")
                        try:
                            os.remove(final_path)
                        except:
                            pass
                        continue
                        
                except requests.exceptions.Timeout:
                    print(f"      ⚠️ Timeout no formato {format_key}")
                    continue
                except Exception as e:
                    print(f"      ⚠️ Erro com formato {format_key}: {e}")
                    continue
            
            # Nenhum formato funcionou
            return None
            
        except Exception as e:
            logger.error(f"Erro ao baixar do Tenor: {e}")
            return None
    
    def download_pixabay_image(self, result: dict, output_path: str) -> dict:
        """Baixa imagem do Pixabay com validação"""
        try:
            # Tenta diferentes tamanhos
            url_options = [
                result.get("largeImageURL"),
                result.get("webformatURL"),
                result.get("previewURL"),
            ]
            
            for image_url in url_options:
                if not image_url:
                    continue
                
                final_path = output_path.rsplit(".", 1)[0] + ".jpg"
                
                try:
                    response = requests.get(image_url, timeout=60)
                    
                    if response.status_code != 200:
                        continue
                    
                    with open(final_path, "wb") as f:
                        f.write(response.content)
                    
                    # Valida
                    if self.validate_media_file(final_path):
                        return {
                            "path": final_path,
                            "type": "image",
                            "id": result.get("id"),
                            "source": "pixabay"
                        }
                    else:
                        try:
                            os.remove(final_path)
                        except:
                            pass
                        continue
                        
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao baixar do Pixabay: {e}")
            return None
    
    def get_media_for_scenes(
        self,
        topic: str,
        prompts: list,
        output_dir: str,
        style: str = "tenor_sticker",
        send_log_callback=None
    ) -> list:
        """
        Busca e baixa mídias para cada cena do vídeo
        v4.5: Com validação de arquivos baixados
        """
        media_files = []
        os.makedirs(output_dir, exist_ok=True)
        
        used_ids = set()
        used_search_terms = set()
        failed_scenes = []
        
        for i, prompt in enumerate(prompts):
            # ===== TRATA DICT OU STRING =====
            if isinstance(prompt, dict):
                descricao = prompt.get("descricao", f"Cena {i+1}")
                search_term = prompt.get("busca_tenor", None)
                emocao = prompt.get("emocao", "neutral")
            else:
                descricao = str(prompt)
                search_term = None
                emocao = "neutral"
            
            print(f"\n  📍 Cena {i+1}/{len(prompts)}")
            print(f"    📝 Descrição: {descricao[:60]}...")
            
            media_info = None
            attempts = 0
            max_attempts = 4  # Aumentado para ter mais chances
            
            while media_info is None and attempts < max_attempts:
                attempts += 1
                
                # Primeira tentativa: usa termo da IA
                # Demais tentativas: gera novos termos
                if search_term and attempts == 1:
                    current_search = search_term
                else:
                    current_search = self.generate_search_term(
                        prompt=descricao, 
                        topic=topic, 
                        style=style, 
                        scene_index=i + (attempts - 1) * 10
                    )
                
                # Evita termos repetidos
                original_term = current_search
                term_attempt = 0
                while current_search in used_search_terms and term_attempt < 5:
                    term_attempt += 1
                    variation = self.scene_variations[(i + term_attempt) % len(self.scene_variations)]
                    current_search = f"{original_term} {variation}"
                
                used_search_terms.add(current_search)
                
                print(f"    🔍 Busca ({attempts}/{max_attempts}): '{current_search}'")
                
                # Decide qual tipo de busca fazer
                use_stickers = style in ["tenor_sticker", "stickman", "stickman_cute"]
                
                if use_stickers:
                    results = self.search_tenor_stickers(current_search, limit=25)
                else:
                    results = self.search_tenor(current_search, limit=25)
                
                # Filtra IDs já usados
                available_results = [r for r in results if r.get("id") not in used_ids]
                
                print(f"    📊 Resultados: {len(results)} total, {len(available_results)} disponíveis")
                
                if not available_results:
                    if attempts < max_attempts:
                        print(f"    ⚠️ Sem resultados novos, tentando busca diferente...")
                        search_term = None  # Força gerar novo termo
                    continue
                
                # Tenta baixar resultados até conseguir um válido
                for result in available_results:
                    result_id = result.get("id")
                    
                    if result_id in used_ids:
                        continue
                    
                    temp_path = os.path.join(output_dir, f"media_{i+1:02d}")
                    media_info = self.download_tenor_media(result, temp_path)
                    
                    if media_info:
                        used_ids.add(result_id)
                        format_used = media_info.get('format_used', media_info['type'])
                        print(f"    ✅ Baixado: {media_info['type'].upper()} ({format_used}) - ID: {result_id[:8]}...")
                        break
                    else:
                        # Marca ID como usado mesmo se falhou para não tentar de novo
                        used_ids.add(result_id)
                
                if not media_info and attempts < max_attempts:
                    print(f"    ⚠️ Downloads falharam, tentando nova busca...")
                    search_term = None
            
            # Fallback: Pixabay se Tenor falhou completamente
            if not media_info and self.pixabay_key:
                print(f"    🔄 Fallback: Pixabay...")
                
                # Usa termo mais genérico para Pixabay
                pixabay_terms = [
                    current_search.replace("stick figure", "illustration"),
                    f"illustration {topic}",
                    topic,
                ]
                
                for px_term in pixabay_terms:
                    if media_info:
                        break
                        
                    pixabay_results = self.search_pixabay(px_term, limit=10)
                    available_pixabay = [r for r in pixabay_results if f"px_{r.get('id')}" not in used_ids]
                    
                    for result in available_pixabay:
                        temp_path = os.path.join(output_dir, f"media_{i+1:02d}")
                        media_info = self.download_pixabay_image(result, temp_path)
                        
                        if media_info:
                            used_ids.add(f"px_{result.get('id')}")
                            print(f"    ✅ Pixabay: imagem válida")
                            break
            
            # Resultado final para esta cena
            if media_info:
                media_files.append(media_info["path"])
            else:
                failed_scenes.append(i + 1)
                print(f"    ❌ FALHA: Nenhuma mídia válida para cena {i+1}")
        
        # Resumo final
        print(f"\n  {'='*40}")
        print(f"  📊 RESUMO DO DOWNLOAD:")
        print(f"  ✅ Sucesso: {len(media_files)}/{len(prompts)} mídias")
        print(f"  🔢 IDs únicos usados: {len(used_ids)}")
        
        if failed_scenes:
            print(f"  ❌ Cenas sem mídia: {failed_scenes}")
        
        return media_files


# ===========================================
# CONFIGURAÇÕES DISPONÍVEIS - v4.5
# ===========================================

VIDEO_FORMATS = {
    "short": {
        "name": "📱 Short/Reels (30s)", 
        "width": 1080, 
        "height": 1920, 
        "desc": "Vertical 9:16",
        "duration": 30,
        "min_scenes": 4,
        "max_scenes": 8,
        "default_scenes": 6,
        "seconds_per_scene": 5,
        "is_short": True,  # ← NOVO: Flag para identificar shorts
    },
    "short_60": {
        "name": "📱 Short 60s", 
        "width": 1080, 
        "height": 1920, 
        "desc": "Vertical 60 segundos",
        "duration": 60,
        "min_scenes": 8,
        "max_scenes": 15,
        "default_scenes": 12,
        "seconds_per_scene": 5,
        "is_short": True,  # ← NOVO
    },
    "youtube_vertical": {
        "name": "📺 YouTube Vertical (3min)", 
        "width": 1080, 
        "height": 1920, 
        "desc": "Vertical longo ~3 min",
        "duration": 180,
        "min_scenes": 25,
        "max_scenes": 45,
        "default_scenes": 36,
        "seconds_per_scene": 5,
        "is_short": False,  # ← NOVO
    },
    "youtube": {
        "name": "📺 YouTube Horizontal (3min)", 
        "width": 1920, 
        "height": 1080, 
        "desc": "Horizontal 16:9 ~3 min",
        "duration": 180,
        "min_scenes": 25,
        "max_scenes": 45,
        "default_scenes": 36,
        "seconds_per_scene": 5,
        "is_short": False,  # ← NOVO
    },
    "youtube_5min": {
        "name": "📺 YouTube 5min", 
        "width": 1920, 
        "height": 1080, 
        "desc": "Horizontal ~5 min",
        "duration": 300,
        "min_scenes": 40,
        "max_scenes": 75,
        "default_scenes": 60,
        "seconds_per_scene": 5,
        "is_short": False,  # ← NOVO
    },
    "square": {
        "name": "⬜ Quadrado (60s)", 
        "width": 1080, 
        "height": 1080, 
        "desc": "Instagram 1:1",
        "duration": 60,
        "min_scenes": 8,
        "max_scenes": 15,
        "default_scenes": 12,
        "seconds_per_scene": 5,
        "is_short": True,  # ← NOVO
    },
}

IMAGE_STYLE_OPTIONS = {
    # === OPÇÕES DO TENOR (ANIMADAS) ===
    "tenor_sticker": {"name": "🎭 Stickman Animado", "desc": "Stick figures animados", "source": "tenor"},
    "tenor_gif": {"name": "📸 GIF Geral", "desc": "GIFs variados", "source": "tenor"},
    "tenor_meme": {"name": "😂 Meme/Reação", "desc": "Memes e reações", "source": "tenor"},
    
    # === OPÇÕES DE IA (EXISTENTES) ===
    "stickman": {"name": "🖤 Palitinho IA", "desc": "Fundo preto, linhas brancas", "source": "ai"},
    "stickman_cute": {"name": "🥰 Palitinho Fofo IA", "desc": "Mais expressivo", "source": "ai"},
    "stickman_comic": {"name": "📰 Palitinho Comic IA", "desc": "Estilo xkcd", "source": "ai"},
    "whiteboard": {"name": "📋 Quadro Branco", "desc": "Fundo branco", "source": "ai"},
    "chalkboard": {"name": "📗 Lousa", "desc": "Estilo giz", "source": "ai"},
    "cartoon": {"name": "🎨 Cartoon", "desc": "Estilo Pixar/Disney", "source": "ai"},
    "anime": {"name": "🇯🇵 Anime", "desc": "Estilo japonês", "source": "ai"},
    "realistic": {"name": "📷 Realista", "desc": "Fotorrealista", "source": "ai"},
    "sketch": {"name": "✏️ Sketch", "desc": "Desenho a lápis", "source": "ai"},
    "watercolor": {"name": "🖌️ Aquarela", "desc": "Pintura suave", "source": "ai"},
    "comic": {"name": "💥 Comic", "desc": "Quadrinhos", "source": "ai"},
    "3d": {"name": "🎮 3D", "desc": "Render 3D", "source": "ai"},
    "cinematic": {"name": "🎬 Cinematic", "desc": "Estilo filme", "source": "ai"},
}

VOICE_OPTIONS = {
    "pt-BR-AntonioNeural": {"name": "🧔 Antonio", "gender": "Masculino", "lang": "PT-BR"},
    "pt-BR-FranciscaNeural": {"name": "👩 Francisca", "gender": "Feminino", "lang": "PT-BR"},
    "pt-BR-ThalitaNeural": {"name": "👧 Thalita", "gender": "Feminino", "lang": "PT-BR"},
    "pt-BR-BrendaNeural": {"name": "👩‍🦰 Brenda", "gender": "Feminino", "lang": "PT-BR"},
    "pt-BR-DonatoNeural": {"name": "👨‍🦳 Donato", "gender": "Masculino", "lang": "PT-BR"},
    "pt-BR-ElzaNeural": {"name": "👵 Elza", "gender": "Feminino", "lang": "PT-BR"},
    "pt-BR-FabioNeural": {"name": "👨 Fabio", "gender": "Masculino", "lang": "PT-BR"},
    "pt-BR-GiovannaNeural": {"name": "👩‍🎤 Giovanna", "gender": "Feminino", "lang": "PT-BR"},
    "pt-BR-HumbertoNeural": {"name": "🧔‍♂️ Humberto", "gender": "Masculino", "lang": "PT-BR"},
}

SPEED_OPTIONS = {
    "0.8": {"name": "🐢 Lenta", "desc": "80% velocidade"},
    "0.9": {"name": "🚶 Devagar", "desc": "90% velocidade"},
    "1.0": {"name": "🏃 Normal", "desc": "100% velocidade"},
    "1.1": {"name": "🏃‍♂️ Rápida", "desc": "110% velocidade"},
    "1.2": {"name": "⚡ Muito Rápida", "desc": "120% velocidade"},
}


# ===========================================
# FUNÇÕES AUXILIARES DE ÁUDIO
# ===========================================

def get_audio_sample_rate(audio_path: str) -> int:
    """Obtém o sample rate do áudio usando ffprobe"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True)
        
        if result.stdout.strip():
            return int(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Erro ao obter sample rate: {e}")
    
    return 0


def normalize_audio(audio_path: str, target_sample_rate: int = 44100) -> str:
    """Normaliza o áudio para evitar problemas de velocidade no vídeo."""
    try:
        current_rate = get_audio_sample_rate(audio_path)
        
        print(f"  🔍 Sample rate atual: {current_rate} Hz")
        
        if current_rate == target_sample_rate:
            print(f"  ✓ Áudio já está em {target_sample_rate} Hz")
            return audio_path
        
        if current_rate == 0:
            print(f"  ⚠️ Não foi possível detectar sample rate, normalizando...")
        else:
            print(f"  🔄 Convertendo {current_rate} Hz -> {target_sample_rate} Hz...")
        
        normalized_path = audio_path.replace('.mp3', '_normalized.mp3')
        
        if os.path.exists(normalized_path):
            os.remove(normalized_path)
        
        result = subprocess.run([
            'ffmpeg', '-y',
            '-i', audio_path,
            '-ar', str(target_sample_rate),
            '-ac', '2',
            '-b:a', '192k',
            '-acodec', 'libmp3lame',
            normalized_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Erro ffmpeg: {result.stderr}")
            print(f"  ❌ Erro na conversão, usando original")
            return audio_path
        
        if os.path.exists(normalized_path):
            new_rate = get_audio_sample_rate(normalized_path)
            print(f"  ✅ Áudio normalizado: {new_rate} Hz")
            return normalized_path
        else:
            print(f"  ❌ Arquivo normalizado não foi criado")
            return audio_path
            
    except Exception as e:
        logger.error(f"Erro ao normalizar áudio: {e}")
        print(f"  ❌ Erro na normalização: {e}")
        return audio_path


def get_audio_duration(audio_path: str) -> float:
    """Obtém a duração do áudio usando ffprobe"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True)
        
        if result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Erro ao obter duração: {e}")
    
    try:
        from moviepy.editor import AudioFileClip
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()
        return duration
    except:
        pass
    
    return 30.0

# ===========================================
# BOT PRINCIPAL - v4.5 CORRIGIDO
# ===========================================

class VideoBot:
    """Bot que gera vídeos e faz upload no YouTube - v4.5 CORRIGIDO"""
    
    def __init__(self):
        print("\n🤖 Inicializando VideoBot v4.5 (CORRIGIDO)...\n")
        
        # Geradores
        self.text_gen = TextGenerator(provider="groq")
        self.image_gen = None
        self.audio_gen = AudioGenerator()
        self.video_gen = VideoGenerator()
        
        # Sticker Downloader
        self.sticker_downloader = StickerDownloader()
        
        # YouTube
        self.youtube = YouTubeUploader()
        
        # Configurações padrão por usuário
        self.user_configs = {}
        
        # Jobs em andamento
        self.active_jobs = {}
        
        # Tópicos pendentes
        self.pending_topics = {}
        
        self._check_dependencies()
        
        print("✓ VideoBot v4.5 inicializado!\n")
    
    def _check_dependencies(self):
        """Verifica dependências"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✓ FFmpeg disponível")
            else:
                print("  ⚠️ FFmpeg pode ter problemas")
        except FileNotFoundError:
            print("  ❌ FFmpeg não encontrado!")
        
        if self.sticker_downloader.tenor_key:
            print("  ✓ Tenor API configurada")
        else:
            print("  ⚠️ Tenor API não configurada")
        
        if self.sticker_downloader.pixabay_key:
            print("  ✓ Pixabay API configurada")
        else:
            print("  ⚠️ Pixabay API não configurada (fallback)")
    
    # ===========================================
    # CONFIGURAÇÕES
    # ===========================================
    
    def get_default_config(self) -> dict:
        """Configuração padrão"""
        return {
            "format": "short",
            "style": "tenor_sticker",
            "voice": "pt-BR-AntonioNeural",
            "speed": "1.0",
            "images": "auto",
            "upload": True,
        }
    
    def get_user_config(self, chat_id: int) -> dict:
        if chat_id not in self.user_configs:
            self.user_configs[chat_id] = self.get_default_config()
        return self.user_configs[chat_id]
    
    def set_user_config(self, chat_id: int, key: str, value: str):
        """Define configuração - auto-ajusta cenas quando muda formato"""
        if chat_id not in self.user_configs:
            self.user_configs[chat_id] = self.get_default_config()
        
        self.user_configs[chat_id][key] = value
        
        # Auto-ajuste quando muda formato
        if key == "format":
            current_images = self.user_configs[chat_id].get("images", "auto")
            format_config = VIDEO_FORMATS.get(value, VIDEO_FORMATS["short"])
            
            min_scenes = format_config.get("min_scenes", 4)
            max_scenes = format_config.get("max_scenes", 10)
            default_scenes = format_config.get("default_scenes", 6)
            
            if current_images != "auto":
                try:
                    current_val = int(current_images)
                    if current_val < min_scenes or current_val > max_scenes:
                        self.user_configs[chat_id]["images"] = "auto"
                        print(f"  ⚙️ Cenas ajustadas para 'auto' ({default_scenes})")
                except:
                    self.user_configs[chat_id]["images"] = "auto"
    
    def get_scenes_for_format(self, format_key: str) -> int:
        """Retorna número ideal de cenas para o formato"""
        format_config = VIDEO_FORMATS.get(format_key, VIDEO_FORMATS["short"])
        return format_config.get("default_scenes", 6)
    
    def get_effective_scenes(self, chat_id: int) -> int:
        """Retorna número efetivo de cenas (resolve 'auto')"""
        config = self.get_user_config(chat_id)
        images_setting = config.get("images", "auto")
        format_key = config.get("format", "short")
        
        if images_setting == "auto":
            return self.get_scenes_for_format(format_key)
        else:
            try:
                return int(images_setting)
            except:
                return self.get_scenes_for_format(format_key)
    
    def get_scene_options_for_format(self, format_key: str) -> dict:
        """Retorna opções de cenas válidas para o formato"""
        format_config = VIDEO_FORMATS.get(format_key, VIDEO_FORMATS["short"])
        
        min_scenes = format_config.get("min_scenes", 4)
        max_scenes = format_config.get("max_scenes", 10)
        default_scenes = format_config.get("default_scenes", 6)
        duration = format_config.get("duration", 30)
        
        options = {
            "auto": {
                "name": f"🤖 Auto ({default_scenes})", 
                "desc": f"Ideal para {self._format_duration(duration)}",
                "value": default_scenes
            }
        }
        
        scene_values = []
        scene_values.append(min_scenes)
        
        if max_scenes - min_scenes > 10:
            step = (max_scenes - min_scenes) // 4
            for i in range(1, 4):
                val = min_scenes + (step * i)
                scene_values.append(val)
        else:
            step = max(1, (max_scenes - min_scenes) // 3)
            current = min_scenes + step
            while current < max_scenes:
                scene_values.append(current)
                current += step
        
        scene_values.append(default_scenes)
        scene_values.append(max_scenes)
        
        scene_values = sorted(set(scene_values))
        
        for val in scene_values:
            secs_per_scene = duration / val
            is_default = val == default_scenes
            
            options[str(val)] = {
                "name": f"{'⭐' if is_default else '🔢'} {val} cenas",
                "desc": f"~{secs_per_scene:.0f}s cada",
                "value": val
            }
        
        return options
    
    def _format_duration(self, seconds: int) -> str:
        """Formata duração em texto legível"""
        if seconds >= 60:
            mins = seconds // 60
            secs = seconds % 60
            if secs > 0:
                return f"{mins}min{secs}s"
            return f"{mins}min"
        return f"{seconds}s"
    
    def is_tenor_style(self, style: str) -> bool:
        style_config = IMAGE_STYLE_OPTIONS.get(style, {})
        return style_config.get("source") == "tenor"
    
    async def is_authorized(self, user_id: int) -> bool:
        if not AUTHORIZED_USERS or AUTHORIZED_USERS == ['']:
            return True
        return str(user_id) in AUTHORIZED_USERS
    
    # ===========================================
    # COMANDOS
    # ===========================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not await self.is_authorized(user.id):
            await update.message.reply_text(
                f"❌ Acesso negado.\n\nSeu ID: `{user.id}`",
                parse_mode='Markdown'
            )
            return
        
        chat_id = update.effective_chat.id
        config = self.get_user_config(chat_id)
        format_config = VIDEO_FORMATS.get(config['format'], {})
        effective_scenes = self.get_effective_scenes(chat_id)
        
        welcome = f"""
👋 Olá, **{user.first_name}**!

🎬 **Bot de Vídeos Automáticos v4.5**

✨ **Novidades:**
• GIFs animados do Tenor!
• 🆕 Cenas automáticas por formato!
• ✅ Correção de vídeos longos!
• Suporte a vídeos longos (3-5 min)

📝 **Comandos:**
• `/config` - Configurações
• `/video [assunto]` - Gerar + upload
• `/preview [assunto]` - Só gerar
• `/help` - Ajuda completa

⚙️ **Configuração atual:**
• Formato: {format_config.get('name', 'Short')}
• Duração: ~{self._format_duration(format_config.get('duration', 30))}
• Cenas: {effective_scenes} (auto)
• Estilo: {IMAGE_STYLE_OPTIONS[config['style']]['name']}

💡 **Dica:** Envie o assunto direto!
        """
        
        await update.message.reply_text(welcome, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📚 **GUIA COMPLETO v4.5**

━━━━━━━━━━━━━━━━━━━━━━

🎬 **GERAR VÍDEOS**

`/video [assunto]` - Gera e faz upload
`/preview [assunto]` - Gera sem upload

━━━━━━━━━━━━━━━━━━━━━━

⚙️ **CONFIGURAÇÕES**

`/config` - Menu de configurações
`/format` - Formato do vídeo
`/style` - Estilo de imagem
`/voice` - Voz da narração
`/speed` - Velocidade
`/images` - Quantidade de cenas

━━━━━━━━━━━━━━━━━━━━━━

📱 **FORMATOS DISPONÍVEIS:**
• Short 30s (6 cenas) - YouTube Shorts
• Short 60s (12 cenas) - YouTube Shorts
• YouTube Vertical 3min (36 cenas)
• YouTube Horizontal 3min (36 cenas)
• YouTube 5min (60 cenas)
• Quadrado 60s (12 cenas)

━━━━━━━━━━━━━━━━━━━━━━

🎨 **ESTILOS ANIMADOS (Tenor):**
• 🎭 Stickman Animado (recomendado!)
• 📸 GIF Geral
• 😂 Meme/Reação

💡 As cenas são ajustadas automaticamente
quando você muda o formato!
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        config = self.get_user_config(chat_id)
        format_config = VIDEO_FORMATS.get(config['format'], {})
        effective_scenes = self.get_effective_scenes(chat_id)
        
        images_display = config.get('images', 'auto')
        if images_display == 'auto':
            images_display = f"🤖 Auto ({effective_scenes})"
        else:
            images_display = f"{images_display} cenas"
        
        keyboard = [
            [InlineKeyboardButton(
                f"📱 Formato: {format_config.get('name', 'Short')}", 
                callback_data="menu:format"
            )],
            [InlineKeyboardButton(
                f"🎨 Estilo: {IMAGE_STYLE_OPTIONS[config['style']]['name']}", 
                callback_data="menu:style"
            )],
            [InlineKeyboardButton(
                f"🎤 Voz: {VOICE_OPTIONS[config['voice']]['name']}", 
                callback_data="menu:voice"
            )],
            [InlineKeyboardButton(
                f"⏱️ Velocidade: {SPEED_OPTIONS[config['speed']]['name']}", 
                callback_data="menu:speed"
            )],
            [InlineKeyboardButton(
                f"🖼️ Cenas: {images_display}", 
                callback_data="menu:images"
            )],
            [InlineKeyboardButton("🔄 Resetar", callback_data="menu:reset")],
        ]
        
        duration_text = self._format_duration(format_config.get('duration', 30))
        
        await update.message.reply_text(
            f"⚙️ **CONFIGURAÇÕES**\n\n"
            f"📱 Formato atual: **{format_config.get('name', 'Short')}**\n"
            f"⏱️ Duração: **~{duration_text}**\n"
            f"🖼️ Cenas: **{effective_scenes}** (~{format_config.get('seconds_per_scene', 5)}s cada)\n\n"
            f"Clique para alterar:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def cmd_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_format_menu(update.message, update.effective_chat.id)
    
    async def cmd_style(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_style_menu(update.message, update.effective_chat.id)
    
    async def cmd_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_voice_menu(update.message, update.effective_chat.id)
    
    async def cmd_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_speed_menu(update.message, update.effective_chat.id)
    
    async def cmd_images(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_images_menu(update.message, update.effective_chat.id)
    
    async def cmd_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_configs[update.effective_chat.id] = self.get_default_config()
        await update.message.reply_text("✅ Configurações resetadas para padrão!")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        
        if chat_id not in self.active_jobs:
            await update.message.reply_text("📊 Nenhum job em andamento.")
            return
        
        job = self.active_jobs[chat_id]
        await update.message.reply_text(
            f"📊 **Job em andamento:**\n\n"
            f"📝 Assunto: {job['topic']}\n"
            f"⏳ Status: {job['status']}\n"
            f"🕐 Iniciado: {job['started']}",
            parse_mode='Markdown'
        )
    
    async def cmd_auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔐 Verificando YouTube...")
        
        try:
            if self.youtube.authenticate():
                await update.message.reply_text("✅ YouTube autenticado!")
            else:
                await update.message.reply_text("❌ Falha na autenticação.")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro: {str(e)[:200]}")
    
    async def cmd_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("📝 Use: `/video [assunto]`", parse_mode='Markdown')
            return
        
        topic = " ".join(context.args)
        self.set_user_config(update.effective_chat.id, "upload", True)
        await self.show_config_summary(update.message, update.effective_chat.id, topic)
    
    async def cmd_preview(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("📝 Use: `/preview [assunto]`", parse_mode='Markdown')
            return
        
        topic = " ".join(context.args)
        self.set_user_config(update.effective_chat.id, "upload", False)
        await self.show_config_summary(update.message, update.effective_chat.id, topic)
    
    # ===========================================
    # MENUS
    # ===========================================
    
    async def show_format_menu(self, message, chat_id: int):
        """Menu de formato - mostra duração e cenas"""
        config = self.get_user_config(chat_id)
        
        keyboard = []
        for key, value in VIDEO_FORMATS.items():
            marker = " ✓" if key == config['format'] else ""
            duration = value.get('duration', 30)
            scenes = value.get('default_scenes', 6)
            duration_text = self._format_duration(duration)
            
            keyboard.append([InlineKeyboardButton(
                f"{value['name']}{marker}", 
                callback_data=f"set:format:{key}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Voltar", callback_data="menu:back")])
        
        await message.reply_text(
            "📱 **FORMATO DO VÍDEO**\n\n"
            "Escolha o formato - as cenas serão ajustadas automaticamente:\n\n"
            "📱 **Shorts:** 30s (6 cenas) ou 60s (12 cenas)\n"
            "📺 **YouTube:** 3min (36 cenas) ou 5min (60 cenas)\n"
            "⬜ **Quadrado:** 60s (12 cenas)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_style_menu(self, message, chat_id: int):
        config = self.get_user_config(chat_id)
        
        keyboard = []
        
        # Seção Tenor (Animados)
        keyboard.append([InlineKeyboardButton("═══ 🎭 ANIMADOS (Tenor) ═══", callback_data="noop")])
        row = []
        for key, value in IMAGE_STYLE_OPTIONS.items():
            if value.get("source") == "tenor":
                marker = " ✓" if key == config['style'] else ""
                row.append(InlineKeyboardButton(
                    f"{value['name']}{marker}", 
                    callback_data=f"set:style:{key}"
                ))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        if row:
            keyboard.append(row)
        
        # Seção IA
        keyboard.append([InlineKeyboardButton("═══ 🤖 IA (Geradas) ═══", callback_data="noop")])
        row = []
        for key, value in IMAGE_STYLE_OPTIONS.items():
            if value.get("source") == "ai":
                marker = " ✓" if key == config['style'] else ""
                row.append(InlineKeyboardButton(
                    f"{value['name']}{marker}", 
                    callback_data=f"set:style:{key}"
                ))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("◀️ Voltar", callback_data="menu:back")])
        
        await message.reply_text(
            "🎨 **ESTILO DE IMAGEM**\n\n"
            "🎭 **Animados:** GIFs do Tenor (rápido!)\n"
            "🤖 **IA:** Geradas (mais lento)\n\n"
            "⭐ Recomendado: **Stickman Animado**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_voice_menu(self, message, chat_id: int):
        config = self.get_user_config(chat_id)
        
        keyboard = []
        for key, value in VOICE_OPTIONS.items():
            marker = " ✓" if key == config['voice'] else ""
            keyboard.append([InlineKeyboardButton(
                f"{value['name']}{marker} ({value['gender']})", 
                callback_data=f"set:voice:{key}"
            )])
        keyboard.append([InlineKeyboardButton("◀️ Voltar", callback_data="menu:back")])
        
        await message.reply_text(
            "🎤 **VOZ DA NARRAÇÃO**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_speed_menu(self, message, chat_id: int):
        config = self.get_user_config(chat_id)
        
        keyboard = []
        for key, value in SPEED_OPTIONS.items():
            marker = " ✓" if key == config['speed'] else ""
            keyboard.append([InlineKeyboardButton(
                f"{value['name']}{marker} - {value['desc']}", 
                callback_data=f"set:speed:{key}"
            )])
        keyboard.append([InlineKeyboardButton("◀️ Voltar", callback_data="menu:back")])
        
        await message.reply_text(
            "⏱️ **VELOCIDADE DA FALA**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_images_menu(self, message, chat_id: int):
        """Menu de cenas - DINÂMICO baseado no formato"""
        config = self.get_user_config(chat_id)
        format_key = config.get("format", "short")
        current_images = config.get("images", "auto")
        
        options = self.get_scene_options_for_format(format_key)
        format_config = VIDEO_FORMATS.get(format_key, {})
        
        keyboard = []
        
        for key, value in options.items():
            marker = " ✓" if key == current_images else ""
            keyboard.append([InlineKeyboardButton(
                f"{value['name']}{marker} - {value['desc']}", 
                callback_data=f"set:images:{key}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Voltar", callback_data="menu:back")])
        
        duration = format_config.get("duration", 30)
        duration_text = self._format_duration(duration)
        
        await message.reply_text(
            f"🖼️ **QUANTIDADE DE CENAS**\n\n"
            f"📱 Formato atual: **{format_config.get('name', 'Short')}**\n"
            f"⏱️ Duração estimada: **{duration_text}**\n\n"
            f"💡 _Recomendado: ~5 segundos por cena_\n"
            f"⭐ _'Auto' ajusta automaticamente_",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_config_summary(self, message, chat_id: int, topic: str):
        """Resumo antes de gerar - mostra info completa"""
        config = self.get_user_config(chat_id)
        self.pending_topics[chat_id] = topic
        
        upload_text = "✅ Sim" if config.get('upload', True) else "❌ Não"
        
        style_info = IMAGE_STYLE_OPTIONS.get(config['style'], {})
        source_emoji = "🎭" if style_info.get("source") == "tenor" else "🤖"
        source_text = "Animado" if style_info.get("source") == "tenor" else "IA"
        
        format_config = VIDEO_FORMATS.get(config['format'], {})
        duration = format_config.get("duration", 30)
        duration_text = self._format_duration(duration)
        
        effective_scenes = self.get_effective_scenes(chat_id)
        images_setting = config.get("images", "auto")
        
        if images_setting == "auto":
            scenes_text = f"🤖 Auto ({effective_scenes})"
        else:
            scenes_text = f"{effective_scenes}"
        
        secs_per_scene = duration / effective_scenes if effective_scenes > 0 else 5
        
        # ✅ CORREÇÃO: Mostra se é Short ou vídeo longo
        is_short = format_config.get("is_short", True)
        video_type_text = "📱 YouTube Short" if is_short else "📺 Vídeo Longo"
        
        keyboard = [
            [InlineKeyboardButton("📱 Formato", callback_data="cfg:format"),
             InlineKeyboardButton("🎨 Estilo", callback_data="cfg:style")],
            [InlineKeyboardButton("🎤 Voz", callback_data="cfg:voice"),
             InlineKeyboardButton("⏱️ Velocidade", callback_data="cfg:speed")],
            [InlineKeyboardButton("🖼️ Cenas", callback_data="cfg:images"),
             InlineKeyboardButton("📤 Upload", callback_data="cfg:upload")],
            [InlineKeyboardButton("🎬 GERAR VÍDEO!", callback_data="generate:start")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="generate:cancel")],
        ]
        
        summary = f"""
🎬 **PRONTO PARA GERAR!**

━━━━━━━━━━━━━━━━━━━━━━

📝 **Assunto:** {topic}

━━━━━━━━━━━━━━━━━━━━━━

📱 Formato: {format_config.get('name', 'Short')}
🎯 Tipo: **{video_type_text}**
⏱️ Duração: ~{duration_text}
🎨 Estilo: {IMAGE_STYLE_OPTIONS[config['style']]['name']}
{source_emoji} Fonte: **{source_text}**
🎤 Voz: {VOICE_OPTIONS[config['voice']]['name']}
⚡ Velocidade: {SPEED_OPTIONS[config['speed']]['name']}
🖼️ Cenas: {scenes_text} (~{secs_per_scene:.1f}s cada)
📤 Upload: {upload_text}

━━━━━━━━━━━━━━━━━━━━━━
        """
        
        await message.reply_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ===========================================
    # HANDLERS
    # ===========================================
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        if not await self.is_authorized(user.id):
            return
        
        topic = update.message.text.strip()
        
        if len(topic) < 3:
            await update.message.reply_text("❌ Assunto muito curto.")
            return
        
        if len(topic) > 300:
            await update.message.reply_text("❌ Assunto muito longo (max 300).")
            return
        
        await self.show_config_summary(update.message, update.effective_chat.id, topic)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat.id
        data = query.data
        
        if data == "noop":
            return
        
        if data.startswith("menu:"):
            action = data.split(":")[1]
            
            if action == "format":
                await self.show_format_menu(query.message, chat_id)
            elif action == "style":
                await self.show_style_menu(query.message, chat_id)
            elif action == "voice":
                await self.show_voice_menu(query.message, chat_id)
            elif action == "speed":
                await self.show_speed_menu(query.message, chat_id)
            elif action == "images":
                await self.show_images_menu(query.message, chat_id)
            elif action == "reset":
                self.user_configs[chat_id] = self.get_default_config()
                await query.edit_message_text("✅ Configurações resetadas!")
            elif action == "back":
                await query.delete_message()
        
        elif data.startswith("set:"):
            parts = data.split(":")
            key = parts[1]
            value = parts[2]
            
            self.set_user_config(chat_id, key, value)
            
            if key == "format":
                format_config = VIDEO_FORMATS.get(value, {})
                new_scenes = self.get_effective_scenes(chat_id)
                duration_text = self._format_duration(format_config.get('duration', 30))
                is_short = format_config.get("is_short", True)
                type_text = "Short" if is_short else "Vídeo Longo"
                name = f"{format_config.get('name', value)}\n⏱️ Duração: {duration_text}\n🖼️ Cenas: {new_scenes}\n🎯 Tipo: {type_text}"
            elif key == "style":
                name = IMAGE_STYLE_OPTIONS[value]['name']
                source = IMAGE_STYLE_OPTIONS[value].get('source', 'ai')
                source_text = " (Animado)" if source == "tenor" else " (IA)"
                name += source_text
            elif key == "voice":
                name = VOICE_OPTIONS[value]['name']
            elif key == "speed":
                name = SPEED_OPTIONS[value]['name']
            elif key == "images":
                if value == "auto":
                    effective = self.get_effective_scenes(chat_id)
                    name = f"🤖 Automático ({effective} cenas)"
                else:
                    name = f"{value} cenas"
            else:
                name = value
            
            await query.edit_message_text(f"✅ **{key.title()}:** {name}", parse_mode='Markdown')
        
        elif data.startswith("cfg:"):
            action = data.split(":")[1]
            
            if action == "format":
                await self.show_format_menu(query.message, chat_id)
            elif action == "style":
                await self.show_style_menu(query.message, chat_id)
            elif action == "voice":
                await self.show_voice_menu(query.message, chat_id)
            elif action == "speed":
                await self.show_speed_menu(query.message, chat_id)
            elif action == "images":
                await self.show_images_menu(query.message, chat_id)
            elif action == "upload":
                config = self.get_user_config(chat_id)
                new_value = not config.get('upload', True)
                self.set_user_config(chat_id, 'upload', new_value)
                
                if chat_id in self.pending_topics:
                    await query.delete_message()
                    await self.show_config_summary(
                        query.message, 
                        chat_id, 
                        self.pending_topics[chat_id]
                    )
        
        elif data.startswith("generate:"):
            action = data.split(":")[1]
            
            if action == "cancel":
                if chat_id in self.pending_topics:
                    del self.pending_topics[chat_id]
                await query.edit_message_text("❌ Cancelado.")
            
            elif action == "start":
                if chat_id not in self.pending_topics:
                    await query.edit_message_text("❌ Erro: Nenhum assunto pendente.")
                    return
                
                topic = self.pending_topics[chat_id]
                config = self.get_user_config(chat_id)
                
                effective_scenes = self.get_effective_scenes(chat_id)
                format_config = VIDEO_FORMATS.get(config['format'], {})
                
                style_info = IMAGE_STYLE_OPTIONS.get(config['style'], {})
                source_text = "🎭 Animado" if style_info.get("source") == "tenor" else "🤖 IA"
                
                # ✅ CORREÇÃO: Pega is_short do formato
                is_short = format_config.get("is_short", True)
                type_text = "📱 Short" if is_short else "📺 Vídeo Longo"
                
                await query.edit_message_text(
                    f"🎬 **Iniciando geração...**\n\n"
                    f"📝 Assunto: {topic}\n"
                    f"📱 Formato: {format_config.get('name', 'Short')}\n"
                    f"🎯 Tipo: {type_text}\n"
                    f"🖼️ Cenas: {effective_scenes}\n"
                    f"🎨 Estilo: {IMAGE_STYLE_OPTIONS[config['style']]['name']}\n"
                    f"📸 Fonte: {source_text}",
                    parse_mode='Markdown'
                )
                
                del self.pending_topics[chat_id]
                
                # ✅ CORREÇÃO: Passa informações completas
                config['_effective_scenes'] = effective_scenes
                config['_target_duration'] = format_config.get('duration', 30)
                config['_is_short'] = is_short
                config['_width'] = format_config.get('width', 1080)
                config['_height'] = format_config.get('height', 1920)
                
                await self.process_video(query, topic, config)
    
    # ===========================================
    # PIPELINE DE GERAÇÃO - v4.5 CORRIGIDO
    # ===========================================
    
    async def process_video(self, query, topic: str, config: dict):
        """Pipeline completo de geração - CORRIGIDO v4.5"""
        
        chat_id = query.message.chat.id
        bot = query.message.get_bot()
        
        async def send_log(text: str):
            try:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Erro log: {e}")
        
        # ✅ CORREÇÃO: Extrai configurações passadas pelo handler
        video_format = config.get('format', 'short')
        style = config.get('style', 'tenor_sticker')
        voice = config.get('voice', 'pt-BR-AntonioNeural')
        speed = float(config.get('speed', '1.0'))
        upload = config.get('upload', True)
        
        # ✅ CORREÇÃO: Usa valores pré-calculados
        num_scenes = config.get('_effective_scenes', 6)
        target_duration = config.get('_target_duration', 30)
        is_short = config.get('_is_short', True)
        width = config.get('_width', 1080)
        height = config.get('_height', 1920)
        
        use_tenor = self.is_tenor_style(style)
        
        format_config = VIDEO_FORMATS.get(video_format, VIDEO_FORMATS["short"])
        
        start_time = datetime.now()
        
        self.active_jobs[chat_id] = {
            "topic": topic,
            "status": "Iniciando...",
            "started": start_time.strftime("%H:%M:%S")
        }
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_dir = OUTPUT_PROJECTS / timestamp
            project_dir.mkdir(parents=True, exist_ok=True)
            
            source_text = "🎭 Animado (Tenor)" if use_tenor else "🤖 IA"
            duration_text = self._format_duration(target_duration)
            type_text = "📱 YouTube Short" if is_short else "📺 Vídeo Longo"
            
            await send_log(
                f"🚀 **INICIANDO v4.5**\n\n"
                f"📝 Assunto: {topic}\n"
                f"📱 Formato: {format_config['name']}\n"
                f"🎯 Tipo: **{type_text}**\n"
                f"⏱️ Duração alvo: **~{duration_text}**\n"
                f"📐 Resolução: **{width}x{height}**\n"
                f"🎨 Estilo: {IMAGE_STYLE_OPTIONS[style]['name']}\n"
                f"📸 Fonte: {source_text}\n"
                f"🎤 Voz: {VOICE_OPTIONS[voice]['name']}\n"
                f"🖼️ Cenas: **{num_scenes}**\n"
                f"📂 Projeto: `{timestamp}`"
            )
            
            # ========== 1. ROTEIRO ==========
            self.active_jobs[chat_id]["status"] = "Gerando roteiro..."
            await send_log(
                f"📝 **[1/5] GERANDO ROTEIRO...**\n\n"
                f"🖼️ Gerando {num_scenes} cenas\n"
                f"⏱️ Duração alvo: {duration_text}"
            )
            
            # ✅ CORREÇÃO PRINCIPAL: Passa target_duration!
            script = self.text_gen.generate_short_script(
                topic=topic, 
                num_scenes=num_scenes,
                target_duration=target_duration  # ← CORREÇÃO!
            )
            
            narration = script.get("narracao", "")
            if not narration:
                narration = f"{script.get('hook', '')} {script.get('roteiro', '')} {script.get('cta', '')}"
            
            image_prompts = script.get("cenas", [])
            
            # Ajusta quantidade de cenas
            if len(image_prompts) < num_scenes:
                print(f"⚠️ Roteiro gerou {len(image_prompts)} cenas, precisamos de {num_scenes}")
                for i in range(len(image_prompts), num_scenes):
                    if isinstance(image_prompts[0], dict) if image_prompts else False:
                        image_prompts.append({
                            "descricao": f"Cena sobre {topic}, parte {i+1}",
                            "busca_tenor": f"stick figure thinking {i % 10}",
                            "emocao": "curious"
                        })
                    else:
                        image_prompts.append(f"Cena sobre {topic}, parte {i+1}")
            elif len(image_prompts) > num_scenes:
                image_prompts = image_prompts[:num_scenes]
            
            # Salva roteiro
            with open(project_dir / "script.txt", "w", encoding="utf-8") as f:
                f.write(f"TÍTULO: {script.get('titulo', '')}\n")
                f.write(f"NARRAÇÃO:\n{narration}\n")
                f.write(f"CENAS: {len(image_prompts)}\n")
                f.write(f"FORMATO: {format_config['name']}\n")
                f.write(f"RESOLUÇÃO: {width}x{height}\n")
                f.write(f"DURAÇÃO ALVO: {target_duration}s\n")
                f.write(f"É SHORT: {is_short}\n")
                f.write(f"TIPO: {'Tenor Animado' if use_tenor else 'IA'}\n")
            
            word_count = len(narration.split())
            estimated_duration = word_count / 2.5
            
            await send_log(
                f"✅ **ROTEIRO GERADO!**\n\n"
                f"📺 Título: {script.get('titulo', 'N/A')[:50]}...\n"
                f"📊 Palavras: {word_count}\n"
                f"⏱️ Duração estimada: ~{estimated_duration:.0f}s\n"
                f"🎬 Cenas: {len(image_prompts)}"
            )
            
            # ========== 2. MÍDIAS ==========
            self.active_jobs[chat_id]["status"] = "Buscando mídias..."
            
            media_files = []
            media_dir = project_dir / "media"
            media_dir.mkdir(parents=True, exist_ok=True)
            
            if use_tenor:
                await send_log(
                    f"🎭 **[2/5] BUSCANDO GIFs ANIMADOS...**\n\n"
                    f"🔍 {num_scenes} cenas\n"
                    f"🎨 Estilo: {IMAGE_STYLE_OPTIONS[style]['desc']}\n"
                    f"⚡ Buscas otimizadas (sem repetição)"
                )
                
                media_files = self.sticker_downloader.get_media_for_scenes(
                    topic=topic,
                    prompts=image_prompts,
                    output_dir=str(media_dir),
                    style=style
                )
                
                if len(media_files) > 10:
                    await send_log(f"✅ **{len(media_files)}/{num_scenes} GIFs baixados!**")
                else:
                    for i, path in enumerate(media_files):
                        file_ext = Path(path).suffix.upper().replace(".", "")
                        await send_log(f"✅ Cena {i+1}: {file_ext}")
                
                if len(media_files) < len(image_prompts):
                    await send_log(f"⚠️ {len(image_prompts) - len(media_files)} cenas faltando")
            
            else:
                await send_log(
                    f"🤖 **[2/5] GERANDO IMAGENS COM IA...**\n\n"
                    f"🎨 Estilo: {IMAGE_STYLE_OPTIONS[style]['name']}\n"
                    f"📐 Tamanho: {width}x{height}\n"
                    f"🖼️ Total: {num_scenes} imagens"
                )
                
                self.image_gen = ImageGenerator(style=style)
                
                for i, prompt in enumerate(image_prompts):
                    if isinstance(prompt, dict):
                        prompt_text = prompt.get("descricao", f"Cena {i+1}")
                    else:
                        prompt_text = prompt
                    
                    if i % 5 == 0 or i == len(image_prompts) - 1:
                        await send_log(f"🖼️ Gerando {i+1}/{len(image_prompts)}...")
                    
                    try:
                        save_path = media_dir / f"image_{i+1:02d}.png"
                        
                        # ✅ CORREÇÃO: Passa tamanho correto para IA
                        result = self.image_gen.generate(
                            prompt=prompt_text,
                            width=width,
                            height=height,
                            save_path=str(save_path)
                        )
                        
                        if result:
                            media_files.append(str(save_path))
                        
                    except Exception as e:
                        logger.error(f"Erro imagem {i+1}: {e}")
                    
                    if i < len(image_prompts) - 1:
                        await asyncio.sleep(2)
                
                await send_log(f"✅ **{len(media_files)}/{num_scenes} imagens geradas!**")
            
            # Verifica quantidade mínima
            min_media = max(3, num_scenes // 3)
            if len(media_files) < min_media:
                await send_log(f"❌ **Poucas mídias obtidas!** ({len(media_files)}/{min_media} mínimo)\nTente novamente.")
                del self.active_jobs[chat_id]
                return
            
            media_type = "GIFs/MP4" if use_tenor else "imagens"
            await send_log(f"✅ **{len(media_files)} {media_type} obtidos!**")
            
            # ========== 3. ÁUDIO ==========
            self.active_jobs[chat_id]["status"] = "Gerando áudio..."
            await send_log(
                f"🔊 **[3/5] GERANDO NARRAÇÃO...**\n\n"
                f"🎤 Voz: {VOICE_OPTIONS[voice]['name']}\n"
                f"⏱️ Velocidade: {speed}x\n"
                f"📊 Palavras: {word_count}\n"
                f"⏱️ Duração esperada: ~{estimated_duration:.0f}s"
            )
            
            audio_path_original = str(project_dir / "audio_original.mp3")
            
            self.audio_gen.generate(
                text=narration,
                output_path=audio_path_original,
                voice=voice,
                rate=speed
            )
            
            await send_log("🔧 **Normalizando áudio...**")
            
            audio_path = normalize_audio(audio_path_original, target_sample_rate=44100)
            audio_duration = get_audio_duration(audio_path)
            
            secs_per_scene = audio_duration / len(media_files)
            
            await send_log(
                f"✅ **ÁUDIO GERADO!**\n\n"
                f"⏱️ Duração: {audio_duration:.1f}s\n"
                f"🖼️ Por cena: ~{secs_per_scene:.1f}s"
            )
            
            # ========== 4. VÍDEO ==========
            self.active_jobs[chat_id]["status"] = "Montando vídeo..."
            await send_log(
                f"🎬 **[4/5] MONTANDO VÍDEO...**\n\n"
                f"🖼️ Mídias: {len(media_files)}\n"
                f"🔊 Áudio: {audio_duration:.1f}s\n"
                f"📐 Resolução: {width}x{height}\n"
                f"🎯 Tipo: {'Short' if is_short else 'Vídeo Longo'}"
            )
            
            # ✅ CORREÇÃO: Usa o formato correto para o VideoGenerator
            if is_short:
                video_path = self.video_gen.create_short(
                    images=media_files,
                    audio_path=audio_path,
                    output_name=timestamp,
                    subtitle_text=narration
                )
            else:
                # Para vídeos longos, usa create_slideshow com formato correto
                # Mapeia o formato do bot para o formato do VideoGenerator
                vg_format = "youtube" if width > height else "youtube_vertical"
                if width == height:
                    vg_format = "square"
                
                video_path = self.video_gen.create_slideshow(
                    images=media_files,
                    audio_path=audio_path,
                    output_name=timestamp,
                    format=vg_format,  # ← Passa formato correto
                    subtitle_text=narration
                )
            
            video_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
            
            await send_log(f"✅ **VÍDEO RENDERIZADO!** ({video_size_mb:.1f} MB)")
            
            # ========== 5. UPLOAD ==========
            if upload:
                self.active_jobs[chat_id]["status"] = "Fazendo upload..."
                
                # ✅ CORREÇÃO: Mostra tipo correto no log
                upload_type = "YouTube Shorts" if is_short else "YouTube (vídeo longo)"
                await send_log(f"📤 **[5/5] UPLOAD NO {upload_type.upper()}...**")
                
                yt_title = script.get("titulo", f"🔥 {topic.title()}")
                yt_tags = [tag.replace("#", "") for tag in script.get("hashtags", ["shorts", "viral"])]
                
                # ✅ CORREÇÃO PRINCIPAL: Usa is_short do formato, NÃO da duração do áudio!
                # is_short já foi definido no início baseado no formato escolhido
                
                # Determina categoria baseada no estilo
                if "educa" in topic.lower() or "aprend" in topic.lower():
                    category = "education"
                elif "engra" in topic.lower() or "humor" in topic.lower():
                    category = "comedy"
                else:
                    category = "entertainment"
                
                result = self.youtube.upload(
                    video_path=video_path,
                    title=yt_title,
                    description=script.get("descricao", f"Vídeo sobre {topic}"),
                    tags=yt_tags,
                    category=category,
                    privacy="public",
                    made_for_kids=False,
                    is_short=is_short,  # ← USA O VALOR CORRETO DO FORMATO!
                    language="pt-BR",
                    auto_thumbnail=not is_short  # Thumbnail só para vídeos longos
                )
                
                total_time = (datetime.now() - start_time).seconds
                
                if result:
                    await send_log(
                        f"🎉🎉🎉 **PUBLICADO!** 🎉🎉🎉\n\n"
                        f"📺 {yt_title[:50]}...\n\n"
                        f"🔗 **{result['url']}**\n\n"
                        f"🎯 Tipo: **{upload_type}**\n"
                        f"⏱️ Tempo total: {total_time//60}min {total_time%60}s\n"
                        f"🖼️ Cenas: {len(media_files)}\n"
                        f"📐 Resolução: {width}x{height}\n"
                        f"📂 Projeto: `{timestamp}`"
                    )
                else:
                    await send_log(
                        f"⚠️ **Upload falhou!**\n\n"
                        f"📂 Vídeo salvo em:\n`{video_path}`"
                    )
            else:
                total_time = (datetime.now() - start_time).seconds
                
                await send_log(
                    f"✅ **PREVIEW PRONTO!**\n\n"
                    f"⏱️ Tempo: {total_time//60}min {total_time%60}s\n"
                    f"🖼️ Cenas: {len(media_files)}\n"
                    f"📐 Resolução: {width}x{height}\n"
                    f"📂 Projeto: `{project_dir}`\n"
                    f"🎬 Vídeo: `{video_path}`"
                )
            
            # Limpa arquivo temporário
            if audio_path != audio_path_original and os.path.exists(audio_path_original):
                try:
                    os.remove(audio_path_original)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Erro: {e}")
            import traceback
            traceback.print_exc()
            await send_log(f"❌ **ERRO:** `{str(e)[:200]}`")
        
        finally:
            if chat_id in self.active_jobs:
                del self.active_jobs[chat_id]


# ===========================================
# MAIN
# ===========================================

def main():
    """Inicia o bot"""
    
    print("\n" + "="*50)
    print("CONTENT AUTOMATION BOT v4.5 - CORRIGIDO")
    print("GIFs Animados + Duração Correta + Formato Correto")
    print("="*50 + "\n")
    
    print_config_status()
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN não configurado!")
        return
    
    # Verifica APIs
    tenor_key = os.getenv("TENOR_API_KEY")
    pixabay_key = os.getenv("PIXABAY_API_KEY")
    
    print("\n📡 APIs de Imagens:")
    if tenor_key:
        print(f"  ✓ Tenor: {tenor_key[:15]}...")
    else:
        print("  ⚠️ Tenor não configurada")
    
    if pixabay_key:
        print(f"  ✓ Pixabay: {pixabay_key[:10]}...")
    else:
        print("  ⚠️ Pixabay não configurada (fallback)")
    
    # Mostra formatos disponíveis
    print("\n📱 Formatos disponíveis:")
    for key, config in VIDEO_FORMATS.items():
        duration = config.get('duration', 30)
        scenes = config.get('default_scenes', 6)
        is_short = config.get('is_short', True)
        type_text = "Short" if is_short else "Longo"
        resolution = f"{config.get('width', 1080)}x{config.get('height', 1920)}"
        print(f"  • {config['name']}: {duration}s, {scenes} cenas, {resolution} ({type_text})")
    
    bot = VideoBot()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", bot.cmd_start))
    app.add_handler(CommandHandler("help", bot.cmd_help))
    app.add_handler(CommandHandler("config", bot.cmd_config))
    app.add_handler(CommandHandler("format", bot.cmd_format))
    app.add_handler(CommandHandler("style", bot.cmd_style))
    app.add_handler(CommandHandler("voice", bot.cmd_voice))
    app.add_handler(CommandHandler("speed", bot.cmd_speed))
    app.add_handler(CommandHandler("images", bot.cmd_images))
    app.add_handler(CommandHandler("reset", bot.cmd_reset))
    app.add_handler(CommandHandler("status", bot.cmd_status))
    app.add_handler(CommandHandler("auth", bot.cmd_auth))
    app.add_handler(CommandHandler("video", bot.cmd_video))
    app.add_handler(CommandHandler("preview", bot.cmd_preview))
    
    # Callbacks e mensagens
    app.add_handler(CallbackQueryHandler(bot.handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("\n" + "="*50)
    print("✓ Bot iniciado!")
    print("  Aguardando mensagens no Telegram...")
    print("="*50 + "\n")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
"""
Configurações centralizadas do projeto
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env
load_dotenv()

# ===========================================
# PATHS
# ===========================================

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
OUTPUT_DIR = ROOT_DIR / "output"
ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"

# Subpastas de output
OUTPUT_IMAGES = OUTPUT_DIR / "images"
OUTPUT_AUDIO = OUTPUT_DIR / "audio"
OUTPUT_VIDEOS = OUTPUT_DIR / "videos"
OUTPUT_SHORTS = OUTPUT_DIR / "shorts"
OUTPUT_PROJECTS = OUTPUT_DIR / "projects"
OUTPUT_LOGS = OUTPUT_DIR / "logs"

# Cria pastas se não existirem
for folder in [OUTPUT_IMAGES, OUTPUT_AUDIO, OUTPUT_VIDEOS, OUTPUT_SHORTS, OUTPUT_PROJECTS, OUTPUT_LOGS]:
    folder.mkdir(parents=True, exist_ok=True)

# ===========================================
# API KEYS
# ===========================================

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_USERS = os.getenv("AUTHORIZED_USERS", "").split(",")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# HuggingFace
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# YouTube
YOUTUBE_CLIENT_SECRETS = os.getenv("YOUTUBE_CLIENT_SECRETS", "config/client_secrets.json")
YOUTUBE_CREDENTIALS_PATH = CONFIG_DIR / "youtube_credentials.pickle"

# ===========================================
# CONFIGURAÇÕES DE VÍDEO
# ===========================================

VIDEO_SETTINGS = {
    "short": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "duration_max": 60,
    },
    "youtube": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
    },
    "square": {
        "width": 1080,
        "height": 1080,
        "fps": 30,
    }
}

# ===========================================
# CONFIGURAÇÕES DE IMAGEM
# ===========================================

IMAGE_STYLES = {
    "cartoon": "cartoon style, pixar style, colorful, vibrant, high quality illustration",
    "anime": "anime style, studio ghibli, japanese animation, detailed, vibrant colors",
    "realistic": "photorealistic, 8k uhd, high quality photo, detailed, sharp focus",
    "digital_art": "digital art, fantasy art, highly detailed, vibrant colors, trending on artstation",
    "3d": "3d render, octane render, unreal engine, highly detailed, cinematic lighting",
    "comic": "comic book style, bold lines, dynamic, vibrant colors",
    "watercolor": "watercolor painting, soft colors, artistic, beautiful illustration",
    "cinematic": "cinematic shot, dramatic lighting, movie scene, epic, photorealistic",
    "stickman": "Palitinho fundo preto",
    "stickman_cute": "Palitinho fofo",
    "stickman_comic": "Palitinho estilo xkcd",
    "whiteboard": "Quadro branco",
    "chalkboard": "Lousa/giz",
}

DEFAULT_IMAGE_STYLE = "stickman"
IMAGES_PER_SHORT = 6
SECONDS_PER_IMAGE = 5

# ===========================================
# VALIDAÇÃO
# ===========================================

def validate_config():
    """Valida se as configurações essenciais estão presentes"""
    
    errors = []
    warnings = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN não configurado")
    
    if not HF_TOKEN:
        warnings.append("HF_TOKEN não configurado (imagens serão de menor qualidade)")
    
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY não configurado")
    
    if not Path(YOUTUBE_CLIENT_SECRETS).exists():
        warnings.append(f"client_secrets.json não encontrado em {YOUTUBE_CLIENT_SECRETS}")
    
    return errors, warnings


def print_config_status():
    """Mostra status das configurações"""
    
    print("\n" + "="*50)
    print("STATUS DAS CONFIGURAÇÕES")
    print("="*50)
    
    configs = [
        ("Telegram Bot", bool(TELEGRAM_BOT_TOKEN)),
        ("HuggingFace", bool(HF_TOKEN)),
        ("Groq", bool(GROQ_API_KEY)),
        ("YouTube Secrets", Path(YOUTUBE_CLIENT_SECRETS).exists()),
    ]
    
    for name, status in configs:
        icon = "✓" if status else "✗"
        print(f"  {icon} {name}")
    
    print("="*50 + "\n")


if __name__ == "__main__":
    print_config_status()
    
    errors, warnings = validate_config()
    
    if errors:
        print("❌ ERROS:")
        for e in errors:
            print(f"   - {e}")
    
    if warnings:
        print("⚠️  AVISOS:")
        for w in warnings:
            print(f"   - {w}")

# ======================================
# CONFIGURAÇÕES DE TTS
# ======================================
TTS_VOICES = {
    "br_feminina": "pt-BR-FranciscaNeural",
    "br_masculina": "pt-BR-AntonioNeural",
    "pt_feminina": "pt-PT-RaquelNeural",
    "pt_masculina": "pt-PT-DuarteNeural"
}

TTS_CONFIG = {
    "default_voice": "br_feminina",
    "rate": "+0%",
    "pitch": "+0Hz"
}




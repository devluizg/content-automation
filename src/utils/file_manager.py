"""
Gerenciador de arquivos e utilitários
"""
from pathlib import Path
import json
import re
from datetime import datetime


def slugify(text: str, max_length: int = 50) -> str:
    """Converte texto para slug (nome de arquivo seguro)"""
    # Remove caracteres especiais
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    # Substitui espaços por underscore
    slug = re.sub(r'[\s]+', '_', slug)
    # Limita tamanho
    return slug[:max_length]


def create_project_folder(topic: str, base_dir: str = "output") -> dict:
    """
    Cria estrutura de pastas para um projeto de conteúdo
    
    Returns:
        Dict com os caminhos criados
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(topic)
    
    project_name = f"{timestamp}_{slug}"
    project_dir = Path(base_dir) / "projects" / project_name
    
    paths = {
        "root": project_dir,
        "images": project_dir / "images",
        "audio": project_dir / "audio",
        "video": project_dir / "video",
        "text": project_dir / "text"
    }
    
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return {k: str(v) for k, v in paths.items()}


def save_json(data: dict, filepath: str):
    """Salva dados em arquivo JSON"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> dict:
    """Carrega dados de arquivo JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_file_size(filepath: str) -> str:
    """Retorna tamanho do arquivo formatado"""
    size = Path(filepath).stat().st_size
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    
    return f"{size:.1f} TB"

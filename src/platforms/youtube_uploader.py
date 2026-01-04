"""
YouTube Uploader - Upload automático de vídeos
v2.0 - Com suporte a thumbnail, idioma e categorias
"""

import os
import pickle
import json
from pathlib import Path
from typing import Optional, Dict, List

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import (
    YOUTUBE_CLIENT_SECRETS,
    YOUTUBE_CREDENTIALS_PATH,
    DATA_DIR
)

# Escopos necessários (inclui thumbnail)
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'  # Necessário para thumbnail
]

# Categorias do YouTube
VIDEO_CATEGORIES = {
    "film": "1",
    "autos": "2",
    "music": "10",
    "pets": "15",
    "sports": "17",
    "travel": "19",
    "gaming": "20",
    "vlog": "21",
    "people": "22",      # People & Blogs
    "comedy": "23",
    "entertainment": "24",
    "news": "25",
    "howto": "26",       # How-to & Style
    "education": "27",   # Educação
    "science": "28",     # Science & Technology
    "nonprofit": "29"
}


class YouTubeUploader:
    """
    Faz upload de vídeos para o YouTube
    v2.0 - Com suporte a:
    - Thumbnail personalizada
    - Configuração de idioma
    - Categorias
    - Made for Kids
    """
    
    def __init__(self):
        self.client_secrets = YOUTUBE_CLIENT_SECRETS
        self.credentials_path = YOUTUBE_CREDENTIALS_PATH
        self.youtube = None
        self.hashtags = self._load_hashtags()
        
        # Importa gerador de thumbnail (se disponível)
        try:
            from src.generators.thumbnail_generator import ThumbnailGenerator
            self.thumbnail_gen = ThumbnailGenerator()
            print("  ✓ ThumbnailGenerator disponível")
        except ImportError:
            self.thumbnail_gen = None
            print("  ⚠️ ThumbnailGenerator não disponível")
    
    def _load_hashtags(self) -> Dict:
        """Carrega hashtags do arquivo de dados"""
        hashtags_file = DATA_DIR / "hashtags.json"
        
        if hashtags_file.exists():
            with open(hashtags_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "default": ["shorts", "viral", "fyp", "foryou", "trending"],
            "education": ["aprender", "curiosidades", "fatos", "educacao", "conhecimento"],
            "entertainment": ["diversao", "engracado", "humor", "comedia"],
            "tech": ["tecnologia", "tech", "inovacao", "futuro", "digital"],
            "curiosity": ["curiosidades", "fatos", "voce sabia", "incrivel"],
        }
    
    def authenticate(self) -> bool:
        """Autentica com o YouTube"""
        
        credentials = None
        
        if not Path(self.client_secrets).exists():
            print(f"❌ Arquivo {self.client_secrets} não encontrado!")
            print("   Coloque o client_secrets.json na pasta config/")
            return False
        
        if Path(self.credentials_path).exists():
            with open(self.credentials_path, 'rb') as token:
                credentials = pickle.load(token)
        
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("🔄 Renovando credenciais do YouTube...")
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"⚠️ Erro ao renovar: {e}")
                    credentials = None
            
            if not credentials:
                print("🔐 Autenticando com YouTube...")
                print("   (vai abrir o navegador)")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets, 
                    SCOPES
                )
                credentials = flow.run_local_server(port=8888)
            
            Path(self.credentials_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.credentials_path, 'wb') as token:
                pickle.dump(credentials, token)
        
        self.youtube = build('youtube', 'v3', credentials=credentials)
        print("✓ Autenticado no YouTube!")
        
        return True
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Faz upload de thumbnail para um vídeo
        
        Args:
            video_id: ID do vídeo no YouTube
            thumbnail_path: Caminho da imagem (JPEG, PNG, etc.)
        
        Returns:
            True se sucesso
        """
        
        if not self.youtube:
            if not self.authenticate():
                return False
        
        if not Path(thumbnail_path).exists():
            print(f"❌ Thumbnail não encontrada: {thumbnail_path}")
            return False
        
        try:
            print(f"📸 Enviando thumbnail...")
            
            media = MediaFileUpload(
                thumbnail_path,
                mimetype='image/jpeg'
            )
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            
            print(f"   ✅ Thumbnail enviada!")
            return True
            
        except Exception as e:
            print(f"   ⚠️ Erro ao enviar thumbnail: {e}")
            return False
    
    def generate_thumbnail(self, title: str, video_type: str = "education") -> Optional[str]:
        """
        Gera thumbnail automaticamente usando IA
        
        Args:
            title: Título do vídeo
            video_type: Tipo do vídeo (education, entertainment, tech, etc.)
        
        Returns:
            Caminho da thumbnail ou None
        """
        
        if not self.thumbnail_gen:
            print("⚠️ ThumbnailGenerator não disponível")
            return None
        
        try:
            return self.thumbnail_gen.generate_from_topic(title, video_type)
        except Exception as e:
            print(f"⚠️ Erro ao gerar thumbnail: {e}")
            return None
    
    def upload(self,
               video_path: str,
               title: str,
               description: str,
               tags: List[str] = None,
               category: str = "entertainment",
               privacy: str = "public",
               made_for_kids: bool = False,
               is_short: bool = True,
               language: str = "pt-BR",
               thumbnail_path: str = None,
               auto_thumbnail: bool = True) -> Optional[Dict]:
        """
        Faz upload de um vídeo com todas as configurações
        
        Args:
            video_path: Caminho do vídeo
            title: Título do vídeo
            description: Descrição
            tags: Lista de tags
            category: Categoria (education, entertainment, tech, etc.)
            privacy: public, private, unlisted
            made_for_kids: Se é conteúdo infantil
            is_short: Se é um Short
            language: Idioma (pt-BR, en-US, etc.)
            thumbnail_path: Caminho da thumbnail (opcional)
            auto_thumbnail: Se True, gera thumbnail automática para vídeos longos
        
        Returns:
            Dados do vídeo ou None se falhar
        """
        
        if not self.youtube:
            if not self.authenticate():
                return None
        
        if not Path(video_path).exists():
            print(f"❌ Vídeo não encontrado: {video_path}")
            return None
        
        # Prepara tags
        if tags is None:
            tags = []
        
        # Adiciona hashtags para Shorts
        if is_short:
            if "Shorts" not in tags:
                tags.insert(0, "Shorts")
            if "#Shorts" not in title and "#shorts" not in title.lower():
                title = f"{title} #Shorts"
        
        # Limita título (100 chars max)
        if len(title) > 100:
            title = title[:97] + "..."
        
        # Adiciona hashtags na descrição
        hashtags_str = " ".join([f"#{tag}" for tag in tags[:15] if not tag.startswith("#")])
        full_description = f"{description}\n\n{hashtags_str}"
        
        # Obtém ID da categoria
        category_id = VIDEO_CATEGORIES.get(category.lower(), VIDEO_CATEGORIES["entertainment"])
        
        # Metadata do vídeo
        body = {
            "snippet": {
                "title": title,
                "description": full_description,
                "tags": tags[:500],
                "categoryId": category_id,
                "defaultLanguage": language,
                "defaultAudioLanguage": language,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": made_for_kids,
                "madeForKids": made_for_kids,
            }
        }
        
        print(f"\n📤 Fazendo upload...")
        print(f"   📹 Título: {title[:50]}...")
        print(f"   📁 Arquivo: {Path(video_path).name}")
        print(f"   🏷️ Categoria: {category} ({category_id})")
        print(f"   🌐 Idioma: {language}")
        print(f"   {'📱 Tipo: Short' if is_short else '🎬 Tipo: Vídeo longo'}")
        
        try:
            # Upload
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                resumable=True,
                chunksize=1024*1024
            )
            
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            # Executa upload com progresso
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"   ⬆️ Progresso: {progress}%")
            
            video_id = response['id']
            
            if is_short:
                video_url = f"https://youtube.com/shorts/{video_id}"
            else:
                video_url = f"https://youtube.com/watch?v={video_id}"
            
            print(f"\n   ✅ Upload concluído!")
            print(f"   🔗 URL: {video_url}")
            
            # ===== THUMBNAIL =====
            # Para vídeos longos, tenta enviar/gerar thumbnail
            if not is_short:
                thumbnail_sent = False
                
                # Se foi fornecida uma thumbnail
                if thumbnail_path and Path(thumbnail_path).exists():
                    thumbnail_sent = self.upload_thumbnail(video_id, thumbnail_path)
                
                # Se não foi fornecida ou falhou, tenta gerar automaticamente
                elif auto_thumbnail and self.thumbnail_gen:
                    print(f"\n🎨 Gerando thumbnail automática...")
                    
                    # Determina tipo do vídeo baseado na categoria
                    video_type = category if category in ["education", "entertainment", "tech"] else "entertainment"
                    
                    generated_thumb = self.generate_thumbnail(title, video_type)
                    
                    if generated_thumb:
                        thumbnail_sent = self.upload_thumbnail(video_id, generated_thumb)
                
                if not thumbnail_sent:
                    print(f"   ⚠️ Vídeo publicado sem thumbnail personalizada")
            
            return {
                "id": video_id,
                "url": video_url,
                "title": title,
                "is_short": is_short,
                "category": category,
                "language": language,
                "response": response
            }
            
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_metadata(self, topic: str, style: str = "engaging", 
                          video_type: str = "education") -> Dict:
        """
        Gera título, descrição e tags automaticamente
        
        Args:
            topic: Assunto do vídeo
            style: engaging, educational, funny
            video_type: education, entertainment, tech, etc.
        
        Returns:
            dict com title, description, tags, category
        """
        
        import random
        
        templates = {
            "engaging": {
                "prefixes": ["😱", "🔥", "⚡", "🤯", "💡", "❗", "🚀"],
                "suffixes": ["", "| Você PRECISA ver!", "| Incrível!", "| Impressionante!"],
            },
            "educational": {
                "prefixes": ["📚", "🎓", "💡", "🧠", "✨", "📖"],
                "suffixes": ["", "| Aprenda agora!", "| Fatos incríveis!", "| Guia completo"],
            },
            "funny": {
                "prefixes": ["😂", "🤣", "😅", "💀", "😭"],
                "suffixes": ["", "| Muito engraçado!", "| Kkkkk", "| Impossível não rir"],
            }
        }
        
        template = templates.get(style, templates["engaging"])
        prefix = random.choice(template["prefixes"])
        suffix = random.choice(template["suffixes"])
        
        title = f"{prefix} {topic.title()} {suffix}".strip()
        
        if len(title) > 95:
            title = title[:92] + "..."
        
        description = f"""{prefix} {topic.title()}

Neste vídeo você vai descobrir coisas incríveis!

📌 Gostou? Deixe seu LIKE!
🔔 INSCREVA-SE e ative o sininho!
💬 Comenta aqui embaixo o que você achou!

═══════════════════════════════════
📱 Me siga nas redes sociais!
═══════════════════════════════════

#shorts #viral #fyp #brasil"""
        
        # Gera tags
        words = topic.lower().replace(",", " ").replace(".", " ").split()
        base_tags = self.hashtags.get(video_type, self.hashtags["default"])
        
        tags = [
            "Shorts",
            *base_tags,
            topic.lower().replace(" ", ""),
            *[w for w in words if len(w) > 2][:5],
            "brasil",
            "portugues",
            "2025"
        ]
        
        tags = list(dict.fromkeys(tags))
        
        # Determina categoria
        category_map = {
            "education": "education",
            "entertainment": "entertainment", 
            "tech": "science",
            "curiosity": "education",
            "comedy": "comedy",
            "lifestyle": "howto",
        }
        category = category_map.get(video_type, "entertainment")
        
        return {
            "title": title,
            "description": description,
            "tags": tags[:30],
            "category": category
        }


# ===========================================
# TESTE
# ===========================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("TESTE - YOUTUBE UPLOADER v2.0")
    print("="*50 + "\n")
    
    uploader = YouTubeUploader()
    
    # Testa autenticação
    if uploader.authenticate():
        print("\n✓ Autenticação OK!")
        
        # Gera metadata de teste
        metadata = uploader.generate_metadata(
            "curiosidades sobre o espaço",
            style="engaging",
            video_type="education"
        )
        
        print(f"\n📋 Metadata gerado:")
        print(f"   Título: {metadata['title']}")
        print(f"   Categoria: {metadata['category']}")
        print(f"   Tags: {metadata['tags'][:5]}...")
        
        # Testa geração de thumbnail
        if uploader.thumbnail_gen:
            print(f"\n🎨 Testando geração de thumbnail...")
            thumb = uploader.generate_thumbnail(
                "5 Curiosidades sobre o Universo",
                video_type="education"
            )
            if thumb:
                print(f"   ✅ Thumbnail gerada: {thumb}")
        
    else:
        print("\n❌ Falha na autenticação")
    
    print("\n" + "="*50)
    print("Teste concluído!")
    print("="*50)
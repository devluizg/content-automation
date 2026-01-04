"""
Gerador de Video com Legendas Sincronizadas
v2.2 - Com BLUR BACKGROUND para imagens que não preenchem a tela
"""
from pathlib import Path
import random
import numpy as np
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys

from moviepy.editor import (
    ImageClip, AudioFileClip, VideoFileClip,
    CompositeVideoClip, concatenate_videoclips,
    VideoClip
)
from moviepy.video.fx.all import fadein, fadeout

sys.path.append(str(Path(__file__).parent.parent))
from utils.srt_generator import SRTGenerator


class VideoGenerator:
    """Gera videos com legendas sincronizadas - v2.2 com Blur Background"""
    
    def __init__(self, output_dir: str = "output/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.formats = {
            "short": {"width": 1080, "height": 1920, "fps": 30},
            "reels": {"width": 1080, "height": 1920, "fps": 30},
            "tiktok": {"width": 1080, "height": 1920, "fps": 30},
            "story": {"width": 1080, "height": 1920, "fps": 30},
            "youtube": {"width": 1920, "height": 1080, "fps": 30},
            "youtube_vertical": {"width": 1080, "height": 1920, "fps": 30},
            "youtube_hd": {"width": 1280, "height": 720, "fps": 30},
            "square": {"width": 1080, "height": 1080, "fps": 30},
        }
        
        self.effects = ["zoom_in", "zoom_out", "pan_left", "pan_right"]
        
        self.video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
        self.gif_extensions = ['.gif']
        self.image_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
        
        self.subtitle_config = {
            "font_size": 72,
            "words_per_subtitle": 2,
            "font_color": (255, 255, 255),
            "stroke_color": (0, 0, 0),
            "stroke_width": 6,
        }
        
        # ✅ NOVO: Configurações de blur background
        self.blur_config = {
            "enabled": True,           # Ativar/desativar blur
            "blur_radius": 50,         # Intensidade do blur (quanto maior, mais borrado)
            "darken_factor": 0.6,      # Escurecer o fundo (0.0 = preto, 1.0 = normal)
            "scale_factor": 1.5,       # Quanto aumentar a imagem de fundo
            "min_coverage": 0.7,       # Mínimo de cobertura para NÃO aplicar blur (70%)
        }
        
        self.font_path = self._find_font()
        self.srt_gen = SRTGenerator(words_per_subtitle=2)
        
        print(f"🎬 VideoGenerator v2.2 inicializado")
        print(f"   ✨ Blur Background: {'Ativado' if self.blur_config['enabled'] else 'Desativado'}")
    
    def _find_font(self) -> str:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        ]
        for p in paths:
            if Path(p).exists():
                return p
        return None
    
    def _get_media_type(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        
        if ext in self.video_extensions:
            return 'video'
        elif ext in self.gif_extensions:
            return 'gif'
        elif ext in self.image_extensions:
            return 'image'
        else:
            return 'unknown'
    
    def _validate_video_file(self, file_path: str) -> bool:
        """Valida se o arquivo de vídeo pode ser lido"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return False
            
            output = result.stdout.strip()
            if not output:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _create_black_clip(self, duration: float, width: int, height: int) -> VideoClip:
        """Cria um clip preto como fallback"""
        def make_frame(t):
            return np.zeros((height, width, 3), dtype=np.uint8)
        
        return VideoClip(make_frame, duration=duration)
    
    def _create_fallback_clip(self, duration: float, width: int, height: int, 
                              original_path: str = None) -> VideoClip:
        """Cria clip de fallback para arquivos corrompidos"""
        if original_path and os.path.exists(original_path):
            try:
                temp_frame = original_path.rsplit(".", 1)[0] + "_frame.png"
                
                result = subprocess.run([
                    'ffmpeg', '-y', '-i', original_path,
                    '-vframes', '1', '-f', 'image2',
                    temp_frame
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and os.path.exists(temp_frame):
                    img_clip = ImageClip(temp_frame).set_duration(duration)
                    img_clip = self._resize_with_blur_background(img_clip, width, height)
                    
                    try:
                        os.remove(temp_frame)
                    except:
                        pass
                    
                    print(f"      🔄 Usando frame extraído como fallback")
                    return img_clip
                    
            except Exception as e:
                print(f"      ⚠️ Não foi possível extrair frame: {e}")
        
        print(f"      ⬛ Usando clip preto como fallback")
        return self._create_black_clip(duration, width, height)
    
    # ===========================================
    # ✅ NOVO: BLUR BACKGROUND
    # ===========================================
    
    def _create_blur_background(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """
        Cria um fundo borrado baseado na imagem original
        
        Args:
            image: Imagem PIL original
            target_width: Largura do canvas final
            target_height: Altura do canvas final
            
        Returns:
            Imagem PIL com fundo borrado no tamanho correto
        """
        # Converte para RGB se necessário
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Calcula escala para cobrir todo o canvas
        img_w, img_h = image.size
        scale_w = target_width / img_w
        scale_h = target_height / img_h
        scale = max(scale_w, scale_h) * self.blur_config['scale_factor']
        
        # Redimensiona para cobrir o canvas
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        # Usa LANCZOS para qualidade (substitui ANTIALIAS depreciado)
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        
        bg_image = image.resize((new_w, new_h), resample)
        
        # Centraliza e corta para o tamanho do canvas
        left = (new_w - target_width) // 2
        top = (new_h - target_height) // 2
        bg_image = bg_image.crop((left, top, left + target_width, top + target_height))
        
        # Aplica blur gaussiano
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=self.blur_config['blur_radius']))
        
        # Escurece o fundo para a imagem principal se destacar
        darken = self.blur_config['darken_factor']
        if darken < 1.0:
            # Cria overlay escuro
            dark_overlay = Image.new('RGB', (target_width, target_height), (0, 0, 0))
            bg_image = Image.blend(bg_image, dark_overlay, 1.0 - darken)
        
        return bg_image
    
    def _calculate_coverage(self, img_w: int, img_h: int, target_w: int, target_h: int) -> float:
        """
        Calcula quanto da área do canvas a imagem cobre (sem distorcer)
        
        Returns:
            Float entre 0.0 e 1.0 representando a porcentagem de cobertura
        """
        # Calcula escala mantendo proporção (fit)
        scale_w = target_w / img_w
        scale_h = target_h / img_h
        scale = min(scale_w, scale_h)
        
        # Tamanho final da imagem
        final_w = int(img_w * scale)
        final_h = int(img_h * scale)
        
        # Área coberta vs área total
        coverage = (final_w * final_h) / (target_w * target_h)
        
        return coverage
    
    def _resize_with_blur_background(self, clip: VideoClip, width: int, height: int) -> VideoClip:
        """
        Redimensiona clip com fundo borrado (blur background)
        
        Se a imagem não preencher pelo menos X% do canvas, usa blur background.
        Caso contrário, usa padding preto simples.
        """
        try:
            clip_w, clip_h = clip.size
            
            # Calcula cobertura
            coverage = self._calculate_coverage(clip_w, clip_h, width, height)
            
            # Se blur está desativado ou imagem cobre o suficiente, usa método simples
            if not self.blur_config['enabled'] or coverage >= self.blur_config['min_coverage']:
                return self._resize_clip_simple(clip, width, height)
            
            print(f"      🌫️ Aplicando blur background (cobertura: {coverage*100:.0f}%)")
            
            # Pega o primeiro frame para criar o fundo
            try:
                first_frame = clip.get_frame(0)
                if first_frame.dtype != np.uint8:
                    first_frame = np.uint8(np.clip(first_frame, 0, 255))
                bg_source = Image.fromarray(first_frame)
            except:
                # Se não conseguir pegar frame, usa método simples
                return self._resize_clip_simple(clip, width, height)
            
            # Cria o fundo borrado
            blur_bg = self._create_blur_background(bg_source, width, height)
            blur_bg_array = np.array(blur_bg)
            
            # Calcula dimensões da imagem principal (fit)
            scale_w = width / clip_w
            scale_h = height / clip_h
            scale = min(scale_w, scale_h)
            
            new_w = int(clip_w * scale)
            new_h = int(clip_h * scale)
            
            # Posição centralizada
            x_pos = (width - new_w) // 2
            y_pos = (height - new_h) // 2
            
            # Redimensiona o clip original
            clip_resized = clip.resize((new_w, new_h))
            
            # Função para compor cada frame
            def make_frame_with_blur(t):
                # Começa com o fundo borrado
                frame = blur_bg_array.copy()
                
                try:
                    # Pega frame do clip original
                    clip_frame = clip_resized.get_frame(t)
                    if clip_frame.dtype != np.uint8:
                        clip_frame = np.uint8(np.clip(clip_frame, 0, 255))
                    
                    # Cola a imagem principal no centro
                    frame[y_pos:y_pos+new_h, x_pos:x_pos+new_w] = clip_frame
                except:
                    pass
                
                return frame
            
            return VideoClip(make_frame_with_blur, duration=clip.duration)
            
        except Exception as e:
            print(f"      ⚠️ Erro no blur background: {e}, usando método simples")
            return self._resize_clip_simple(clip, width, height)
    
    def _resize_clip_simple(self, clip: VideoClip, width: int, height: int) -> VideoClip:
        """Redimensiona clip com padding preto (método original)"""
        try:
            clip_w, clip_h = clip.size
            
            scale_w = width / clip_w
            scale_h = height / clip_h
            scale = min(scale_w, scale_h)
            
            new_w = int(clip_w * scale)
            new_h = int(clip_h * scale)
            
            clip_resized = clip.resize((new_w, new_h))
            
            x_pos = (width - new_w) // 2
            y_pos = (height - new_h) // 2
            
            def make_black_frame(t):
                return np.zeros((height, width, 3), dtype=np.uint8)
            
            black_bg = VideoClip(make_black_frame, duration=clip.duration)
            
            final = CompositeVideoClip(
                [black_bg, clip_resized.set_position((x_pos, y_pos))],
                size=(width, height)
            )
            
            return final
            
        except Exception as e:
            print(f"      ⚠️ Erro no resize simples: {e}")
            return clip.resize((width, height))
    
    # Mantém o método antigo como alias para compatibilidade
    def _resize_clip_with_padding(self, clip: VideoClip, width: int, height: int) -> VideoClip:
        """Alias para o novo método com blur background"""
        return self._resize_with_blur_background(clip, width, height)
    
    # ===========================================
    # CARREGAMENTO DE MÍDIAS
    # ===========================================
    
    def _load_media_as_clip(self, file_path: str, duration: float, 
                            width: int, height: int, apply_effect: bool = True) -> VideoClip:
        """Carrega qualquer tipo de mídia como VideoClip"""
        media_type = self._get_media_type(file_path)
        
        print(f"      Tipo: {media_type} | Duração: {duration:.1f}s")
        
        if media_type == 'video':
            clip = self._load_video_clip(file_path, duration, width, height)
        elif media_type == 'gif':
            clip = self._load_gif_clip(file_path, duration, width, height)
        elif media_type == 'image':
            clip = self._load_image_clip(file_path, duration, width, height, apply_effect)
        else:
            print(f"      ⚠️ Tipo desconhecido, tratando como imagem")
            clip = self._load_image_clip(file_path, duration, width, height, apply_effect)
        
        return clip
    
    def _load_video_clip(self, file_path: str, duration: float, 
                         width: int, height: int) -> VideoClip:
        """Carrega vídeo MP4 com tratamento de erro"""
        try:
            if not self._validate_video_file(file_path):
                print(f"      ⚠️ Arquivo inválido, usando fallback")
                return self._create_fallback_clip(duration, width, height, file_path)
            
            clip = VideoFileClip(file_path)
            
            if clip.duration is None or clip.duration <= 0:
                print(f"      ⚠️ Vídeo sem duração válida")
                clip.close()
                return self._create_fallback_clip(duration, width, height, file_path)
            
            original_duration = clip.duration
            
            if clip.duration < duration:
                loops_needed = int(duration / clip.duration) + 1
                try:
                    clips_to_concat = [clip] * loops_needed
                    clip = concatenate_videoclips(clips_to_concat)
                except Exception as e:
                    print(f"      ⚠️ Erro ao fazer loop: {e}")
                    return self._create_fallback_clip(duration, width, height, file_path)
            
            clip = clip.subclip(0, min(duration, clip.duration))
            clip = self._resize_with_blur_background(clip, width, height)
            
            print(f"      ✅ Vídeo carregado ({original_duration:.1f}s → {duration:.1f}s)")
            
            return clip
            
        except Exception as e:
            print(f"      ❌ Erro ao carregar vídeo: {e}")
            return self._create_fallback_clip(duration, width, height, file_path)
    
    def _load_gif_clip(self, file_path: str, duration: float, 
                       width: int, height: int) -> VideoClip:
        """Carrega GIF com tratamento de erro"""
        try:
            clip = VideoFileClip(file_path)
            
            clip_duration = clip.duration if clip.duration else 2.0
            if clip_duration <= 0:
                clip_duration = 2.0
            
            original_duration = clip_duration
            
            if clip_duration < duration:
                loops_needed = int(duration / clip_duration) + 1
                try:
                    clips_to_concat = [clip] * loops_needed
                    clip = concatenate_videoclips(clips_to_concat)
                except Exception as e:
                    print(f"      ⚠️ Erro ao fazer loop do GIF: {e}")
                    return self._load_image_clip(file_path, duration, width, height, apply_effect=False)
            
            if clip.duration:
                clip = clip.subclip(0, min(duration, clip.duration))
            else:
                clip = clip.set_duration(duration)
            
            clip = self._resize_with_blur_background(clip, width, height)
            
            print(f"      ✅ GIF carregado ({original_duration:.1f}s → {duration:.1f}s)")
            
            return clip
            
        except Exception as e:
            print(f"      ❌ Erro ao carregar GIF: {e}")
            try:
                return self._load_image_clip(file_path, duration, width, height, apply_effect=False)
            except:
                return self._create_fallback_clip(duration, width, height, file_path)
    
    def _load_image_clip(self, file_path: str, duration: float, 
                         width: int, height: int, apply_effect: bool = True) -> VideoClip:
        """Carrega imagem estática com blur background"""
        try:
            img_clip = ImageClip(file_path)
            
            if apply_effect:
                effect = random.choice(self.effects)
                clip = self._apply_ken_burns(img_clip, effect, duration, width, height)
                print(f"      ✅ Imagem + efeito {effect}")
            else:
                clip = img_clip.set_duration(duration)
                clip = self._resize_with_blur_background(clip, width, height)
                print(f"      ✅ Imagem estática")
            
            return clip
            
        except Exception as e:
            print(f"      ❌ Erro ao carregar imagem: {e}")
            return self._create_black_clip(duration, width, height)
    
    def _apply_ken_burns(self, clip, effect: str, duration: float, width: int, height: int):
        """Aplica efeito Ken Burns em imagens com blur background"""
        original_frame = clip.get_frame(0)
        
        if original_frame.dtype != np.uint8:
            original_frame = np.uint8(np.clip(original_frame, 0, 255))
        
        pil_img = Image.fromarray(original_frame)
        
        # Verifica se precisa de blur background
        img_w, img_h = pil_img.size
        coverage = self._calculate_coverage(img_w, img_h, width, height)
        use_blur = self.blur_config['enabled'] and coverage < self.blur_config['min_coverage']
        
        if use_blur:
            print(f"      🌫️ Ken Burns com blur background")
            # Cria fundo borrado
            blur_bg = self._create_blur_background(pil_img, width, height)
        
        # Prepara imagem para efeito
        scale = 1.2
        base_w = int(width * scale)
        base_h = int(height * scale)
        
        # Redimensiona imagem mantendo proporção
        img_scale = min(base_w / img_w, base_h / img_h)
        scaled_w = int(img_w * img_scale)
        scaled_h = int(img_h * img_scale)
        
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS
        
        pil_img_scaled = pil_img.resize((scaled_w, scaled_h), resample)
        
        def make_frame(t):
            progress = t / duration if duration > 0 else 0
            
            if effect == "zoom_in":
                zoom = 1.0 + (0.15 * progress)
            elif effect == "zoom_out":
                zoom = 1.15 - (0.15 * progress)
            else:
                zoom = 1.0
            
            crop_w = int(width / zoom)
            crop_h = int(height / zoom)
            
            # Calcula posição do crop na imagem escalada
            if effect == "pan_left":
                x_offset = int((scaled_w - crop_w) * (1 - progress))
            elif effect == "pan_right":
                x_offset = int((scaled_w - crop_w) * progress)
            else:
                x_offset = (scaled_w - crop_w) // 2
            
            y_offset = (scaled_h - crop_h) // 2
            
            # Garante que não saia dos limites
            x_offset = max(0, min(x_offset, scaled_w - crop_w))
            y_offset = max(0, min(y_offset, scaled_h - crop_h))
            
            # Corta e redimensiona
            cropped = pil_img_scaled.crop((x_offset, y_offset, x_offset + crop_w, y_offset + crop_h))
            final_img = cropped.resize((width, height), resample)
            
            # Se usar blur, compõe com o fundo
            if use_blur:
                # Calcula tamanho da imagem principal neste frame
                main_w = int(scaled_w / zoom * 0.85)  # 85% do tamanho para não cobrir tudo
                main_h = int(scaled_h / zoom * 0.85)
                
                # Limita ao tamanho do canvas
                main_w = min(main_w, width - 40)
                main_h = min(main_h, height - 40)
                
                # Mantém proporção
                img_ratio = img_w / img_h
                canvas_ratio = main_w / main_h
                
                if img_ratio > canvas_ratio:
                    main_h = int(main_w / img_ratio)
                else:
                    main_w = int(main_h * img_ratio)
                
                # Redimensiona imagem original
                main_img = pil_img.resize((main_w, main_h), resample)
                
                # Posição centralizada
                x_pos = (width - main_w) // 2
                y_pos = (height - main_h) // 2
                
                # Compõe: fundo blur + imagem principal
                result = blur_bg.copy()
                result.paste(main_img, (x_pos, y_pos))
                
                return np.array(result, dtype=np.uint8)
            else:
                return np.array(final_img, dtype=np.uint8)
        
        return VideoClip(make_frame, duration=duration)
    
    # ===========================================
    # LEGENDAS
    # ===========================================
    
    def _render_text_on_frame(self, frame: np.ndarray, text: str, width: int, height: int) -> np.ndarray:
        """Renderiza texto com borda no frame"""
        if frame.dtype != np.uint8:
            frame = np.uint8(frame)
        
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img)
        
        font_size = self.subtitle_config["font_size"]
        stroke_width = self.subtitle_config["stroke_width"]
        
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        text_upper = text.upper()
        
        text_bbox = draw.textbbox((0, 0), text_upper, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        
        x = (width - text_width) // 2
        y = int(height * 0.65)
        
        stroke_color = self.subtitle_config["stroke_color"]
        for offset in range(1, stroke_width + 1):
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text_upper, font=font, fill=stroke_color)
        
        draw.text((x, y), text_upper, font=font, fill=self.subtitle_config["font_color"])
        
        return np.array(img, dtype=np.uint8)
    
    def _create_video_with_subtitles(self, base_video, subtitle_text: str, 
                                      duration: float, width: int, height: int) -> VideoClip:
        """Cria video com legendas"""
        timings = self.srt_gen.calculate_timings(subtitle_text, duration)
        
        print(f"    {len(timings)} legendas sincronizadas")
        
        def get_subtitle_at_time(t):
            for timing in timings:
                if timing["start"] <= t < timing["end"]:
                    return timing["text"]
            return None
        
        def make_frame_with_subtitle(t):
            try:
                frame = base_video.get_frame(t)
            except Exception as e:
                frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            if frame.dtype != np.uint8:
                frame = np.uint8(np.clip(frame, 0, 255))
            
            subtitle = get_subtitle_at_time(t)
            
            if subtitle:
                frame = self._render_text_on_frame(frame, subtitle, width, height)
            
            return frame
        
        return VideoClip(make_frame_with_subtitle, duration=duration)
    
    # ===========================================
    # CONFIGURAÇÃO DE BLUR
    # ===========================================
    
    def set_blur_config(self, 
                        enabled: bool = None,
                        blur_radius: int = None,
                        darken_factor: float = None,
                        min_coverage: float = None):
        """
        Configura o blur background
        
        Args:
            enabled: Ativar/desativar blur
            blur_radius: Intensidade do blur (10-100)
            darken_factor: Escurecer fundo (0.0-1.0)
            min_coverage: Cobertura mínima para não aplicar blur (0.0-1.0)
        """
        if enabled is not None:
            self.blur_config['enabled'] = enabled
        
        if blur_radius is not None:
            self.blur_config['blur_radius'] = max(10, min(100, blur_radius))
        
        if darken_factor is not None:
            self.blur_config['darken_factor'] = max(0.0, min(1.0, darken_factor))
        
        if min_coverage is not None:
            self.blur_config['min_coverage'] = max(0.0, min(1.0, min_coverage))
        
        print(f"🌫️ Blur config atualizado: {self.blur_config}")
    
    # ===========================================
    # CRIAÇÃO DE VÍDEOS
    # ===========================================
    
    def create_short(self, images: list, audio_path: str, output_name: str,
                     add_subtitles: bool = True, subtitle_text: str = None,
                     save_srt: bool = True) -> str:
        """Cria video short com legendas"""
        return self._create_video(
            media_files=images,
            audio_path=audio_path,
            output_name=output_name,
            format="short",
            add_subtitles=add_subtitles,
            subtitle_text=subtitle_text,
            save_srt=save_srt
        )
    
    def create_slideshow(self, images: list, audio_path: str, output_name: str,
                         format: str = "youtube", add_subtitles: bool = True,
                         subtitle_text: str = None, save_srt: bool = True) -> str:
        """Cria slideshow com legendas"""
        return self._create_video(
            media_files=images,
            audio_path=audio_path,
            output_name=output_name,
            format=format,
            add_subtitles=add_subtitles,
            subtitle_text=subtitle_text,
            save_srt=save_srt
        )
    
    def _create_video(self, media_files: list, audio_path: str, output_name: str,
                      format: str, add_subtitles: bool = True,
                      subtitle_text: str = None, save_srt: bool = True) -> str:
        """Cria video com legendas e blur background"""
        
        config = self.formats.get(format, self.formats["short"])
        width = config["width"]
        height = config["height"]
        fps = config["fps"]
        
        print(f"\n🎬 Criando video {format} ({width}x{height})...")
        print(f"   🌫️ Blur background: {'Ativado' if self.blur_config['enabled'] else 'Desativado'}")
        
        audio = AudioFileClip(audio_path)
        total_duration = audio.duration
        
        print(f"  🔊 Audio: {total_duration:.1f}s")
        
        if not media_files:
            raise ValueError("Nenhuma mídia fornecida")
        
        # Filtra arquivos que existem
        valid_files = [f for f in media_files if os.path.exists(f)]
        if len(valid_files) < len(media_files):
            print(f"  ⚠️ {len(media_files) - len(valid_files)} arquivos não encontrados")
        
        if not valid_files:
            raise ValueError("Nenhum arquivo de mídia válido encontrado")
        
        media_files = valid_files
        
        media_types = [self._get_media_type(f) for f in media_files]
        video_count = sum(1 for t in media_types if t in ['video', 'gif'])
        image_count = sum(1 for t in media_types if t == 'image')
        
        print(f"  📁 Mídias: {len(media_files)} total ({video_count} vídeos/GIFs, {image_count} imagens)")
        
        duration_per_media = total_duration / len(media_files)
        print(f"  ⏱️ Duração por mídia: {duration_per_media:.1f}s")
        
        print("  📹 Carregando mídias...")
        clips = []
        crossfade = 0.3
        
        for i, media_path in enumerate(media_files):
            print(f"    [{i+1}/{len(media_files)}] {Path(media_path).name}")
            
            media_type = self._get_media_type(media_path)
            apply_effect = (media_type == 'image')
            
            clip = self._load_media_as_clip(
                file_path=media_path,
                duration=duration_per_media,
                width=width,
                height=height,
                apply_effect=apply_effect
            )
            
            clip = fadein(clip, crossfade)
            clip = fadeout(clip, crossfade)
            
            clips.append(clip)
        
        print("  🔗 Concatenando clips...")
        video = concatenate_videoclips(clips, method="compose", padding=-crossfade)
        
        if video.duration > total_duration:
            video = video.subclip(0, total_duration)
        
        if add_subtitles and subtitle_text:
            print("  📝 Adicionando legendas...")
            
            if save_srt:
                srt_path = str(self.output_dir / f"{output_name}.srt")
                self.srt_gen.generate_srt(subtitle_text, total_duration, srt_path)
                print(f"    SRT salvo: {srt_path}")
            
            video = self._create_video_with_subtitles(
                video, subtitle_text, total_duration, width, height
            )
        
        video = video.set_audio(audio)
        
        output_path = self.output_dir / f"{output_name}.mp4"
        print(f"  💾 Renderizando video...")
        
        video.write_videofile(
            str(output_path),
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=4,
            logger=None
        )
        
        # Fecha recursos
        video.close()
        audio.close()
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        
        print(f"\n✅ Video salvo: {output_path}")
        
        return str(output_path)


# ===========================================
# TESTE
# ===========================================

if __name__ == "__main__":
    print("="*50)
    print("VideoGenerator v2.2 - Com Blur Background")
    print("="*50)
    
    gen = VideoGenerator()
    
    # Mostra configuração atual
    print(f"\n🌫️ Configuração de Blur:")
    print(f"   Enabled: {gen.blur_config['enabled']}")
    print(f"   Blur Radius: {gen.blur_config['blur_radius']}")
    print(f"   Darken Factor: {gen.blur_config['darken_factor']}")
    print(f"   Min Coverage: {gen.blur_config['min_coverage']*100}%")
    
    # Exemplo de como alterar configuração
    print("\n📝 Exemplo de uso:")
    print("   gen.set_blur_config(blur_radius=60, darken_factor=0.5)")
    
    print("\n✅ VideoGenerator pronto!")
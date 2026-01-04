#!/usr/bin/env python3
"""
Pipeline Automatico com Legendas TikTok
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.generators.text_generator import TextGenerator
from src.generators.image_generator import ImageGenerator, STYLES
from src.generators.audio_generator import AudioGenerator
from src.generators.video_generator import VideoGenerator
from src.utils.file_manager import create_project_folder, save_json, slugify
from src.utils.logger import Logger
from src.utils.image_resizer import SIZES


class ContentPipeline:
    """Pipeline automatico com legendas"""
    
    SECONDS_PER_IMAGE = 5
    
    def __init__(self, llm_provider: str = "groq", image_style: str = "cartoon"):
        self.log = Logger("Auto")
        
        self.log.info(f"Inicializando (LLM: {llm_provider} | Estilo: {image_style})")
        
        self.text_gen = TextGenerator(provider=llm_provider)
        self.image_gen = ImageGenerator(
            remove_watermark=True,
            watermark_method="crop",
            auto_resize=True,
            resize_method="cover",
            style=image_style
        )
        self.audio_gen = AudioGenerator(engine="edge")
        self.video_gen = VideoGenerator()
        self.image_style = image_style
        
        self.log.success("Pipeline inicializado!")
    
    def create_short(self, topic, voice="br_feminina", speech_rate="+5%", 
                     crop_watermark=80, seconds_per_image=None,
                     add_subtitles=True):
        return self._create_video(topic, "short", voice, speech_rate, 
                                  crop_watermark, seconds_per_image or self.SECONDS_PER_IMAGE,
                                  add_subtitles)
    
    def create_youtube_video(self, topic, voice="br_feminina", speech_rate="+0%",
                             crop_watermark=60, seconds_per_image=None,
                             add_subtitles=True):
        return self._create_video(topic, "youtube", voice, speech_rate,
                                  crop_watermark, seconds_per_image or self.SECONDS_PER_IMAGE,
                                  add_subtitles)
    
    def create_square_video(self, topic, voice="br_feminina", speech_rate="+5%",
                            crop_watermark=80, seconds_per_image=None,
                            add_subtitles=True):
        return self._create_video(topic, "square", voice, speech_rate,
                                  crop_watermark, seconds_per_image or self.SECONDS_PER_IMAGE,
                                  add_subtitles)
    
    def _create_video(self, topic, format, voice, speech_rate, crop_watermark, 
                      seconds_per_image, add_subtitles):
        
        if format in SIZES:
            width, height = SIZES[format]["width"], SIZES[format]["height"]
            format_desc = SIZES[format]["description"]
        else:
            width, height, format_desc = 1080, 1920, "Video"
        
        self.log.info(f"Criando {format_desc}: {topic}")
        self.log.info(f"Legendas: {'Sim' if add_subtitles else 'Nao'}")
        
        paths = create_project_folder(f"{format}_{topic}")
        result = {"topic": topic, "format": format, "paths": paths, "files": {}}
        
        # 1. Roteiro
        self.log.step(1, 5, "Gerando roteiro...")
        script = self.text_gen.generate_short_script(topic)
        save_json(script, str(Path(paths["text"]) / "roteiro.json"))
        result["script"] = script
        self.log.success(f"Roteiro: {script['titulo']}")
        
        # 2. Audio
        self.log.step(2, 5, "Gerando narracao...")
        narration = script.get("narracao") or f"{script.get('hook','')} {script.get('roteiro','')} {script.get('cta','')}"
        
        # Salva texto da narracao para legendas
        narration_text = narration
        
        audio_path = Path(paths["audio"]) / "narracao.mp3"
        self.audio_gen.generate(narration, str(audio_path), voice, speech_rate)
        result["files"]["audio"] = str(audio_path)
        
        from moviepy.editor import AudioFileClip
        audio_clip = AudioFileClip(str(audio_path))
        duration = audio_clip.duration
        audio_clip.close()
        self.log.success(f"Audio: {duration:.1f}s")
        
        # 3. Imagens
        num_images = max(5, int(duration / seconds_per_image) + 1)
        self.log.step(3, 5, f"Gerando {num_images} imagens...")
        
        prompts = script.get("cenas", [])
        while len(prompts) < num_images:
            prompts.append(f"scene about {topic}, creative illustration")
        
        images = self.image_gen.generate_batch(prompts[:num_images], paths["images"], 
                                                format, 2, crop_watermark)
        result["files"]["images"] = images
        self.log.success(f"{len(images)} imagens")
        
        # 4. Video COM LEGENDAS
        self.log.step(4, 5, "Montando video com legendas...")
        video_name = slugify(f"{format}_{topic}")
        
        video_path = self.video_gen.create_short(
            images=images,
            audio_path=str(audio_path),
            output_name=video_name,
            add_subtitles=add_subtitles,
            subtitle_text=narration_text  # Passa texto para legendas
        )
        
        final_video = Path(paths["video"]) / f"{video_name}.mp4"
        Path(video_path).rename(final_video)
        result["files"]["video"] = str(final_video)
        
        # 5. Final
        self.log.step(5, 5, "Finalizando...")
        save_json(result, str(Path(paths["root"]) / "metadata.json"))
        
        self.log.success("=" * 50)
        self.log.success("VIDEO CRIADO COM LEGENDAS!")
        self.log.info(f"Arquivo: {final_video}")
        
        return result

#!/usr/bin/env python3
"""
Content Automation Pipeline v3.0

Modos:
1. AUTOMÁTICO - IA gera tudo (roteiro, imagens, áudio, vídeo)
2. MANUAL - Você fornece imagens e roteiro

Execute:
    python main.py           # Menu interativo
    python main.py auto      # Modo automático direto
    python main.py manual    # Modo manual direto
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def show_menu():
    """Menu principal"""
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   CONTENT AUTOMATION PIPELINE v3.0                        ║
║                                                           ║
║   Escolha o modo:                                         ║
║                                                           ║
║   1. AUTOMÁTICO - IA gera tudo                            ║
║      (roteiro, imagens, áudio, vídeo)                     ║
║                                                           ║
║   2. MANUAL - Use suas próprias imagens e roteiro         ║
║      (você fornece imagens + texto)                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    choice = input("Escolha (1 ou 2): ").strip()
    
    return choice


def run_auto_mode():
    """Executa modo automático (IA gera tudo)"""
    
    from src.generators.text_generator import TextGenerator
    from src.generators.image_generator import ImageGenerator, STYLES
    from src.generators.audio_generator import AudioGenerator
    from src.generators.video_generator import VideoGenerator
    from src.utils.file_manager import create_project_folder, save_json, slugify
    from src.utils.logger import Logger
    from src.utils.image_resizer import SIZES
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║   MODO AUTOMÁTICO - IA gera tudo                          ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Tema
    topic = input("Digite o tema do vídeo: ").strip()
    if not topic:
        print("Tema não pode estar vazio!")
        return
    
    # Estilo
    print("\nEstilo das imagens:")
    print("  1. cartoon   - Desenho animado")
    print("  2. anime     - Anime japonês")
    print("  3. sketch    - Desenho a lápis")
    print("  4. watercolor - Aquarela")
    print("  5. comic     - Quadrinhos")
    print("  6. flat      - Design flat")
    print("  7. realistic - Fotos realistas")
    
    style_choice = input("\nEscolha (1-7) [1]: ").strip() or "1"
    style_map = {"1": "cartoon", "2": "anime", "3": "sketch", 
                 "4": "watercolor", "5": "comic", "6": "flat", "7": "realistic"}
    image_style = style_map.get(style_choice, "cartoon")
    
    # Formato
    print("\nFormato do vídeo:")
    print("  1. Short/Reels/TikTok (vertical)")
    print("  2. YouTube (horizontal)")
    print("  3. Quadrado (Instagram)")
    
    format_choice = input("\nEscolha (1-3) [1]: ").strip() or "1"
    format_map = {"1": "short", "2": "youtube", "3": "square"}
    video_format = format_map.get(format_choice, "short")
    
    # Segundos por imagem
    print("\nSegunos por imagem:")
    print("  1. 3 segundos (mais dinâmico)")
    print("  2. 5 segundos (equilibrado)")
    print("  3. 7 segundos (mais calmo)")
    
    speed_choice = input("\nEscolha (1-3) [2]: ").strip() or "2"
    speed_map = {"1": 3, "2": 5, "3": 7}
    seconds_per_image = speed_map.get(speed_choice, 5)
    
    # Importa e executa pipeline automático
    from main_auto import ContentPipeline
    
    pipeline = ContentPipeline(llm_provider="groq", image_style=image_style)
    
    if video_format == "short":
        result = pipeline.create_short(topic, seconds_per_image=seconds_per_image)
    elif video_format == "youtube":
        result = pipeline.create_youtube_video(topic, seconds_per_image=seconds_per_image)
    else:
        result = pipeline.create_square_video(topic, seconds_per_image=seconds_per_image)
    
    print(f"\nVídeo criado: {result['files']['video']}")


def run_manual_mode():
    """Executa modo manual (suas próprias imagens e roteiro)"""
    
    # Importa e executa
    from manual_mode import main as manual_main
    manual_main()


def main():
    # Verifica argumentos
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "auto":
            run_auto_mode()
        elif mode == "manual":
            run_manual_mode()
        else:
            # Assume que é um tema para modo automático
            sys.argv = [sys.argv[0]]  # Reset args
            run_auto_mode()
    else:
        # Menu interativo
        choice = show_menu()
        
        if choice == "1":
            run_auto_mode()
        elif choice == "2":
            run_manual_mode()
        else:
            print("Opção inválida!")


if __name__ == "__main__":
    main()

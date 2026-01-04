#!/usr/bin/env python3
"""
MODO MANUAL com Legendas Sincronizadas (2 palavras, borda grossa)

Como usar:
1. python manual_mode.py
2. Escolha "Criar novo projeto"
3. Coloque suas imagens na pasta images/
4. Edite o roteiro.txt
5. Escolha "Processar projeto"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.generators.audio_generator import AudioGenerator
from src.generators.video_generator import VideoGenerator
from src.utils.file_manager import slugify, save_json
from src.utils.logger import Logger
from src.utils.srt_generator import SRTGenerator


class ManualPipeline:
    """Pipeline manual com legendas sincronizadas"""
    
    def __init__(self):
        self.log = Logger("Manual")
        self.base_dir = Path("manual_projects")
        self.audio_gen = AudioGenerator(engine="edge")
        self.video_gen = VideoGenerator()
        self.srt_gen = SRTGenerator(words_per_subtitle=2)
    
    def list_projects(self) -> list:
        """Lista todos os projetos manuais"""
        if not self.base_dir.exists():
            return []
        
        projects = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                images_dir = item / "images"
                roteiro_file = item / "roteiro.txt"
                
                num_images = 0
                if images_dir.exists():
                    num_images = len(list(images_dir.glob("*.png")) + 
                                    list(images_dir.glob("*.jpg")) + 
                                    list(images_dir.glob("*.jpeg")) +
                                    list(images_dir.glob("*.webp")))
                
                projects.append({
                    "name": item.name,
                    "path": str(item),
                    "has_roteiro": roteiro_file.exists(),
                    "num_images": num_images
                })
        
        return projects
    
    def create_new_project(self, name: str) -> dict:
        """Cria estrutura para novo projeto"""
        
        project_dir = self.base_dir / slugify(name)
        images_dir = project_dir / "images"
        audio_dir = project_dir / "audio"
        video_dir = project_dir / "video"
        
        # Cria pastas
        images_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Cria roteiro modelo
        roteiro_path = project_dir / "roteiro.txt"
        if not roteiro_path.exists():
            roteiro_template = """TITULO: {name}

DESCRICAO: Escreva aqui a descricao do video para o YouTube.
Use varias linhas se precisar.

HASHTAGS: #shorts #viral #conteudo #foryou

NARRACAO:
Escreva aqui o texto completo que sera narrado.

IMPORTANTE: Este texto sera usado para:
1. Gerar o audio da narracao
2. Criar as legendas sincronizadas (2 palavras por vez)

Dicas:
- Comece com um gancho forte nos primeiros 3 segundos
- Use frases curtas e diretas
- Termine com uma chamada para acao

Exemplo de texto bom:
Voce sabia que o cerebro humano tem mais conexoes 
do que estrelas na galaxia? Isso mesmo! Sao mais de 
cem trilhoes de conexoes. Incrivel nao e? Deixa o like 
e segue para mais curiosidades!
""".format(name=name)
            
            roteiro_path.write_text(roteiro_template, encoding='utf-8')
        
        # Cria README com instrucoes
        readme_path = project_dir / "LEIA-ME.txt"
        readme_content = """
========================================
INSTRUCOES DO PROJETO
========================================

1. IMAGENS
   - Coloque suas imagens na pasta "images/"
   - Formatos aceitos: PNG, JPG, JPEG, WEBP
   - As imagens serao usadas na ordem alfabetica
   - Recomendado: nomear como 01.png, 02.png, 03.png...

2. ROTEIRO
   - Edite o arquivo "roteiro.txt"
   - Preencha o TITULO, DESCRICAO e HASHTAGS
   - Escreva a NARRACAO completa
   - O texto da narracao vira audio E legendas

3. LEGENDAS
   - Serao geradas automaticamente
   - 2 palavras por vez
   - Sincronizadas com o audio
   - Borda preta grossa, texto branco

4. PROCESSAR
   - Execute: python manual_mode.py
   - Escolha opcao 2 (Processar projeto)
   - Selecione este projeto
   - O video sera salvo na pasta "video/"

========================================
"""
        readme_path.write_text(readme_content, encoding='utf-8')
        
        self.log.success(f"Projeto criado: {project_dir}")
        self.log.info(f"")
        self.log.info(f"Proximos passos:")
        self.log.info(f"1. Coloque suas imagens em: {images_dir}")
        self.log.info(f"2. Edite o roteiro em: {roteiro_path}")
        self.log.info(f"3. Execute novamente e escolha 'Processar projeto'")
        
        return {
            "name": name,
            "path": str(project_dir),
            "images_dir": str(images_dir),
            "roteiro_path": str(roteiro_path)
        }
    
    def parse_roteiro(self, roteiro_path: str) -> dict:
        """Le e interpreta o arquivo de roteiro"""
        
        content = Path(roteiro_path).read_text(encoding='utf-8')
        
        result = {
            "titulo": "",
            "descricao": "",
            "hashtags": [],
            "narracao": ""
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith("TITULO:"):
                result["titulo"] = line_stripped.replace("TITULO:", "").strip()
                current_section = None
            
            elif line_stripped.startswith("DESCRICAO:"):
                result["descricao"] = line_stripped.replace("DESCRICAO:", "").strip()
                current_section = "descricao"
            
            elif line_stripped.startswith("HASHTAGS:"):
                hashtags_str = line_stripped.replace("HASHTAGS:", "").strip()
                result["hashtags"] = [h.strip() for h in hashtags_str.split() if h.startswith("#")]
                current_section = None
            
            elif line_stripped.startswith("NARRACAO:"):
                current_section = "narracao"
            
            elif current_section == "descricao" and line_stripped:
                result["descricao"] += " " + line_stripped
            
            elif current_section == "narracao":
                # Ignora linhas que comecam com # ou sao instrucoes
                if not line_stripped.startswith(("#", "IMPORTANTE", "Dicas:", "Exemplo", "-", "1.", "2.", "3.")):
                    result["narracao"] += line + "\n"
        
        # Limpa
        result["narracao"] = result["narracao"].strip()
        result["descricao"] = result["descricao"].strip()
        
        return result
    
    def get_images(self, images_dir: str) -> list:
        """Lista todas as imagens na pasta, ordenadas"""
        
        images_path = Path(images_dir)
        
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp']
        
        images = []
        for ext in extensions:
            images.extend(images_path.glob(ext))
        
        # Ordena por nome
        images = sorted(images, key=lambda x: x.name)
        
        return [str(img) for img in images]
    
    def preview_subtitles(self, text: str, duration: float):
        """Mostra preview das legendas que serao geradas"""
        
        timings = self.srt_gen.calculate_timings(text, duration)
        
        print("\n" + "=" * 60)
        print("PREVIEW DAS LEGENDAS (2 palavras por vez)")
        print("=" * 60)
        
        for t in timings[:15]:  # Mostra primeiras 15
            print(f"  {t['start']:5.2f}s - {t['end']:5.2f}s: {t['text'].upper()}")
        
        if len(timings) > 15:
            print(f"  ... e mais {len(timings) - 15} legendas")
        
        print("=" * 60)
        print(f"Total: {len(timings)} legendas para {duration:.1f}s de video")
        print()
    
    def process_project(self, 
                        project_name: str,
                        voice: str = "br_feminina",
                        speech_rate: str = "+5%",
                        format: str = "short",
                        add_subtitles: bool = True,
                        upload_youtube: bool = False) -> dict:
        """
        Processa um projeto manual completo
        COM LEGENDAS SINCRONIZADAS
        """
        
        project_dir = self.base_dir / project_name
        
        if not project_dir.exists():
            raise ValueError(f"Projeto nao encontrado: {project_dir}")
        
        self.log.info(f"Processando projeto: {project_name}")
        self.log.info(f"Legendas sincronizadas: {'Sim (2 palavras por frame)' if add_subtitles else 'Nao'}")
        
        images_dir = project_dir / "images"
        audio_dir = project_dir / "audio"
        video_dir = project_dir / "video"
        roteiro_path = project_dir / "roteiro.txt"
        
        # Garante que as pastas existem
        audio_dir.mkdir(exist_ok=True)
        video_dir.mkdir(exist_ok=True)
        
        result = {
            "project": project_name,
            "format": format,
            "subtitles": add_subtitles,
            "files": {}
        }
        
        # ========================================
        # PASSO 1: Ler Roteiro
        # ========================================
        self.log.step(1, 5, "Lendo roteiro...")
        
        if not roteiro_path.exists():
            raise ValueError(f"Roteiro nao encontrado: {roteiro_path}")
        
        roteiro = self.parse_roteiro(str(roteiro_path))
        result["roteiro"] = roteiro
        
        if not roteiro["narracao"]:
            raise ValueError("Narracao esta vazia! Edite o roteiro.txt")
        
        self.log.success(f"Titulo: {roteiro['titulo']}")
        self.log.info(f"Narracao: {len(roteiro['narracao'])} caracteres")
        self.log.info(f"Palavras: {len(roteiro['narracao'].split())} palavras")
        
        # ========================================
        # PASSO 2: Carregar Imagens
        # ========================================
        self.log.step(2, 5, "Carregando imagens...")
        
        images = self.get_images(str(images_dir))
        
        if not images:
            raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")
        
        result["files"]["images"] = images
        self.log.success(f"{len(images)} imagens encontradas:")
        
        for i, img in enumerate(images):
            self.log.info(f"  {i+1}. {Path(img).name}")
        
        # ========================================
        # PASSO 3: Gerar Audio
        # ========================================
        self.log.step(3, 5, "Gerando narracao...")
        
        audio_path = audio_dir / "narracao.mp3"
        narration_text = roteiro["narracao"]
        
        self.audio_gen.generate(
            text=narration_text,
            output_path=str(audio_path),
            voice=voice,
            rate=speech_rate
        )
        
        result["files"]["audio"] = str(audio_path)
        
        # Pega duracao do audio
        from moviepy.editor import AudioFileClip
        audio_clip = AudioFileClip(str(audio_path))
        audio_duration = audio_clip.duration
        audio_clip.close()
        
        self.log.success(f"Audio gerado: {audio_duration:.1f} segundos")
        
        # Preview das legendas
        if add_subtitles:
            self.preview_subtitles(narration_text, audio_duration)
        
        # ========================================
        # PASSO 4: Montar Video COM LEGENDAS
        # ========================================
        self.log.step(4, 5, "Montando video com legendas sincronizadas...")
        
        video_name = slugify(roteiro["titulo"] or project_name)
        
        # Caminho para salvar o SRT
        srt_path = video_dir / f"{video_name}.srt"
        
        video_path = self.video_gen.create_short(
            images=images,
            audio_path=str(audio_path),
            output_name=video_name,
            add_subtitles=add_subtitles,
            subtitle_text=narration_text,
            save_srt=True
        )
        
        # Move video para pasta do projeto
        final_video = video_dir / f"{video_name}.mp4"
        Path(video_path).rename(final_video)
        
        # Move SRT se foi gerado
        srt_source = self.video_gen.output_dir / f"{video_name}.srt"
        if srt_source.exists():
            srt_dest = video_dir / f"{video_name}.srt"
            srt_source.rename(srt_dest)
            result["files"]["srt"] = str(srt_dest)
            self.log.info(f"Arquivo SRT: {srt_dest}")
        
        result["files"]["video"] = str(final_video)
        self.log.success(f"Video criado: {final_video}")
        
        # ========================================
        # PASSO 5: Upload YouTube (Opcional)
        # ========================================
        if upload_youtube:
            self.log.step(5, 5, "Fazendo upload para YouTube...")
            
            try:
                from src.platforms.youtube_uploader import YouTubeUploader
                
                uploader = YouTubeUploader()
                
                # Monta descricao com hashtags
                description = roteiro["descricao"]
                if roteiro["hashtags"]:
                    description += "\n\n" + " ".join(roteiro["hashtags"])
                
                upload_result = uploader.upload_short(
                    video_path=str(final_video),
                    title=roteiro["titulo"],
                    description=description
                )
                
                result["youtube"] = upload_result
                self.log.success(f"Upload concluido!")
                self.log.info(f"URL: {upload_result['url']}")
                
            except Exception as e:
                self.log.error(f"Erro no upload: {e}")
                result["youtube_error"] = str(e)
        else:
            self.log.step(5, 5, "Finalizando...")
        
        # Salva metadata
        metadata_path = project_dir / "resultado.json"
        save_json(result, str(metadata_path))
        
        # Resumo final
        self.log.success("=" * 60)
        self.log.success("PROJETO PROCESSADO COM SUCESSO!")
        self.log.success("=" * 60)
        self.log.info(f"Video: {result['files']['video']}")
        self.log.info(f"Duracao: {audio_duration:.1f}s")
        self.log.info(f"Imagens: {len(images)}")
        self.log.info(f"Legendas: {'Sim (2 palavras, sincronizadas)' if add_subtitles else 'Nao'}")
        
        if "srt" in result["files"]:
            self.log.info(f"Arquivo SRT: {result['files']['srt']}")
        
        return result


def main():
    """Menu principal do modo manual"""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   MODO MANUAL - Use suas proprias imagens e roteiro           ║
║                                                               ║
║   RECURSOS:                                                   ║
║   - Legendas sincronizadas (2 palavras por vez)               ║
║   - Borda preta grossa                                        ║
║   - Efeitos Ken Burns (zoom/pan)                              ║
║   - Arquivo SRT gerado automaticamente                        ║
║                                                               ║
║   OPCOES:                                                     ║
║   1. Criar novo projeto                                       ║
║   2. Processar projeto existente                              ║
║   3. Listar projetos                                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    pipeline = ManualPipeline()
    
    choice = input("Escolha (1, 2 ou 3): ").strip()
    
    # ========================================
    # OPCAO 1: Criar novo projeto
    # ========================================
    if choice == "1":
        print("\n" + "=" * 50)
        print("CRIAR NOVO PROJETO")
        print("=" * 50)
        
        name = input("\nNome do projeto: ").strip()
        
        if name:
            result = pipeline.create_new_project(name)
            
            print("\n" + "=" * 50)
            print("PROJETO CRIADO!")
            print("=" * 50)
            print(f"\nPasta: {result['path']}")
            print(f"\nProximos passos:")
            print(f"  1. Coloque suas imagens em:")
            print(f"     {result['images_dir']}")
            print(f"\n  2. Edite o roteiro em:")
            print(f"     {result['roteiro_path']}")
            print(f"\n  3. Execute novamente e escolha opcao 2")
        else:
            print("Nome invalido!")
    
    # ========================================
    # OPCAO 2: Processar projeto
    # ========================================
    elif choice == "2":
        projects = pipeline.list_projects()
        
        if not projects:
            print("\nNenhum projeto encontrado!")
            print("Crie um projeto primeiro (opcao 1)")
            return
        
        print("\n" + "=" * 50)
        print("PROJETOS DISPONIVEIS")
        print("=" * 50)
        
        for i, proj in enumerate(projects):
            status_roteiro = "OK" if proj["has_roteiro"] else "FALTA"
            status_imgs = "OK" if proj["num_images"] > 0 else "FALTA"
            status = "PRONTO" if proj["has_roteiro"] and proj["num_images"] > 0 else "INCOMPLETO"
            
            print(f"\n  {i+1}. {proj['name']}")
            print(f"      Roteiro: {status_roteiro} | Imagens: {proj['num_images']} | Status: {status}")
        
        print()
        proj_choice = input("Numero do projeto: ").strip()
        
        try:
            proj_idx = int(proj_choice) - 1
            project = projects[proj_idx]
            
            if not project["has_roteiro"]:
                print("\nErro: Projeto nao tem roteiro.txt!")
                print(f"Crie o arquivo em: {project['path']}/roteiro.txt")
                return
            
            if project["num_images"] == 0:
                print("\nErro: Projeto nao tem imagens!")
                print(f"Coloque imagens em: {project['path']}/images/")
                return
            
            # Configuracoes
            print("\n" + "=" * 50)
            print("CONFIGURACOES")
            print("=" * 50)
            
            # Voz
            print("\nVoz da narracao:")
            print("  1. Feminina (Francisca) - Recomendada")
            print("  2. Masculina (Antonio)")
            
            voice_choice = input("\nEscolha (1 ou 2) [1]: ").strip() or "1"
            voice = "br_feminina" if voice_choice == "1" else "br_masculina"
            
            # Velocidade
            print("\nVelocidade da fala:")
            print("  1. Normal")
            print("  2. Um pouco mais rapido (+10%)")
            print("  3. Mais rapido (+20%)")
            
            speed_choice = input("\nEscolha (1, 2 ou 3) [2]: ").strip() or "2"
            speed_map = {"1": "+0%", "2": "+10%", "3": "+20%"}
            speech_rate = speed_map.get(speed_choice, "+10%")
            
            # Formato
            print("\nFormato do video:")
            print("  1. Short/Reels/TikTok (vertical 1080x1920)")
            print("  2. YouTube (horizontal 1920x1080)")
            print("  3. Quadrado (Instagram 1080x1080)")
            
            format_choice = input("\nEscolha (1, 2 ou 3) [1]: ").strip() or "1"
            format_map = {"1": "short", "2": "youtube", "3": "square"}
            video_format = format_map.get(format_choice, "short")
            
            # Legendas
            print("\nLegendas:")
            print("  - 2 palavras por vez")
            print("  - Borda preta grossa")
            print("  - Sincronizadas com audio")
            
            subtitles_choice = input("\nAdicionar legendas? (S/n) [S]: ").strip().lower()
            add_subtitles = subtitles_choice != "n"
            
            # Upload YouTube
            upload_choice = input("\nFazer upload para YouTube? (s/N) [N]: ").strip().lower()
            upload_youtube = upload_choice == "s"
            
            # Confirmacao
            print("\n" + "=" * 50)
            print("RESUMO")
            print("=" * 50)
            print(f"  Projeto: {project['name']}")
            print(f"  Imagens: {project['num_images']}")
            print(f"  Voz: {'Feminina' if voice == 'br_feminina' else 'Masculina'}")
            print(f"  Velocidade: {speech_rate}")
            print(f"  Formato: {video_format}")
            print(f"  Legendas: {'Sim' if add_subtitles else 'Nao'}")
            print(f"  Upload YouTube: {'Sim' if upload_youtube else 'Nao'}")
            
            confirm = input("\nConfirmar e processar? (S/n) [S]: ").strip().lower()
            
            if confirm != "n":
                print()
                result = pipeline.process_project(
                    project_name=project["name"],
                    voice=voice,
                    speech_rate=speech_rate,
                    format=video_format,
                    add_subtitles=add_subtitles,
                    upload_youtube=upload_youtube
                )
                
                print("\n" + "=" * 50)
                print("CONCLUIDO!")
                print("=" * 50)
                print(f"\nVideo: {result['files']['video']}")
                
                if "srt" in result["files"]:
                    print(f"SRT: {result['files']['srt']}")
            else:
                print("\nCancelado.")
            
        except (ValueError, IndexError):
            print("\nEscolha invalida!")
    
    # ========================================
    # OPCAO 3: Listar projetos
    # ========================================
    elif choice == "3":
        projects = pipeline.list_projects()
        
        if not projects:
            print("\nNenhum projeto encontrado!")
            print("Crie um com a opcao 1.")
            return
        
        print("\n" + "=" * 60)
        print("PROJETOS MANUAIS")
        print("=" * 60)
        
        for proj in projects:
            status = "PRONTO" if proj["has_roteiro"] and proj["num_images"] > 0 else "INCOMPLETO"
            
            print(f"\n{proj['name']}")
            print(f"  Pasta: {proj['path']}")
            print(f"  Imagens: {proj['num_images']}")
            print(f"  Roteiro: {'Sim' if proj['has_roteiro'] else 'Nao'}")
            print(f"  Status: {status}")
    
    else:
        print("\nOpcao invalida!")


if __name__ == "__main__":
    main()

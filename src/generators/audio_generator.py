"""
Gerador de áudio/narração usando Edge-TTS (Microsoft, gratuito)
CORRIGIDO: Funciona corretamente com bot async do Telegram
"""
import edge_tts
import asyncio
from pathlib import Path
from gtts import gTTS
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

# Vozes disponíveis em PT-BR
EDGE_VOICES = {
    # Chaves simplificadas (compatibilidade)
    "br_feminina": "pt-BR-FranciscaNeural",
    "br_masculina": "pt-BR-AntonioNeural",
    "pt_feminina": "pt-PT-RaquelNeural",
    "pt_masculina": "pt-PT-DuarteNeural",
    
    # Todas as vozes PT-BR disponíveis
    "antonio": "pt-BR-AntonioNeural",
    "francisca": "pt-BR-FranciscaNeural",
    "brenda": "pt-BR-BrendaNeural",
    "donato": "pt-BR-DonatoNeural",
    "elza": "pt-BR-ElzaNeural",
    "fabio": "pt-BR-FabioNeural",
    "giovanna": "pt-BR-GiovannaNeural",
    "humberto": "pt-BR-HumbertoNeural",
    "leila": "pt-BR-LeilaNeural",
    "leticia": "pt-BR-LeticiaNeural",
    "manuela": "pt-BR-ManuelaNeural",
    "nicolau": "pt-BR-NicolauNeural",
    "thalita": "pt-BR-ThalitaNeural",
    "valerio": "pt-BR-ValerioNeural",
    "yara": "pt-BR-YaraNeural",
}


class AudioGenerator:
    """Gera narração em áudio usando TTS gratuito"""
    
    def __init__(self, engine: str = "edge"):
        """
        Args:
            engine: "edge" (melhor qualidade) ou "gtts" (backup)
        """
        self.engine = engine
        self.voices = EDGE_VOICES
    
    def _parse_voice(self, voice: str) -> str:
        """Converte o nome da voz para o formato do Edge-TTS"""
        if voice.startswith("pt-") and "Neural" in voice:
            return voice
        
        voice_lower = voice.lower().replace("-", "_").replace(" ", "_")
        
        if voice_lower in self.voices:
            return self.voices[voice_lower]
        
        for key, value in self.voices.items():
            if voice_lower in key or voice_lower in value.lower():
                return value
        
        print(f"⚠️ Voz '{voice}' não encontrada, usando padrão (Francisca)")
        return "pt-BR-FranciscaNeural"
    
    def _parse_rate(self, rate) -> str:
        """
        Converte a velocidade para o formato do Edge-TTS
        
        IMPORTANTE: Edge-TTS usa formato "+XX%" ou "-XX%"
        - 1.0 = +0% (normal)
        - 1.2 = +20% (mais rápido)
        - 1.5 = +50% (bem mais rápido)
        - 0.8 = -20% (mais lento)
        """
        # Se já é string no formato correto
        if isinstance(rate, str):
            if "%" in rate:
                return rate
            # Tenta converter string numérica
            try:
                rate = float(rate)
            except:
                return "+0%"
        
        # Converte número para porcentagem
        try:
            rate_float = float(rate)
            
            # Converte: 1.0 = +0%, 1.2 = +20%, 0.8 = -20%
            percentage = int((rate_float - 1.0) * 100)
            
            if percentage >= 0:
                return f"+{percentage}%"
            else:
                return f"{percentage}%"
                
        except (ValueError, TypeError):
            return "+0%"
    
    async def _generate_edge_async(self,
                                    text: str,
                                    output_path: str,
                                    voice: str,
                                    rate: str) -> str:
        """Gera áudio usando Edge-TTS (método async interno)"""
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate
        )
        
        await communicate.save(output_path)
        return output_path
    
    def generate(self,
                 text: str,
                 output_path: str,
                 voice: str = "br_feminina",
                 rate = 1.0) -> str:
        """
        Gera áudio de narração (versão síncrona)
        
        Args:
            text: Texto para converter em fala
            output_path: Caminho do arquivo de saída (.mp3)
            voice: Tipo de voz
            rate: Velocidade (1.0 = normal, 1.2 = 20% mais rápido)
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        text = text.strip()
        if not text:
            print("⚠️ Texto vazio")
            return None
        
        # Parse dos parâmetros
        voice_name = self._parse_voice(voice)
        rate_str = self._parse_rate(rate)
        
        print(f"🎤 Gerando narração ({len(text)} caracteres)...")
        print(f"   Voz: {voice_name}")
        print(f"   Velocidade: {rate_str}")
        
        if self.engine == "edge":
            try:
                # Verifica se já existe um event loop rodando
                try:
                    loop = asyncio.get_running_loop()
                    # Se chegou aqui, já tem um loop rodando (contexto async)
                    # Usa run_until_complete em um novo loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._generate_edge_async(text, output_path, voice_name, rate_str)
                        )
                        future.result(timeout=120)
                except RuntimeError:
                    # Não tem loop rodando, pode usar asyncio.run normalmente
                    asyncio.run(
                        self._generate_edge_async(text, output_path, voice_name, rate_str)
                    )
                
                print(f"✅ Áudio salvo: {output_path}")
                return output_path
                
            except Exception as e:
                print(f"⚠️ Edge-TTS falhou: {e}")
                print("   Tentando gTTS...")
                self.engine = "gtts"
        
        if self.engine == "gtts":
            try:
                tts = gTTS(text=text, lang='pt-br')
                tts.save(output_path)
                print(f"✅ Áudio salvo (gTTS): {output_path}")
                return output_path
            except Exception as e:
                print(f"❌ gTTS falhou: {e}")
                return None
    
    async def generate_async(self,
                             text: str,
                             output_path: str,
                             voice: str = "br_feminina",
                             rate = 1.0) -> str:
        """
        Gera áudio de narração (versão assíncrona)
        USE ESTA VERSÃO NO BOT DO TELEGRAM!
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        text = text.strip()
        if not text:
            print("⚠️ Texto vazio")
            return None
        
        # Parse dos parâmetros
        voice_name = self._parse_voice(voice)
        rate_str = self._parse_rate(rate)
        
        print(f"🎤 Gerando narração ({len(text)} caracteres)...")
        print(f"   Voz: {voice_name}")
        print(f"   Velocidade: {rate_str}")
        
        try:
            await self._generate_edge_async(text, output_path, voice_name, rate_str)
            print(f"✅ Áudio salvo: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"⚠️ Edge-TTS falhou: {e}")
            # Fallback para gTTS (síncrono)
            try:
                tts = gTTS(text=text, lang='pt-br')
                tts.save(output_path)
                print(f"✅ Áudio salvo (gTTS): {output_path}")
                return output_path
            except Exception as e2:
                print(f"❌ gTTS também falhou: {e2}")
                return None
    
    @staticmethod
    def list_voices() -> dict:
        """Lista todas as vozes disponíveis"""
        voices_info = {
            "pt-BR-AntonioNeural": {"name": "Antonio", "gender": "Masculino"},
            "pt-BR-FranciscaNeural": {"name": "Francisca", "gender": "Feminino"},
            "pt-BR-BrendaNeural": {"name": "Brenda", "gender": "Feminino"},
            "pt-BR-DonatoNeural": {"name": "Donato", "gender": "Masculino"},
            "pt-BR-ElzaNeural": {"name": "Elza", "gender": "Feminino"},
            "pt-BR-FabioNeural": {"name": "Fabio", "gender": "Masculino"},
            "pt-BR-GiovannaNeural": {"name": "Giovanna", "gender": "Feminino"},
            "pt-BR-HumbertoNeural": {"name": "Humberto", "gender": "Masculino"},
            "pt-BR-ThalitaNeural": {"name": "Thalita", "gender": "Feminino"},
        }
        
        print("\n🎤 VOZES DISPONÍVEIS (PT-BR):")
        for voice_id, info in voices_info.items():
            icon = "🧔" if info["gender"] == "Masculino" else "👩"
            print(f"  {icon} {info['name']:12} | {voice_id}")
        
        return voices_info


# ===========================================
# TESTE
# ===========================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("TESTE AUDIO GENERATOR")
    print("="*50 + "\n")
    
    gen = AudioGenerator()
    
    # Teste com diferentes velocidades
    velocidades = [0.8, 1.0, 1.2, 1.5]
    
    for vel in velocidades:
        print(f"\n--- Velocidade {vel}x ---")
        gen.generate(
            text="Este é um teste de velocidade da narração.",
            output_path=f"output/audio/teste_vel_{vel}.mp3",
            voice="pt-BR-AntonioNeural",
            rate=vel
        )
    
    print("\n✅ Testes concluídos!")
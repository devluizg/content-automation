"""
Gerador de texto usando APIs gratuitas (Gemini e Groq)
v3: Com controle de duração para vídeos longos
"""
from pathlib import Path
import sys
import re
import json

sys.path.append(str(Path(__file__).parent.parent.parent))

# Tenta importar as bibliotecas
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ google-genai não instalado. Use: pip install google-genai")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ groq não instalado. Use: pip install groq")

from config.settings import GEMINI_API_KEY, GROQ_API_KEY


# ============================================
# CONFIGURAÇÕES DE DURAÇÃO
# ============================================

# Aproximadamente 2.5 palavras por segundo na narração
WORDS_PER_SECOND = 2.5

def calculate_word_count(duration_seconds: int) -> dict:
    """
    Calcula número de palavras necessárias para a duração desejada
    
    Args:
        duration_seconds: Duração alvo em segundos
        
    Returns:
        Dict com contagem de palavras para cada parte
    """
    total_words = int(duration_seconds * WORDS_PER_SECOND)
    
    return {
        "total": total_words,
        "hook": max(15, int(total_words * 0.08)),      # ~8% para hook
        "roteiro": int(total_words * 0.82),            # ~82% para conteúdo principal
        "cta": max(15, int(total_words * 0.10)),       # ~10% para CTA
        "min_total": int(total_words * 0.85),          # Mínimo aceitável (85%)
    }


# ============================================
# PROMPTS OTIMIZADOS
# ============================================

SYSTEM_PROMPT_STICKMAN = """
Você é um roteirista especializado em vídeos virais com animação de STICK FIGURES (bonecos de palito).

REGRAS PARA AS CENAS:
1. Cada cena deve descrever stick figures SIMPLES
2. Foque em AÇÕES e EMOÇÕES básicas
3. Máximo 2-3 personagens por cena
4. Use descrições CURTAS em inglês para busca_tenor

Para cada cena, forneça:
- descricao: O que acontece na cena (em português)
- busca_tenor: Termos de busca em INGLÊS para Tenor (2-4 palavras)
- emocao: A emoção principal

TERMOS DE BUSCA EFETIVOS:
stick figure thinking, stickman excited, stick figure confused, 
stick figure celebrating, stickman running, stick figure mind blown,
stickman thumbs up, stick figure explaining, stickman happy,
stick figure surprised, stickman dancing, stick figure working
"""

# Template para vídeos CURTOS (até 60s)
SCRIPT_TEMPLATE_SHORT = """
{system_prompt}

Crie um roteiro para um SHORT/REELS sobre: {topic}

DURAÇÃO: {duration_seconds} segundos (~{total_words} palavras no total)

RESPONDA APENAS COM JSON VÁLIDO:

{{
    "titulo": "título chamativo com emoji (máx 60 chars)",
    "hook": "ESCREVA ~{hook_words} PALAVRAS - frase impactante para prender atenção",
    "roteiro": "ESCREVA ~{roteiro_words} PALAVRAS - conteúdo principal da narração",
    "cta": "ESCREVA ~{cta_words} PALAVRAS - chamada para ação final",
    "descricao": "descrição para YouTube com emojis (2-3 linhas)",
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"],
    "cenas": [
{cenas_template}
    ]
}}

REGRAS:
1. Retorne APENAS JSON válido
2. O texto total deve ter aproximadamente {total_words} palavras
3. Cada "busca_tenor" deve ser ÚNICO
"""

# Template para vídeos LONGOS (mais de 60s)
SCRIPT_TEMPLATE_LONG = """
{system_prompt}

Crie um roteiro DETALHADO para um vídeo sobre: {topic}

═══════════════════════════════════════════════════
REQUISITOS DE DURAÇÃO (MUITO IMPORTANTE!):
═══════════════════════════════════════════════════
• Duração total: {duration_seconds} segundos ({duration_formatted})
• Palavras necessárias: ~{total_words} palavras
• Hook (abertura): ~{hook_words} palavras
• Conteúdo principal: ~{roteiro_words} palavras
• CTA (fechamento): ~{cta_words} palavras
• Número de cenas: {num_scenes}

O ROTEIRO PRECISA SER LONGO O SUFICIENTE PARA {duration_formatted} DE NARRAÇÃO!
═══════════════════════════════════════════════════

RESPONDA APENAS COM JSON VÁLIDO:

{{
    "titulo": "título chamativo com emoji (máx 60 chars)",
    
    "hook": "ESCREVA EXATAMENTE {hook_words} PALAVRAS aqui. Comece com uma pergunta ou fato surpreendente que prenda a atenção imediatamente.",
    
    "roteiro": "ESCREVA EXATAMENTE {roteiro_words} PALAVRAS aqui. Este é o conteúdo principal. Desenvolva o tema com: 1) Introdução do conceito, 2) Explicação detalhada com exemplos práticos, 3) Dados ou curiosidades interessantes, 4) Aplicação prática no dia a dia, 5) Benefícios e resultados. Use linguagem conversacional, faça perguntas retóricas, conte mini-histórias. IMPORTANTE: O texto deve ser longo e detalhado para preencher {duration_formatted} de narração.",
    
    "cta": "ESCREVA EXATAMENTE {cta_words} PALAVRAS aqui. Convide para curtir, comentar, compartilhar e seguir. Faça uma pergunta para gerar engajamento nos comentários.",
    
    "descricao": "descrição para YouTube com emojis (2-3 linhas)",
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5", "#hashtag6", "#hashtag7"],
    "cenas": [
{cenas_template}
    ]
}}

REGRAS CRÍTICAS:
1. O roteiro COMPLETO deve ter aproximadamente {total_words} palavras
2. Desenvolva CADA ponto com detalhes, exemplos e explicações
3. NÃO seja superficial - o vídeo tem {duration_formatted}, precisa de conteúdo!
4. Cada "busca_tenor" deve ser ÚNICO
5. Retorne APENAS JSON válido, sem markdown
"""


# Lista de emoções e termos de busca
EMOTION_SEARCH_TERMS = {
    "curious": ["thinking", "wondering", "pondering", "hmm"],
    "excited": ["excited", "jumping", "yay", "pumped"],
    "surprised": ["surprised", "shocked", "wow", "omg"],
    "happy": ["happy", "smiling", "joy", "celebrating"],
    "sad": ["sad", "crying", "disappointed", "depressed"],
    "angry": ["angry", "mad", "frustrated", "rage"],
    "confused": ["confused", "puzzled", "lost", "questioning"],
    "amazed": ["mind blown", "amazed", "impressed", "astonished"],
    "scared": ["scared", "afraid", "terrified", "nervous"],
    "love": ["love", "heart", "romantic", "adorable"],
    "bored": ["bored", "tired", "sleepy", "yawn"],
    "proud": ["proud", "confident", "victory", "winner"],
    "informative": ["explaining", "teaching", "pointing", "presenting"],
    "thinking": ["thinking", "pondering", "idea", "lightbulb"],
    "laughing": ["laughing", "lol", "funny", "hilarious"],
    "working": ["working", "typing", "busy", "focused"],
    "running": ["running", "fast", "hurry", "escape"],
    "dancing": ["dancing", "party", "groove", "moves"],
}

# Ações disponíveis para variedade
SEARCH_ACTIONS = [
    "thinking", "excited", "explaining", "surprised", "celebrating",
    "pointing", "happy", "thumbs up", "mind blown", "dancing",
    "confused", "working", "laughing", "running", "waving",
    "sad", "angry", "scared", "proud", "idea", "sleeping",
    "talking", "jumping", "clapping", "facepalm", "shrugging"
]


class TextGenerator:
    """Gera roteiros e textos usando IA - v3 com controle de duração"""
    
    def __init__(self, provider: str = "gemini"):
        """
        Args:
            provider: "gemini" ou "groq"
        """
        self.provider = provider.lower()
        self._setup_client()
        self._used_search_terms = set()
    
    def _setup_client(self):
        """Configura o cliente da API"""
        
        if self.provider == "gemini":
            if not GENAI_AVAILABLE:
                raise ImportError("google-genai não instalado. Use: pip install google-genai")
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY não configurada no .env")
            
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.model_name = "gemini-2.0-flash"
            print(f"✓ TextGenerator: Gemini ({self.model_name})")
        
        elif self.provider == "groq":
            if not GROQ_AVAILABLE:
                raise ImportError("groq não instalado. Use: pip install groq")
            if not GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY não configurada no .env")
            
            self.client = Groq(api_key=GROQ_API_KEY)
            self.model_name = "llama-3.3-70b-versatile"
            print(f"✓ TextGenerator: Groq ({self.model_name})")
        
        else:
            raise ValueError(f"Provider '{self.provider}' não suportado. Use 'gemini' ou 'groq'")
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Gera texto baseado em um prompt"""
        
        try:
            if self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            
            elif self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"❌ Erro ao gerar texto: {e}")
            raise
    
    def generate_short_script(self, topic: str, num_scenes: int = 6, 
                              target_duration: int = 30) -> dict:
        """
        Gera roteiro completo com duração controlada
        
        Args:
            topic: Tema do vídeo
            num_scenes: Número de cenas
            target_duration: Duração alvo em segundos (NOVO!)
            
        Returns:
            Dict com título, roteiro, cenas, etc.
        """
        # Reseta termos usados
        self._used_search_terms = set()
        
        # Calcula palavras necessárias
        word_config = calculate_word_count(target_duration)
        
        # Formata duração para exibição
        duration_formatted = self._format_duration(target_duration)
        
        print(f"\n📝 Gerando roteiro: {topic}")
        print(f"   ⏱️ Duração alvo: {duration_formatted}")
        print(f"   📊 Palavras alvo: ~{word_config['total']}")
        print(f"   🎬 Cenas: {num_scenes}")
        
        # Gera template de cenas
        cenas_template = self._generate_cenas_template(num_scenes)
        
        # Escolhe template baseado na duração
        if target_duration <= 60:
            template = SCRIPT_TEMPLATE_SHORT
        else:
            template = SCRIPT_TEMPLATE_LONG
        
        # Monta o prompt
        prompt = template.format(
            system_prompt=SYSTEM_PROMPT_STICKMAN,
            topic=topic,
            duration_seconds=target_duration,
            duration_formatted=duration_formatted,
            total_words=word_config['total'],
            hook_words=word_config['hook'],
            roteiro_words=word_config['roteiro'],
            cta_words=word_config['cta'],
            num_scenes=num_scenes,
            cenas_template=cenas_template
        )
        
        # Ajusta max_tokens baseado na duração
        max_tokens = max(2000, min(8000, word_config['total'] * 3))
        
        # Gera o roteiro
        result = self._generate_and_parse(prompt, max_tokens)
        
        # Se falhou ou ficou muito curto, tenta método alternativo
        if not result or not result.get("roteiro"):
            print("   ⚠️ JSON falhou, usando método alternativo...")
            result = self._generate_with_expansion(topic, num_scenes, word_config, duration_formatted)
        
        # Verifica se precisa expandir
        result = self._ensure_minimum_length(result, topic, word_config, duration_formatted)
        
        # Garante número correto de cenas
        result["cenas"] = self._ensure_scene_count(result.get("cenas", []), num_scenes, topic)
        
        # Garante termos de busca únicos
        result["cenas"] = self._ensure_search_terms(result["cenas"])
        
        # Monta narração completa
        result["narracao"] = self._build_narration(result)
        result["topic"] = topic
        result["target_duration"] = target_duration
        
        # Log do resultado
        actual_words = len(result["narracao"].split())
        estimated_duration = actual_words / WORDS_PER_SECOND
        
        print(f"\n   ✅ Roteiro gerado:")
        print(f"      Palavras: {actual_words} (alvo: {word_config['total']})")
        print(f"      Duração estimada: {self._format_duration(int(estimated_duration))}")
        print(f"      Cenas: {len(result['cenas'])}")
        
        # Aviso se ficou muito diferente do esperado
        ratio = actual_words / word_config['total'] if word_config['total'] > 0 else 0
        if ratio < 0.7:
            print(f"      ⚠️ AVISO: Roteiro {int((1-ratio)*100)}% menor que o esperado!")
        elif ratio > 1.3:
            print(f"      ⚠️ AVISO: Roteiro {int((ratio-1)*100)}% maior que o esperado!")
        
        return result
    
    def _format_duration(self, seconds: int) -> str:
        """Formata duração em texto legível"""
        if seconds >= 60:
            mins = seconds // 60
            secs = seconds % 60
            if secs > 0:
                return f"{mins}min {secs}s"
            return f"{mins} minutos"
        return f"{seconds} segundos"
    
    def _generate_cenas_template(self, num_scenes: int) -> str:
        """Gera template JSON para as cenas"""
        cenas = []
        
        for i in range(num_scenes):
            action = SEARCH_ACTIONS[i % len(SEARCH_ACTIONS)]
            emotion = list(EMOTION_SEARCH_TERMS.keys())[i % len(EMOTION_SEARCH_TERMS)]
            prefix = "stick figure" if i % 2 == 0 else "stickman"
            
            cenas.append(f'''        {{
            "descricao": "descrição da cena {i+1} em português",
            "busca_tenor": "{prefix} {action}",
            "emocao": "{emotion}"
        }}''')
        
        return ",\n".join(cenas)
    
    def _generate_and_parse(self, prompt: str, max_tokens: int) -> dict:
        """Gera e faz parse do JSON"""
        try:
            response = self.generate(prompt, temperature=0.7, max_tokens=max_tokens)
            json_str = self._extract_json(response)
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Erro ao parsear JSON: {e}")
            return {}
        except Exception as e:
            print(f"   ⚠️ Erro na geração: {e}")
            return {}
    
    def _extract_json(self, response: str) -> str:
        """Extrai JSON da resposta"""
        # Remove blocos de código markdown
        response = re.sub(r'^```json\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'^```\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'```$', '', response, flags=re.MULTILINE)
        
        # Encontra o JSON
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return match.group(0)
        
        return response.strip()
    
    def _generate_with_expansion(self, topic: str, num_scenes: int, 
                                  word_config: dict, duration_formatted: str) -> dict:
        """Gera roteiro em partes quando JSON falha"""
        
        result = {
            "titulo": "",
            "hook": "",
            "roteiro": "",
            "cta": "",
            "descricao": "",
            "hashtags": [],
            "cenas": []
        }
        
        # Gera título
        try:
            title_prompt = f"Crie um título chamativo com emoji (máximo 60 caracteres) para um vídeo sobre: {topic}\n\nResponda APENAS com o título, nada mais."
            result["titulo"] = self.generate(title_prompt, temperature=0.8, max_tokens=100).strip().strip('"')
        except:
            result["titulo"] = f"🔥 {topic.title()}"
        
        # Gera hook
        try:
            hook_prompt = f"Crie uma frase de abertura impactante ({word_config['hook']} palavras) para um vídeo sobre: {topic}\n\nResponda APENAS com a frase, nada mais."
            result["hook"] = self.generate(hook_prompt, temperature=0.8, max_tokens=200).strip().strip('"')
        except:
            result["hook"] = f"Você sabia que {topic}? Isso vai mudar sua perspectiva!"
        
        # Gera conteúdo principal (parte mais importante)
        try:
            roteiro_prompt = f"""
Escreva o conteúdo principal de um vídeo sobre: {topic}

REQUISITOS:
- Deve ter EXATAMENTE {word_config['roteiro']} palavras
- Duração quando narrado: {duration_formatted}
- Tom conversacional e envolvente
- Inclua exemplos práticos
- Faça perguntas retóricas
- Desenvolva cada ponto com detalhes

Escreva APENAS o texto, sem formatação ou marcadores.
"""
            result["roteiro"] = self.generate(roteiro_prompt, temperature=0.7, max_tokens=4000).strip()
        except Exception as e:
            print(f"   ⚠️ Erro ao gerar roteiro: {e}")
            result["roteiro"] = f"Vamos falar sobre {topic}. Este é um tema muito interessante que merece nossa atenção."
        
        # Gera CTA
        try:
            cta_prompt = f"Crie uma chamada para ação final ({word_config['cta']} palavras) convidando a curtir, comentar e seguir. Faça uma pergunta para engajamento.\n\nResponda APENAS com o texto, nada mais."
            result["cta"] = self.generate(cta_prompt, temperature=0.8, max_tokens=200).strip().strip('"')
        except:
            result["cta"] = "Gostou desse conteúdo? Deixa seu like, comenta aqui embaixo o que você achou, e se inscreve no canal para mais vídeos como esse!"
        
        # Gera descrição
        result["descricao"] = f"🎬 {topic}\n\n📌 Neste vídeo você vai aprender tudo sobre {topic}!\n\n👆 Ative o sininho para não perder nenhum conteúdo!"
        
        # Gera hashtags
        topic_words = topic.lower().split()[:3]
        result["hashtags"] = [f"#{w}" for w in topic_words] + ["#shorts", "#viral", "#dicasúteis", "#aprendizado"]
        
        return result
    
    def _ensure_minimum_length(self, result: dict, topic: str, 
                                word_config: dict, duration_formatted: str) -> dict:
        """Garante que o roteiro tem o tamanho mínimo necessário"""
        
        if not result:
            result = {}
        
        # Calcula palavras atuais
        current_words = 0
        for key in ['hook', 'roteiro', 'cta']:
            current_words += len(result.get(key, '').split())
        
        target_words = word_config['total']
        min_words = word_config['min_total']
        
        print(f"   📊 Verificando tamanho: {current_words}/{target_words} palavras")
        
        # Se está muito curto, expande
        if current_words < min_words:
            print(f"   🔄 Roteiro curto ({current_words} palavras), expandindo...")
            result = self._expand_script(result, topic, word_config, duration_formatted)
        
        return result
    
    def _expand_script(self, result: dict, topic: str, 
                       word_config: dict, duration_formatted: str) -> dict:
        """Expande um roteiro que ficou muito curto"""
        
        current_roteiro = result.get('roteiro', '')
        current_words = len(current_roteiro.split())
        needed_words = word_config['roteiro']
        
        if current_words >= needed_words * 0.8:
            return result  # Já está bom o suficiente
        
        expand_prompt = f"""
Expanda o seguinte roteiro sobre "{topic}" para ter aproximadamente {needed_words} palavras.

═══════════════════════════════════════════════════
ROTEIRO ATUAL ({current_words} palavras):
═══════════════════════════════════════════════════
{current_roteiro}
═══════════════════════════════════════════════════

INSTRUÇÕES:
1. Mantenha o mesmo tom e estilo
2. Adicione MUITO mais detalhes, exemplos e explicações
3. O resultado DEVE ter aproximadamente {needed_words} palavras
4. O vídeo tem {duration_formatted}, então PRECISA de conteúdo suficiente
5. Desenvolva cada ponto mencionado
6. Adicione estatísticas, curiosidades ou histórias

Escreva APENAS o texto expandido, sem formatação ou comentários.
"""
        
        try:
            expanded = self.generate(expand_prompt, temperature=0.7, max_tokens=5000)
            expanded = expanded.strip()
            
            # Remove possíveis aspas ou formatação
            if expanded.startswith('"') and expanded.endswith('"'):
                expanded = expanded[1:-1]
            if expanded.startswith("```") or expanded.startswith("Roteiro"):
                # Tenta extrair apenas o texto
                lines = expanded.split('\n')
                expanded = '\n'.join([l for l in lines if not l.startswith('```') and not l.startswith('═')])
            
            new_words = len(expanded.split())
            
            if new_words > current_words:
                result['roteiro'] = expanded
                print(f"   ✅ Roteiro expandido: {current_words} → {new_words} palavras")
            else:
                print(f"   ⚠️ Expansão não aumentou ({new_words} palavras)")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao expandir: {e}")
        
        return result
    
    def _ensure_scene_count(self, cenas: list, target_count: int, topic: str) -> list:
        """Garante o número correto de cenas"""
        
        # Converte strings para dicts
        processed = []
        for i, cena in enumerate(cenas):
            if isinstance(cena, str):
                action = SEARCH_ACTIONS[i % len(SEARCH_ACTIONS)]
                prefix = "stick figure" if i % 2 == 0 else "stickman"
                processed.append({
                    "descricao": cena,
                    "busca_tenor": f"{prefix} {action}",
                    "emocao": list(EMOTION_SEARCH_TERMS.keys())[i % len(EMOTION_SEARCH_TERMS)]
                })
            elif isinstance(cena, dict):
                processed.append(cena)
        
        # Adiciona cenas se faltando
        while len(processed) < target_count:
            idx = len(processed)
            action = SEARCH_ACTIONS[idx % len(SEARCH_ACTIONS)]
            prefix = "stick figure" if idx % 2 == 0 else "stickman"
            emotion = list(EMOTION_SEARCH_TERMS.keys())[idx % len(EMOTION_SEARCH_TERMS)]
            
            processed.append({
                "descricao": f"Cena {idx + 1} ilustrando o conceito sobre {topic}",
                "busca_tenor": f"{prefix} {action}",
                "emocao": emotion
            })
        
        # Remove excesso
        if len(processed) > target_count:
            processed = processed[:target_count]
        
        return processed
    
    def _ensure_search_terms(self, cenas: list) -> list:
        """Garante que todas as cenas têm termos de busca únicos"""
        
        used_terms = set()
        result = []
        
        for i, cena in enumerate(cenas):
            if isinstance(cena, str):
                cena = {
                    "descricao": cena,
                    "busca_tenor": "",
                    "emocao": "neutral"
                }
            
            if not isinstance(cena, dict):
                cena = {"descricao": str(cena), "busca_tenor": "", "emocao": "neutral"}
            
            # Verifica/gera busca_tenor único
            busca = cena.get("busca_tenor", "")
            
            if not busca or busca in used_terms:
                busca = self._generate_unique_search_term(i, used_terms)
            
            used_terms.add(busca)
            cena["busca_tenor"] = busca
            
            # Garante emoção
            if not cena.get("emocao"):
                cena["emocao"] = list(EMOTION_SEARCH_TERMS.keys())[i % len(EMOTION_SEARCH_TERMS)]
            
            result.append(cena)
        
        return result
    
    def _generate_unique_search_term(self, index: int, used: set) -> str:
        """Gera um termo de busca único"""
        
        # Tenta ações em ordem
        for offset in range(len(SEARCH_ACTIONS)):
            action_idx = (index + offset) % len(SEARCH_ACTIONS)
            action = SEARCH_ACTIONS[action_idx]
            
            # Alterna entre prefixos
            for prefix in ["stick figure", "stickman"]:
                term = f"{prefix} {action}"
                if term not in used:
                    return term
        
        # Último recurso: adiciona número
        return f"stick figure animation {index + 1}"
    
    def _build_narration(self, result: dict) -> str:
        """Monta a narração completa"""
        parts = []
        
        if result.get("hook"):
            parts.append(result["hook"])
        
        if result.get("roteiro"):
            parts.append(result["roteiro"])
        
        if result.get("cta"):
            parts.append(result["cta"])
        
        return " ".join(parts)
    
    def generate_post(self, topic: str, platform: str = "instagram") -> dict:
        """Gera texto para post em redes sociais"""
        
        prompt = f"""
Crie um post viral para {platform} sobre: {topic}

FORMATO:
TEXTO: [texto do post com emojis estratégicos, máximo 300 caracteres]
HASHTAGS: [8-10 hashtags relevantes e populares]
"""
        
        response = self.generate(prompt)
        return {
            "content": response, 
            "platform": platform,
            "topic": topic
        }
    
    def change_provider(self, provider: str):
        """Muda o provider de IA"""
        self.provider = provider.lower()
        self._setup_client()


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def get_scene_descriptions(cenas: list) -> list:
    """Extrai apenas as descrições das cenas"""
    return [
        c.get("descricao", c) if isinstance(c, dict) else c
        for c in cenas
    ]

def get_search_terms(cenas: list) -> list:
    """Extrai os termos de busca das cenas"""
    return [
        c.get("busca_tenor", "stick figure") if isinstance(c, dict) else "stick figure"
        for c in cenas
    ]


# ============================================
# TESTE
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTE: TextGenerator v3 (Com controle de duração)")
    print("="*60 + "\n")
    
    # Tenta Groq primeiro
    try:
        gen = TextGenerator(provider="groq")
        provider_ok = "groq"
    except Exception as e:
        print(f"⚠️ Groq não disponível: {e}")
        try:
            gen = TextGenerator(provider="gemini")
            provider_ok = "gemini"
        except Exception as e2:
            print(f"❌ Gemini também não disponível: {e2}")
            exit(1)
    
    print(f"✓ Usando provider: {provider_ok}\n")
    
    # Teste 1: Short (30s)
    print("="*50)
    print("📹 TESTE 1: Short 30 segundos")
    print("="*50)
    
    script_short = gen.generate_short_script(
        topic="3 dicas de produtividade",
        num_scenes=6,
        target_duration=30
    )
    
    words_short = len(script_short.get('narracao', '').split())
    print(f"\n📊 Resultado: {words_short} palavras (~{words_short/2.5:.0f}s)")
    
    # Teste 2: Vídeo longo (3 min)
    print("\n" + "="*50)
    print("📹 TESTE 2: YouTube 3 minutos")
    print("="*50)
    
    script_long = gen.generate_short_script(
        topic="5 hábitos que vão mudar sua vida",
        num_scenes=36,
        target_duration=180
    )
    
    words_long = len(script_long.get('narracao', '').split())
    print(f"\n📊 Resultado: {words_long} palavras (~{words_long/2.5:.0f}s)")
    
    # Mostra amostra do roteiro longo
    print(f"\n📝 Amostra do roteiro:")
    print(f"   {script_long.get('narracao', '')[:500]}...")
    
    print(f"\n🎬 Cenas geradas: {len(script_long.get('cenas', []))}")
    
    print("\n" + "="*60)
    print("✅ Testes concluídos!")
    print("="*60 + "\n")
"""
Avaliador de APIs de Imagens
Compara: Tenor, Giphy, Pixabay, Pexels, Unsplash
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import json

load_dotenv()

# Pasta para salvar amostras
SAMPLES_DIR = Path("output/api_samples")
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


class ImageAPITester:
    """Testa e compara diferentes APIs de imagens"""
    
    def __init__(self):
        self.tenor_key = os.getenv("TENOR_API_KEY")
        self.giphy_key = os.getenv("GIPHY_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    
    # ===========================================
    # TENOR
    # ===========================================
    def search_tenor(self, query: str, limit: int = 10) -> list:
        """Busca no Tenor"""
        if not self.tenor_key:
            print("❌ TENOR_API_KEY não configurada")
            return []
        
        try:
            url = "https://tenor.googleapis.com/v2/search"
            params = {
                "q": query,
                "key": self.tenor_key,
                "limit": limit,
                "media_filter": "gif,mp4"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                
                processed = []
                for r in results:
                    media = r.get("media_formats", {})
                    
                    # Pega a melhor qualidade disponível
                    gif_info = media.get("gif", {})
                    mp4_info = media.get("mp4", {})
                    
                    processed.append({
                        "id": r.get("id"),
                        "title": r.get("content_description", "")[:50],
                        "gif_url": gif_info.get("url"),
                        "gif_size": f"{gif_info.get('dims', [0,0])[0]}x{gif_info.get('dims', [0,0])[1]}",
                        "mp4_url": mp4_info.get("url"),
                        "mp4_size": f"{mp4_info.get('dims', [0,0])[0]}x{mp4_info.get('dims', [0,0])[1]}",
                        "source": "tenor"
                    })
                
                return processed
            else:
                print(f"❌ Tenor erro: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Tenor exceção: {e}")
            return []
    
    # ===========================================
    # GIPHY
    # ===========================================
    def search_giphy(self, query: str, limit: int = 10) -> list:
        """Busca no Giphy"""
        if not self.giphy_key:
            print("❌ GIPHY_API_KEY não configurada")
            return []
        
        try:
            # Busca GIFs normais
            url = "https://api.giphy.com/v1/gifs/search"
            params = {
                "api_key": self.giphy_key,
                "q": query,
                "limit": limit,
                "rating": "g"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get("data", [])
                
                processed = []
                for r in results:
                    images = r.get("images", {})
                    
                    # Diferentes qualidades disponíveis
                    original = images.get("original", {})
                    downsized = images.get("downsized_large", {})
                    hd = images.get("hd", {})
                    
                    processed.append({
                        "id": r.get("id"),
                        "title": r.get("title", "")[:50],
                        "original_url": original.get("url"),
                        "original_size": f"{original.get('width', 0)}x{original.get('height', 0)}",
                        "hd_url": hd.get("mp4") if hd else None,
                        "hd_size": f"{hd.get('width', 0)}x{hd.get('height', 0)}" if hd else "N/A",
                        "source": "giphy"
                    })
                
                return processed
            else:
                print(f"❌ Giphy erro: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Giphy exceção: {e}")
            return []
    
    # ===========================================
    # PIXABAY (Imagens estáticas de alta qualidade)
    # ===========================================
    def search_pixabay(self, query: str, limit: int = 10, orientation: str = "vertical") -> list:
        """
        Busca no Pixabay
        orientation: "all", "horizontal", "vertical"
        """
        if not self.pixabay_key:
            print("❌ PIXABAY_API_KEY não configurada")
            return []
        
        try:
            url = "https://pixabay.com/api/"
            params = {
                "key": self.pixabay_key,
                "q": query,
                "per_page": limit,
                "orientation": orientation,
                "image_type": "illustration",  # illustration, photo, vector
                "safesearch": "true",
                "min_width": 1080,
                "min_height": 1920
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get("hits", [])
                
                processed = []
                for r in results:
                    processed.append({
                        "id": r.get("id"),
                        "title": r.get("tags", "")[:50],
                        "preview_url": r.get("webformatURL"),
                        "preview_size": f"{r.get('webformatWidth', 0)}x{r.get('webformatHeight', 0)}",
                        "full_url": r.get("largeImageURL"),
                        "full_size": f"{r.get('imageWidth', 0)}x{r.get('imageHeight', 0)}",
                        "source": "pixabay"
                    })
                
                return processed
            else:
                print(f"❌ Pixabay erro: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Pixabay exceção: {e}")
            return []
    
    # ===========================================
    # PEXELS (Fotos/Vídeos de alta qualidade)
    # ===========================================
    def search_pexels(self, query: str, limit: int = 10, orientation: str = "portrait") -> list:
        """
        Busca no Pexels
        orientation: "landscape", "portrait", "square"
        """
        if not self.pexels_key:
            print("❌ PEXELS_API_KEY não configurada")
            return []
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_key}
            params = {
                "query": query,
                "per_page": limit,
                "orientation": orientation
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get("photos", [])
                
                processed = []
                for r in results:
                    src = r.get("src", {})
                    
                    processed.append({
                        "id": r.get("id"),
                        "title": r.get("alt", "")[:50],
                        "original_url": src.get("original"),
                        "original_size": f"{r.get('width', 0)}x{r.get('height', 0)}",
                        "large_url": src.get("large2x"),
                        "portrait_url": src.get("portrait"),  # 800x1200
                        "source": "pexels"
                    })
                
                return processed
            else:
                print(f"❌ Pexels erro: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Pexels exceção: {e}")
            return []
    
    # ===========================================
    # UNSPLASH (Fotos artísticas)
    # ===========================================
    def search_unsplash(self, query: str, limit: int = 10, orientation: str = "portrait") -> list:
        """
        Busca no Unsplash
        orientation: "landscape", "portrait", "squarish"
        """
        if not self.unsplash_key:
            print("❌ UNSPLASH_ACCESS_KEY não configurada")
            return []
        
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
            params = {
                "query": query,
                "per_page": limit,
                "orientation": orientation
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                
                processed = []
                for r in results:
                    urls = r.get("urls", {})
                    
                    processed.append({
                        "id": r.get("id"),
                        "title": r.get("alt_description", "")[:50] if r.get("alt_description") else "N/A",
                        "thumb_url": urls.get("thumb"),
                        "regular_url": urls.get("regular"),  # 1080px
                        "full_url": urls.get("full"),
                        "raw_url": urls.get("raw"),  # Máxima qualidade
                        "size": f"{r.get('width', 0)}x{r.get('height', 0)}",
                        "source": "unsplash"
                    })
                
                return processed
            else:
                print(f"❌ Unsplash erro: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Unsplash exceção: {e}")
            return []
    
    # ===========================================
    # DOWNLOAD DE AMOSTRA
    # ===========================================
    def download_sample(self, url: str, filename: str) -> str:
        """Baixa uma imagem de amostra"""
        try:
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                filepath = SAMPLES_DIR / filename
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return str(filepath)
        except Exception as e:
            print(f"❌ Erro ao baixar: {e}")
        
        return None
    
    # ===========================================
    # COMPARAÇÃO COMPLETA
    # ===========================================
    def compare_all(self, query: str, download_samples: bool = True):
        """Compara todas as APIs disponíveis"""
        
        print("\n" + "="*60)
        print(f"🔍 COMPARANDO APIs - Busca: '{query}'")
        print("="*60)
        
        # Tenor
        print("\n" + "-"*40)
        print("🎭 TENOR (GIFs/Stickers)")
        print("-"*40)
        tenor_results = self.search_tenor(query, limit=5)
        if tenor_results:
            for i, r in enumerate(tenor_results):
                print(f"  {i+1}. {r['title']}")
                print(f"     GIF: {r['gif_size']} | MP4: {r['mp4_size']}")
            
            if download_samples and tenor_results[0].get("gif_url"):
                path = self.download_sample(
                    tenor_results[0]["gif_url"], 
                    f"tenor_{query.replace(' ', '_')}.gif"
                )
                if path:
                    print(f"  📥 Amostra: {path}")
        else:
            print("  Nenhum resultado")
        
        # Giphy
        print("\n" + "-"*40)
        print("🎬 GIPHY (GIFs)")
        print("-"*40)
        giphy_results = self.search_giphy(query, limit=5)
        if giphy_results:
            for i, r in enumerate(giphy_results):
                print(f"  {i+1}. {r['title']}")
                print(f"     Original: {r['original_size']} | HD: {r['hd_size']}")
            
            if download_samples and giphy_results[0].get("original_url"):
                path = self.download_sample(
                    giphy_results[0]["original_url"], 
                    f"giphy_{query.replace(' ', '_')}.gif"
                )
                if path:
                    print(f"  📥 Amostra: {path}")
        else:
            print("  Nenhum resultado")
        
        # Pixabay
        print("\n" + "-"*40)
        print("🖼️ PIXABAY (Ilustrações VERTICAIS)")
        print("-"*40)
        pixabay_results = self.search_pixabay(query, limit=5, orientation="vertical")
        if pixabay_results:
            for i, r in enumerate(pixabay_results):
                print(f"  {i+1}. {r['title']}")
                print(f"     Full: {r['full_size']}")
            
            if download_samples and pixabay_results[0].get("full_url"):
                path = self.download_sample(
                    pixabay_results[0]["full_url"], 
                    f"pixabay_{query.replace(' ', '_')}.jpg"
                )
                if path:
                    print(f"  📥 Amostra: {path}")
        else:
            print("  Nenhum resultado")
        
        # Pexels
        print("\n" + "-"*40)
        print("📷 PEXELS (Fotos PORTRAIT)")
        print("-"*40)
        pexels_results = self.search_pexels(query, limit=5, orientation="portrait")
        if pexels_results:
            for i, r in enumerate(pexels_results):
                print(f"  {i+1}. {r['title']}")
                print(f"     Original: {r['original_size']}")
            
            if download_samples and pexels_results[0].get("large_url"):
                path = self.download_sample(
                    pexels_results[0]["large_url"], 
                    f"pexels_{query.replace(' ', '_')}.jpg"
                )
                if path:
                    print(f"  📥 Amostra: {path}")
        else:
            print("  Nenhum resultado")
        
        # Unsplash
        print("\n" + "-"*40)
        print("🎨 UNSPLASH (Fotos artísticas)")
        print("-"*40)
        unsplash_results = self.search_unsplash(query, limit=5, orientation="portrait")
        if unsplash_results:
            for i, r in enumerate(unsplash_results):
                print(f"  {i+1}. {r['title']}")
                print(f"     Tamanho: {r['size']}")
            
            if download_samples and unsplash_results[0].get("regular_url"):
                path = self.download_sample(
                    unsplash_results[0]["regular_url"], 
                    f"unsplash_{query.replace(' ', '_')}.jpg"
                )
                if path:
                    print(f"  📥 Amostra: {path}")
        else:
            print("  Nenhum resultado")
        
        # Resumo
        print("\n" + "="*60)
        print("📊 RESUMO")
        print("="*60)
        print(f"""
| API      | Resultados | Melhor Para              | Orientação |
|----------|------------|--------------------------|------------|
| Tenor    | {len(tenor_results):2}         | GIFs animados, memes     | Horizontal |
| Giphy    | {len(giphy_results):2}         | GIFs animados            | Horizontal |
| Pixabay  | {len(pixabay_results):2}         | Ilustrações, vetores     | ✅ Vertical |
| Pexels   | {len(pexels_results):2}         | Fotos reais              | ✅ Vertical |
| Unsplash | {len(unsplash_results):2}         | Fotos artísticas         | ✅ Vertical |
        """)
        
        if download_samples:
            print(f"📁 Amostras salvas em: {SAMPLES_DIR.absolute()}")


def main():
    """Menu interativo para testar APIs"""
    
    tester = ImageAPITester()
    
    print("\n" + "="*60)
    print("🔬 AVALIADOR DE APIs DE IMAGENS")
    print("="*60)
    
    # Verifica quais APIs estão configuradas
    print("\n📋 APIs Configuradas:")
    print(f"  • Tenor:   {'✅' if tester.tenor_key else '❌'}")
    print(f"  • Giphy:   {'✅' if tester.giphy_key else '❌'}")
    print(f"  • Pixabay: {'✅' if tester.pixabay_key else '❌'}")
    print(f"  • Pexels:  {'✅' if tester.pexels_key else '❌'}")
    print(f"  • Unsplash:{'✅' if tester.unsplash_key else '❌'}")
    
    while True:
        print("\n" + "-"*40)
        print("OPÇÕES:")
        print("  1. Comparar TODAS as APIs")
        print("  2. Testar só Tenor")
        print("  3. Testar só Giphy")
        print("  4. Testar só Pixabay")
        print("  5. Testar só Pexels")
        print("  6. Testar só Unsplash")
        print("  0. Sair")
        print("-"*40)
        
        choice = input("\nEscolha: ").strip()
        
        if choice == "0":
            print("👋 Até mais!")
            break
        
        query = input("🔍 Termo de busca: ").strip()
        if not query:
            query = "happy person"
        
        if choice == "1":
            tester.compare_all(query, download_samples=True)
        
        elif choice == "2":
            results = tester.search_tenor(query, limit=10)
            print(f"\n📊 Tenor - {len(results)} resultados:")
            for i, r in enumerate(results):
                print(f"  {i+1}. {r['title']} | GIF: {r['gif_size']}")
        
        elif choice == "3":
            results = tester.search_giphy(query, limit=10)
            print(f"\n📊 Giphy - {len(results)} resultados:")
            for i, r in enumerate(results):
                print(f"  {i+1}. {r['title']} | {r['original_size']}")
        
        elif choice == "4":
            results = tester.search_pixabay(query, limit=10, orientation="vertical")
            print(f"\n📊 Pixabay - {len(results)} resultados:")
            for i, r in enumerate(results):
                print(f"  {i+1}. {r['title']} | {r['full_size']}")
        
        elif choice == "5":
            results = tester.search_pexels(query, limit=10, orientation="portrait")
            print(f"\n📊 Pexels - {len(results)} resultados:")
            for i, r in enumerate(results):
                print(f"  {i+1}. {r['title']} | {r['original_size']}")
        
        elif choice == "6":
            results = tester.search_unsplash(query, limit=10, orientation="portrait")
            print(f"\n📊 Unsplash - {len(results)} resultados:")
            for i, r in enumerate(results):
                print(f"  {i+1}. {r['title']} | {r['size']}")


if __name__ == "__main__":
    main()
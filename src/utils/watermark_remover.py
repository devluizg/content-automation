"""
Removedor de Marca D'água
Remove ou esconde marcas d'água de imagens geradas por IA
"""
from PIL import Image, ImageDraw, ImageFilter
import cv2
import numpy as np
from pathlib import Path


class WatermarkRemover:
    """Remove marcas d'água de imagens"""
    
    def __init__(self):
        # Configurações padrão para marca d'água no canto inferior esquerdo
        # Ajuste conforme necessário
        self.watermark_height = 80  # Altura da área com marca d'água
        self.watermark_width = 200  # Largura da área com marca d'água
    
    def remove_by_crop(self, 
                       image_path: str, 
                       output_path: str = None,
                       crop_bottom: int = 80,
                       crop_left: int = 0) -> str:
        """
        Remove marca d'água cortando a parte inferior/esquerda da imagem
        
        Args:
            image_path: Caminho da imagem original
            output_path: Caminho de saída (se None, sobrescreve)
            crop_bottom: Pixels a cortar da parte inferior
            crop_left: Pixels a cortar da esquerda
            
        Returns:
            Caminho da imagem processada
        """
        img = Image.open(image_path)
        width, height = img.size
        
        # Corta a imagem (left, top, right, bottom)
        cropped = img.crop((
            crop_left,           # esquerda
            0,                   # topo
            width,               # direita
            height - crop_bottom # fundo
        ))
        
        # Redimensiona de volta ao tamanho original
        cropped = cropped.resize((width, height), Image.Resampling.LANCZOS)
        
        output_path = output_path or image_path
        cropped.save(output_path)
        
        return output_path
    
    def remove_by_gradient(self,
                           image_path: str,
                           output_path: str = None,
                           gradient_height: int = 150,
                           gradient_opacity: float = 0.9) -> str:
        """
        Adiciona gradiente escuro na parte inferior (esconde marca d'água)
        Efeito profissional estilo cinema/Netflix
        
        Args:
            image_path: Caminho da imagem original
            output_path: Caminho de saída
            gradient_height: Altura do gradiente
            gradient_opacity: Opacidade máxima do gradiente (0-1)
        """
        img = Image.open(image_path).convert('RGBA')
        width, height = img.size
        
        # Cria gradiente
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)
        
        # Desenha gradiente de baixo para cima
        for y in range(gradient_height):
            # Calcula opacidade (mais escuro embaixo)
            progress = y / gradient_height
            opacity = int(255 * gradient_opacity * (1 - progress))
            
            draw.line(
                [(0, height - y - 1), (width, height - y - 1)],
                fill=(0, 0, 0, opacity)
            )
        
        # Combina imagem com gradiente
        result = Image.alpha_composite(img, gradient)
        
        # Converte de volta para RGB
        result = result.convert('RGB')
        
        output_path = output_path or image_path
        result.save(output_path)
        
        return output_path
    
    def remove_by_blur(self,
                       image_path: str,
                       output_path: str = None,
                       blur_area: tuple = None,
                       blur_radius: int = 30) -> str:
        """
        Desfoca a área da marca d'água
        
        Args:
            image_path: Caminho da imagem
            blur_area: Tupla (x, y, largura, altura) da área a desfocar
                      Se None, usa canto inferior esquerdo
        """
        img = Image.open(image_path)
        width, height = img.size
        
        # Área padrão: canto inferior esquerdo
        if blur_area is None:
            blur_area = (0, height - self.watermark_height, 
                        self.watermark_width, self.watermark_height)
        
        x, y, w, h = blur_area
        
        # Recorta a área da marca d'água
        watermark_region = img.crop((x, y, x + w, y + h))
        
        # Aplica blur forte
        blurred = watermark_region.filter(
            ImageFilter.GaussianBlur(radius=blur_radius)
        )
        
        # Cola de volta na imagem
        img.paste(blurred, (x, y))
        
        output_path = output_path or image_path
        img.save(output_path)
        
        return output_path
    
    def remove_by_inpaint(self,
                          image_path: str,
                          output_path: str = None,
                          inpaint_area: tuple = None) -> str:
        """
        Usa inpainting do OpenCV para remover marca d'água
        (tenta reconstruir a imagem na área)
        
        Args:
            image_path: Caminho da imagem
            inpaint_area: Tupla (x, y, largura, altura)
        """
        # Lê imagem com OpenCV
        img = cv2.imread(image_path)
        height, width = img.shape[:2]
        
        # Área padrão: canto inferior esquerdo
        if inpaint_area is None:
            x, y = 0, height - self.watermark_height
            w, h = self.watermark_width, self.watermark_height
        else:
            x, y, w, h = inpaint_area
        
        # Cria máscara (branco = área a reconstruir)
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[y:y+h, x:x+w] = 255
        
        # Aplica inpainting
        result = cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
        
        output_path = output_path or image_path
        cv2.imwrite(output_path, result)
        
        return output_path
    
    def remove_by_logo(self,
                       image_path: str,
                       logo_path: str,
                       output_path: str = None,
                       position: str = "bottom_left",
                       logo_size: tuple = None,
                       margin: int = 20) -> str:
        """
        Coloca seu logo por cima da marca d'água
        
        Args:
            image_path: Caminho da imagem
            logo_path: Caminho do seu logo (PNG com transparência)
            position: "bottom_left", "bottom_right", "bottom_center"
            logo_size: Tupla (largura, altura) para redimensionar logo
            margin: Margem das bordas
        """
        img = Image.open(image_path).convert('RGBA')
        logo = Image.open(logo_path).convert('RGBA')
        
        width, height = img.size
        
        # Redimensiona logo se especificado
        if logo_size:
            logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
        
        logo_w, logo_h = logo.size
        
        # Calcula posição
        if position == "bottom_left":
            pos = (margin, height - logo_h - margin)
        elif position == "bottom_right":
            pos = (width - logo_w - margin, height - logo_h - margin)
        elif position == "bottom_center":
            pos = ((width - logo_w) // 2, height - logo_h - margin)
        else:
            pos = (margin, height - logo_h - margin)
        
        # Cola logo na imagem
        img.paste(logo, pos, logo)
        
        # Converte para RGB
        result = img.convert('RGB')
        
        output_path = output_path or image_path
        result.save(output_path)
        
        return output_path
    
    def remove_by_solid_bar(self,
                            image_path: str,
                            output_path: str = None,
                            bar_height: int = 100,
                            bar_color: tuple = (0, 0, 0),
                            add_text: str = None) -> str:
        """
        Adiciona barra sólida na parte inferior
        Pode incluir texto (seu @ ou canal)
        
        Args:
            image_path: Caminho da imagem
            bar_height: Altura da barra
            bar_color: Cor RGB da barra
            add_text: Texto para adicionar na barra (opcional)
        """
        from PIL import ImageFont
        
        img = Image.open(image_path).convert('RGB')
        width, height = img.size
        
        draw = ImageDraw.Draw(img)
        
        # Desenha barra
        draw.rectangle(
            [(0, height - bar_height), (width, height)],
            fill=bar_color
        )
        
        # Adiciona texto se fornecido
        if add_text:
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                    32
                )
            except:
                font = ImageFont.load_default()
            
            # Centraliza texto
            text_bbox = draw.textbbox((0, 0), add_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (width - text_width) // 2
            text_y = height - bar_height + (bar_height - 32) // 2
            
            draw.text((text_x, text_y), add_text, fill="white", font=font)
        
        output_path = output_path or image_path
        img.save(output_path)
        
        return output_path
    
    def process_batch(self,
                      image_paths: list,
                      method: str = "gradient",
                      **kwargs) -> list:
        """
        Processa múltiplas imagens
        
        Args:
            image_paths: Lista de caminhos de imagens
            method: "crop", "gradient", "blur", "inpaint", "bar"
            **kwargs: Argumentos adicionais para o método
            
        Returns:
            Lista de caminhos processados
        """
        methods = {
            "crop": self.remove_by_crop,
            "gradient": self.remove_by_gradient,
            "blur": self.remove_by_blur,
            "inpaint": self.remove_by_inpaint,
            "bar": self.remove_by_solid_bar
        }
        
        if method not in methods:
            raise ValueError(f"Método '{method}' não existe. Use: {list(methods.keys())}")
        
        func = methods[method]
        processed = []
        
        for img_path in image_paths:
            try:
                result = func(img_path, **kwargs)
                processed.append(result)
                print(f"✅ Processado: {img_path}")
            except Exception as e:
                print(f"❌ Erro em {img_path}: {e}")
                processed.append(img_path)  # Mantém original se falhar
        
        return processed


# ============================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================

def remove_watermark(image_path: str, method: str = "gradient") -> str:
    """
    Função simples para remover marca d'água
    
    Uso:
        remove_watermark("imagem.png")
        remove_watermark("imagem.png", method="crop")
    """
    remover = WatermarkRemover()
    
    if method == "crop":
        return remover.remove_by_crop(image_path)
    elif method == "gradient":
        return remover.remove_by_gradient(image_path)
    elif method == "blur":
        return remover.remove_by_blur(image_path)
    elif method == "inpaint":
        return remover.remove_by_inpaint(image_path)
    elif method == "bar":
        return remover.remove_by_solid_bar(image_path)
    else:
        return remover.remove_by_gradient(image_path)


# ============================================
# TESTE
# ============================================

if __name__ == "__main__":
    import sys
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║          REMOVEDOR DE MARCA D'ÁGUA                        ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Métodos disponíveis:                                     ║
║  1. crop     - Corta a parte inferior                     ║
║  2. gradient - Gradiente escuro (recomendado)             ║
║  3. blur     - Desfoca a marca d'água                     ║
║  4. inpaint  - IA reconstrói a área                       ║
║  5. bar      - Barra sólida com texto                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Teste se imagem existe
    test_image = "output/images/teste.png"
    
    if not Path(test_image).exists():
        print(f"⚠️ Imagem de teste não encontrada: {test_image}")
        print("Execute primeiro o teste de geração de imagem.")
        sys.exit(1)
    
    remover = WatermarkRemover()
    
    # Cria cópias para testar cada método
    from shutil import copy
    
    methods = ["crop", "gradient", "blur", "inpaint", "bar"]
    
    for method in methods:
        output = f"output/images/teste_{method}.png"
        copy(test_image, output)
        
        print(f"\n🔄 Testando método: {method}")
        
        if method == "bar":
            remover.remove_by_solid_bar(output, add_text="@seucanal")
        else:
            remove_watermark(output, method=method)
        
        print(f"✅ Salvo: {output}")
    
    print("\n✅ Todos os métodos testados!")
    print("📁 Verifique as imagens em: output/images/")

"""
Sistema de logging simples
"""
from datetime import datetime
from pathlib import Path


class Logger:
    """Logger simples com cores no terminal"""
    
    COLORS = {
        "info": "\033[94m",     # Azul
        "success": "\033[92m",  # Verde
        "warning": "\033[93m",  # Amarelo
        "error": "\033[91m",    # Vermelho
        "reset": "\033[0m"      # Reset
    }
    
    def __init__(self, name: str = "ContentBot", save_to_file: bool = True):
        self.name = name
        self.save_to_file = save_to_file
        self.log_file = Path("output/logs") / f"{datetime.now().strftime('%Y%m%d')}.log"
        
        if save_to_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.COLORS.get(level, "")
        reset = self.COLORS["reset"]
        
        formatted = f"[{timestamp}] [{self.name}] {message}"
        
        # Print colorido
        print(f"{color}{formatted}{reset}")
        
        # Salva em arquivo
        if self.save_to_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{level.upper()}] {formatted}\n")
    
    def info(self, message: str):
        self._log("info", f"ℹ️ {message}")
    
    def success(self, message: str):
        self._log("success", f"✅ {message}")
    
    def warning(self, message: str):
        self._log("warning", f"⚠️ {message}")
    
    def error(self, message: str):
        self._log("error", f"❌ {message}")
    
    def step(self, step_num: int, total: int, message: str):
        self._log("info", f"[{step_num}/{total}] {message}")

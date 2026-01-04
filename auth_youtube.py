"""
Autenticação YouTube - Executa uma vez
"""

import pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS = 'config/client_secrets.json'
CREDENTIALS_FILE = 'config/youtube_credentials.pickle'

def authenticate():
    print("🔐 Autenticando com YouTube...")
    print("   (vai abrir o navegador)\n")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS, 
        SCOPES
    )
    
    # Usa porta 8888 ao invés de 8080
    credentials = flow.run_local_server(port=8888)
    
    # Salva credenciais
    Path(CREDENTIALS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, 'wb') as f:
        pickle.dump(credentials, f)
    
    print(f"\n✅ Autenticado com sucesso!")
    print(f"   Credenciais salvas em: {CREDENTIALS_FILE}")

if __name__ == "__main__":
    authenticate()
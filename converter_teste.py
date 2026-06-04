import os
import time
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from yt_dlp import YoutubeDL

# Configurações de ambiente para evitar problemas de compilação na nuvem
os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ["NUMBA_CACHE_DIR"] = "/tmp/numba_cache"

app = FastAPI()

# Definição dos diretórios corretos usando caminhos absolutos
OUTPUT_DIR = "/tmp/downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mapeia o caminho absoluto exato do arquivo de cookies criado pelo Secret Files
CAMINHO_COOKIES = os.path.join(os.path.dirname(__file__), "cookies.txt")

def detectar_tom_musical(caminho_audio):
    """
    Analisa o arquivo de áudio utilizando o Cromagrama STFT do Librosa 
    e perfis de correlação para estimar o tom da música.
    """
    try:
        import librosa
        import numpy as np

        # Aguarda o arquivo estabilizar em disco se o download for muito rápido
        for _ in range(5):
            if os.path.exists(caminho_audio) and os.path.getsize(caminho_audio) > 0:
                break
            time.sleep(1)
            
        if not os.path.exists(caminho_audio):
            return "Tom indisponível (Processamento lento)"

        # Otimizado: sr=11025 reduz drasticamente o uso de memória RAM no Render (evita estouro de 512MB)
        y, sr = librosa.load(caminho_audio, sr=11025, mono=True)
        
        # Otimizado: chroma_stft é leve e não exige compilação paralela travada no Linux
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_medio = np.mean(chroma, axis=1)
        
        notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Perfis de Krumhansl-Kessler para correlação de tons estáveis
        perfil_maior = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        perfil_menor = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        melhor_correlacao = -1
        tom_detectado = "Não identif

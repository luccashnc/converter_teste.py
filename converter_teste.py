import os
import time
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from yt_dlp import YoutubeDL

# Configurações de ambiente para evitar problemas de compilação na nuvem
os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ["NUMBA_CACHE_DIR"] = "/tmp/numba_cache"

app = FastAPI()

# Definição do diretório temporário correto
OUTPUT_DIR = "/tmp/downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        tom_detectado = "Não identificado"
        
        for i in range(12):
            p_maior_rotacionado = np.roll(perfil_maior, i)
            p_menor_rotacionado = np.roll(perfil_menor, i)
            
            corr_maior = np.corrcoef(chroma_medio, p_maior_rotacionado)[0, 1]
            corr_menor = np.corrcoef(chroma_medio, p_menor_rotacionado)[0, 1]
            
            if corr_maior > melhor_correlacao:
                melhor_correlacao = corr_maior
                tom_detectado = f"{notas[i]} Maior"
                
            if corr_menor > melhor_correlacao:
                melhor_correlacao = corr_menor
                tom_detectado = f"{notas[i]} Menor"
                
        return tom_detectado
    except Exception as e:
        return f"Tom indisponível (Erro na análise)"


@app.get("/", response_class=HTMLResponse)
def pagina_inicial():
    return """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Conversor & Key Detector</title>
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 30px; background-color: #f4f4f9;">
            <h2>Conversor Privado com Detetor de Tom</h2>
            <form action="/converter" method="post" style="margin-top: 20px;">
                <input type="text" name="url" placeholder="Cole a URL do YouTube aqui" style="width: 90%; max-width: 500px; padding: 12px; border-radius: 5px; border: 1px solid #ccc;"><br><br>
                <button type="submit" style="padding: 12px 24px; background-color: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">Analisar e Converter</button>
            </form>
        </body>
    </html>
    """


@app.post("/converter", response_class=HTMLResponse)
def converter_video(url: str = Form(...)):
    id_arquivo = "audio_analisado"
    caminho_mp3 = os.path.join(OUTPUT_DIR, f"{id_arquivo}.mp3")
    
    # Limpa downloads anteriores para economizar espaço em disco no container
    if os.path.exists(caminho_mp3):
        try:
            os.remove(caminho_mp3)
        except:
            pass

    # Configuração do yt-dlp atualizada com suporte ao arquivo de cookies
    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': 'cookies.txt',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(OUTPUT_DIR, f"{id_arquivo}.%(ext)s"),
        'restrictfilenames': True,
        'keepvideo': False,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:

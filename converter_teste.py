import os
import time
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from yt_dlp import YoutubeDL

# Configurações de ambiente para nuvem
os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ["NUMBA_CACHE_DIR"] = "/tmp/numba_cache"

app = FastAPI()

OUTPUT_DIR = "/tmp/downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mapeia o caminho absoluto do arquivo criado pelo Secret Files do Render
CAMINHO_COOKIES = os.path.join(os.path.dirname(__file__), "cookies.txt")

def detectar_tom_musical(caminho_audio):
    try:
        import librosa
        import numpy as np

        for _ in range(5):
            if os.path.exists(caminho_audio) and os.path.getsize(caminho_audio) > 0:
                break
            time.sleep(1)
            
        if not os.path.exists(caminho_audio):
            return "Tom indisponivel (Processamento lento)"

        y, sr = librosa.load(caminho_audio, sr=11025, mono=True)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_medio = np.mean(chroma, axis=1)
        
        notas = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        perfil_maior = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        perfil_menor = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        melhor_correlacao = -1
        tom_detectado = "Nao identificado"
        
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
        return f"Tom indisponivel (Erro: {str(e)[:30]})"


@app.get("/", response_class=HTMLResponse)
def pagina_inicial():
    return """
    <html>
        <head>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <title>Conversor & Key Detector</title>
        </head>
        <body style='font-family: Arial, sans-serif; text-align: center; padding: 30px; background-color: #f4f4f9;'>
            <h2>Conversor Privado com Detetor de Tom</h2>
            <form action='/converter' method='post' style='margin-top: 20px;'>
                <input type='text' name='url' placeholder='Cole a URL do YouTube aqui' style='width: 90%; max-width: 500px; padding: 12px; border-radius: 5px; border: 1px solid #ccc;'><br><br>
                <button type='submit' style='padding: 12px 24px; background-color: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;'>Analisar e Converter</button>
            </form>
        </body>
    </html>
    """


@app.post("/converter", response_class=HTMLResponse)
def converter_video(url: str = Form(...)):
    id_arquivo = "audio_analisado"
    caminho_audio = os.path.join(OUTPUT_DIR, f"{id_arquivo}.m4a")
    
    if os.path.exists(caminho_audio):
        try:
            os.remove(caminho_audio)
        except Exception:
            pass

    # PLANO B INFALÍVEL: Emulação estrita do cliente de áudio (YouTube Music)
    ydl_opts = {
        'format': 'ba[ext=m4a]/bestaudio/best',
        'cookiefile': CAMINHO_COOKIES,
        'outtmpl': os.path.join(OUTPUT_DIR, f"{id_arquivo}.%(ext)s"),
        'restrictfilenames': True,
        'keepvideo': False,
        'remote_components': 'ejs:github',
        
        # Ignora páginas pesadas de vídeo e foca apenas nos endpoints de música
        'youtube_include_dash_manifest': False,
        'youtube_include_hls_manifest': False,
        
        'extractor_args': {
            'youtube': {
                # Força o yt-dlp a se identificar estritamente como o app do YouTube Music (YTM)
                'player_client': ['youtube_music'],
                'skip': ['webpage', 'hls', 'dash'],
            }
        }
    }
    
    try

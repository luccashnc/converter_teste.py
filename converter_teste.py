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

    ydl_opts = {
        'format': 'bestaudio/best',
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
            ydl.download([url])
    except Exception as e:
        return f"""
        <body style="font-family: Arial; text-align: center; padding: 40px;">
            <h3>Erro ao baixar do YouTube</h3>
            <p style="color: red;">{str(e)}</p>
            <a href="/">Voltar</a>
        </body>
        """
    
    # Executa a análise de tom no arquivo baixado
    tom_da_musica = detectar_tom_musical(caminho_mp3)
    
    return f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resultado da Análise</title>
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 40px; background-color: #f4f4f9;">
            <div style="background: white; padding: 30px; border-radius: 10px; display: inline-block; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); max-width: 90%;">
                <h3>Música Processada!</h3>
                <p style="font-size: 18px; margin: 20px 0;">Tom Estimado: <strong style="color: #e63946; font-size: 26px;">{tom_da_musica}</strong></p>
                <br>
                <a href="/download?arquivo={id_arquivo}.mp3" style="display: inline-block; padding: 12px 24px; background-color: #2a9d8f; color: white; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">Baixar Arquivo MP3</a>
                <br><br>
                <a href="/" style="color: #666; text-decoration: none; font-size: 14px;">← Converter outra</a>
            </div>
        </body>
    </html>
    """


@app.get("/download")
def baixar_arquivo(arquivo: str):
    caminho_completo = os.path.join(OUTPUT_DIR, arquivo)
    if os.path.exists(caminho_completo):
        return FileResponse(caminho_completo, media_type="audio/mpeg", filename="musica_convertida.mp3")
    return HTMLResponse("<h3>Arquivo expirado ou não encontrado. Volte e converta novamente.</h3>", status_code=404)

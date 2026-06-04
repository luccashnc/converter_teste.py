@app.post("/converter", response_class=HTMLResponse)
def converter_video(url: str = Form(...)):
    id_arquivo = "audio_analisado"
    caminho_mp3 = os.path.join(OUTPUT_DIR, f"{id_arquivo}.mp3")
    
    if os.path.exists(caminho_mp3):
        try:
            os.remove(caminho_mp3)
        except Exception:
            pass

    # Configuração robusta: remove a trava rígida de formato e força compatibilidade
    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': CAMINHO_COOKIES,
        'outtmpl': os.path.join(OUTPUT_DIR, f"{id_arquivo}.%(ext)s"),
        'restrictfilenames': True,
        'keepvideo': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'prefer_ffmpeg': True,  # Força o uso do FFmpeg se disponível
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Garante a extensão correta para o Librosa caso o FFmpeg converta ou use fallback
        caminho_baixado = os.path.join(OUTPUT_DIR, f"{id_arquivo}.mp3")
        if not os.path.exists(caminho_baixado):
            # Fallback caso o sistema salve com outra extensão devido ao ambiente Linux
            for ext in ['webm', 'm4a', 'wav']:
                teste_caminho = os.path.join(OUTPUT_DIR, f"{id_arquivo}.{ext}")
                if os.path.exists(teste_caminho):
                    os.rename(teste_caminho, caminho_mp3)
                    break
                    
    except Exception as e:
        return f"<html><body><h3>Erro no download</h3><p style='color:red;'>{str(e)}</p><a href='/'>Voltar</a></body></html>"
    
    # Executa a análise de tom no arquivo final
    tom_da_musica = detectar_tom_musical(caminho_mp3)
    
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 40px; background-color: #f4f4f9;">
            <div style="background: white; padding: 30px; border-radius: 10px; display: inline-block; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                <h3>Música Processada!</h3>
                <p style="font-size: 18px;">Tom Estimado: <strong style="color: #e63946; font-size: 24px;">{tom_da_musica}</strong></p>
                <br>
                <a href="/download?arquivo={id_arquivo}.mp3" style="display: inline-block; padding: 12px 24px; background-color: #2a9d8f; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Baixar Arquivo MP3</a>
                <br><br>
                <a href="/" style="color: #666; text-decoration: none;">← Converter outra</a>
            </div>
        </body>
    </html>
    """

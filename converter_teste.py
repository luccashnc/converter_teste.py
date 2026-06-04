ydl_opts = {
        'format': 'bestaudio/best',
        'cookiefile': 'cookies.txt',  # <--- ADICIONE ESTA LINHA AQUI
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(OUTPUT_DIR, f"{id_arquivo}.%(ext)s"),
        'restrictfilenames': True,
        'keepvideo': False,
    }

import os
import time
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from yt_dlp import YoutubeDL

# Configurações de ambiente para evitar problemas de compilação na nuvem
os.environ["NUMBA_DISABLE_JIT"] = "1"

app = FastAPI()

# Definição do diretório temporário correto
OUTPUT_DIR = "/tmp/downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

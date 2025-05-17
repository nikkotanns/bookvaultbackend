from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os

app = FastAPI()

HTML_FILE_PATH = os.path.join(os.path.dirname(__file__), "index.html")
FILE_PATH = os.path.join(os.path.dirname(__file__), "BookVault.exe")

@app.get("/", response_class=HTMLResponse)
async def main_page():
    with open(HTML_FILE_PATH, encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/download")
async def download_file():
    return FileResponse(
        path=FILE_PATH,
        filename="BookVault.exe",
        media_type='application/octet-stream'
    )

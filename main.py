from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import yt_dlp
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Serve the frontend HTML at the root
@app.get("/")
async def root():
    try:
        with open("index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Download endpoint
@app.post("/download")
async def download_video(url: str = Form(...)):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Temporary file path (Vercel allows /tmp)
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',  # Smaller format for Vercel
            'socket_timeout': 30,  # Timeout after 30 seconds
            'retries': 2,  # Retry twice on failure
        }

        try:
            logger.info(f"Starting download for URL: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filepath = os.path.join(tmpdir, filename)

                if not os.path.exists(filepath):
                    logger.error("Downloaded file not found")
                    raise HTTPException(status_code=500, detail="Download failed: File not found")

                # Get the actual filename after download
                actual_filename = os.path.basename(filepath)
                logger.info(f"Download successful, serving file: {actual_filename}")

                return FileResponse(
                    filepath,
                    media_type='application/octet-stream',
                    headers={"Content-Disposition": f"attachment; filename={actual_filename}"}
                )
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error downloading video: {str(e)}")

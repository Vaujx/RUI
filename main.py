from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
import yt_dlp
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Download endpoint (no root endpoint now, as frontend is static)
@app.post("/download")
async def download_video(url: str = Form(...)):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Path to bundled FFmpeg binary
    ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg')

    # Ensure FFmpeg is executable (redundant if set in git, but safe)
    try:
        os.chmod(ffmpeg_path, 0o755)
    except Exception as e:
        logger.warning(f"Could not chmod FFmpeg: {str(e)}")

    # Temporary file path
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',  # Requires FFmpeg for merge
            'ffmpeg_location': ffmpeg_path,  # Use bundled FFmpeg
            'socket_timeout': 30,
            'retries': 2,
        }

        try:
            logger.info(f"Starting download for URL: {url} with FFmpeg at {ffmpeg_path}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filepath = os.path.join(tmpdir, filename)

                if not os.path.exists(filepath):
                    logger.error("Downloaded file not found")
                    raise HTTPException(status_code=500, detail="Download failed: File not found")

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

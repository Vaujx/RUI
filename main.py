from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import yt_dlp
import os
import tempfile

app = FastAPI()

# Serve the frontend HTML at the root
@app.get("/")
async def root():
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

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
            'format': 'best',  # Best quality
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filepath = os.path.join(tmpdir, filename)

                if not os.path.exists(filepath):
                    raise HTTPException(status_code=500, detail="Download failed")

                # Get the actual filename after download (yt-dlp may adjust it)
                actual_filename = os.path.basename(filepath)

                return FileResponse(
                    filepath,
                    media_type='application/octet-stream',
                    headers={"Content-Disposition": f"attachment; filename={actual_filename}"}
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error downloading video: {str(e)}")
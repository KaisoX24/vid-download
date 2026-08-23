import time
from pathlib import Path
import yt_dlp


def progress_hook(d, progress_callback=None, status_callback=None, state=None):
    "Handles yt-dlp progress updates safely, throttled to avoid UI spam."
    now = time.time()

    if state and now - state["last_update"] < 0.2:
        return

    if state:
        state["last_update"] = now

    if d["status"] == "downloading":
        downloaded = d.get("downloaded_bytes", 0)
        total = d.get("total_bytes") or d.get("total_bytes_estimate")

        if total:
            percent = min(downloaded / total, 1.0)
            if progress_callback:
                progress_callback(percent)
            percent_text = f"{percent * 100:.1f}%"
        else:
            percent_text = "Calculating..."

        speed = d.get("speed") or 0
        eta = d.get("eta")

        if status_callback:
            status_callback(
                f"{percent_text} | "
                f"{downloaded / 1e6:.1f} MB | "
                f"{speed / 1e6:.1f} MB/s | "
                f"ETA: {eta if eta else 'N/A'}"
            )


def download_video(
    url,
    selected_res="Best",
    audio_quality="192k",
    file_type="mp4",
    output_path="downloads",
    progress_callback=None,
    status_callback=None,
):
    "Downloads a single URL as mp4 or mp3 via yt-dlp"
    
    Path(output_path).mkdir(parents=True, exist_ok=True)

    format_map = {
        "Best": "bestvideo+bestaudio/best",
        "480P": "bestvideo[height<=480]+bestaudio/best",
        "720P": "bestvideo[height<=720]+bestaudio/best",
        "1080P": "bestvideo[height<=1080]+bestaudio/best",
    }

    audio_map = {
        "128k": "128",
        "192k": "192",
        "256k": "256",
        "320k": "320",
    }

    ydl_opts = {
        "outtmpl": f"{output_path}/%(title).200s_%(id)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "quiet": True,
    }

    if file_type == "mp4":
        ydl_opts.update(
            {
                "format": format_map[selected_res],
                "merge_output_format": "mp4",
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",  
                    }
                ],
                
                "postprocessor_args": {
                    "videoconvertor": ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"],
                },
            }
        )

    elif file_type == "mp3":
        ydl_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": audio_map.get(audio_quality, "192"),
                    }
                ],
            }
        )

    state = {"last_update": 0}
    ydl_opts["progress_hooks"] = [
        lambda d: progress_hook(
            d,
            progress_callback=progress_callback,
            status_callback=status_callback,
            state=state,
        )
    ]

    if status_callback:
        status_callback("Starting download...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if progress_callback:
        progress_callback(1.0)
    if status_callback:
        status_callback("Download complete!")
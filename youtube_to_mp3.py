from pathlib import Path
import shutil
import sys

def ensure_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found. Please install it first:")
        if sys.platform == "darwin":
            print("  macOS: brew install ffmpeg")
        elif sys.platform.startswith("win"):
            print("  Windows: choco install ffmpeg  (or download from ffmpeg.org)")
        else:
            print("  Linux (Debian/Ubuntu): sudo apt-get install ffmpeg")
        sys.exit(1)

def main():
    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        print("Missing dependency: yt-dlp. Install with: pip install yt-dlp")
        sys.exit(1)

    url = input("Paste the YouTube link and press Enter: ").strip()
    if not url:
        print("No link provided. Exiting.")
        return

    ensure_ffmpeg()

    downloads_dir = Path.home() / "Downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        # Save into Downloads with the video title as filename
        "outtmpl": str(downloads_dir / "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": False,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }],
    }

    print("Downloading and converting to MP3...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extract info (and download) to determine final path
            info = ydl.extract_info(url, download=True)
            # Prepare the expected output filename and swap extension to .mp3
            final_path = Path(ydl.prepare_filename(info)).with_suffix(".mp3")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if final_path.exists():
        print(f"Done! Saved to:\n  {final_path}")
    else:
        print(f"Done. Check your Downloads folder:\n  {downloads_dir}")

if __name__ == "__main__":
    main()
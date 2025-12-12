"""
YouTube → MP3 → Whisper → Transcript pipeline.

Features:
- Downloads YouTube audio as MP3
- Splits long audio into chunks to bypass Whisper API size limits
- Transcribes each chunk using OpenAI Whisper API
- Saves:
    - MP3 to downloads/
    - audio chunks to audio_chunks/
    - transcript to transcripts/
- Normalizes messy YouTube input strings automatically
"""

import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import os
import sys
import re
from pydub import AudioSegment
from openai import OpenAI
import re
import string

# ------------------------------------------------------------
# Environment / client setup
# ------------------------------------------------------------

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not set in environment.")

client = OpenAI()

# ------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------

def run(cmd: list[str]) -> None:
    """
    Run a subprocess command and raise if it fails.
    """
    subprocess.run(cmd, check=True)

def normalize_youtube_input(s: str) -> str:
    """
    Normalize user-provided YouTube input into a valid URL.

    Handles:
    - Full URLs (even badly escaped)
    - watch?v=VIDEO_ID&t=...
    - Escaped strings (\\, \\?, \\=, \\v)
    - Raw video IDs

    Returns:
        A valid https://www.youtube.com/watch?v=... URL
    """
    # Strip whitespace
    s = s.strip()

    # Remove all ASCII control characters (incl. \v, \t, etc.)
    s = "".join(c for c in s if c in string.printable)

    # Remove leftover backslashes
    s = s.replace("\\", "")

    # Extract video ID if present anywhere
    match = re.search(r"v=([A-Za-z0-9_-]{11})", s)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"

    # Raw video ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return f"https://www.youtube.com/watch?v={s}"

    # watch?v=...
    if s.startswith("watch?v="):
        return f"https://www.youtube.com/{s}"

    return s


# ------------------------------------------------------------
# Download step
# ------------------------------------------------------------

def download_audio(url: str, out_dir: Path) -> Path:
    """
    Download best available YouTube audio and convert to MP3.

    Args:
        url: Normalized YouTube URL
        out_dir: Directory to store MP3

    Returns:
        Path to downloaded MP3 file
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(out_dir / "%(title)s.%(ext)s")

    run([
        sys.executable,
        "-m", "yt_dlp",
        "-f", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--force-overwrites",
        "-o", out_tmpl,
        url,
    ])

    mp3s = sorted(out_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp3s:
        raise RuntimeError("No MP3 produced.")

    return mp3s[0]


# ------------------------------------------------------------
# Transcription step
# ------------------------------------------------------------

import shutil

def transcribe(mp3_path: Path, chunks_dir: Path) -> str:
    """
    Split MP3 into chunks and transcribe each using Whisper API.

    Temporary audio chunks are deleted after transcription.

    Args:
        mp3_path: Path to full MP3 file
        chunks_dir: Temporary directory for audio chunks

    Returns:
        Full transcript text
    """
    chunks_dir.mkdir(parents=True, exist_ok=True)

    audio = AudioSegment.from_file(mp3_path)
    chunk_length_ms = 5 * 60 * 1000  # 5 minutes
    full_text: list[str] = []

    try:
        for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
            chunk = audio[start:start + chunk_length_ms]
            chunk_path = chunks_dir / f"chunk_{i:03d}.mp3"
            chunk.export(chunk_path, format="mp3")

            with open(chunk_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    file=f,
                    model="whisper-1",
                )

            full_text.append(result.text.strip())

    finally:
        # Always clean up chunk directory
        shutil.rmtree(chunks_dir, ignore_errors=True)

    return "\n".join(full_text)


# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------

def main() -> None:
    """
    CLI entry point.
    """
    ap = argparse.ArgumentParser(description="Transcribe YouTube videos using Whisper.")
    ap.add_argument("url", help="YouTube URL, watch?v=..., or video ID")
    ap.add_argument("--out-dir", default="downloads", help="MP3 output directory")
    args = ap.parse_args()

    downloads_dir = Path(args.out_dir)
    transcripts_dir = Path("transcripts")
    chunks_dir = Path("audio_chunks")

    transcripts_dir.mkdir(exist_ok=True)

    url = normalize_youtube_input(args.url)
    mp3_path = download_audio(url, downloads_dir)

    text = transcribe(mp3_path, chunks_dir)

    transcript_path = transcripts_dir / f"{mp3_path.stem}.txt"
    transcript_path.write_text(text, encoding="utf-8")

    print(f"Transcript saved to: {transcript_path}")


if __name__ == "__main__":
    main()
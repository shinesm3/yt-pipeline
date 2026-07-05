"""
Renders a finished .mp4 from a text script:
  1. Generates TTS voiceover (edge-tts, free, no API key needed)
  2. Builds a simple captioned video (solid background + centered text,
     synced roughly to audio duration) using FFmpeg
  3. Outputs a ready-to-upload .mp4

Requires:
  pip install edge-tts --break-system-packages
  FFmpeg installed on the system (apt install ffmpeg / brew install ffmpeg)

Usage:
  python render_video.py --script "Your script text here" --output out.mp4 --title_card "Password Security"
"""

import argparse
import asyncio
import subprocess
import textwrap
import os

import edge_tts

VOICE = "en-US-GuyNeural"  # change to any edge-tts voice you prefer
WIDTH, HEIGHT = 1080, 1920  # vertical format for Shorts


async def generate_tts(text, out_path):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(out_path)


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def build_video(audio_path, script_text, title_card, out_path):
    duration = get_audio_duration(audio_path)

    # Split script into chunks so captions change every ~4 seconds
    words = script_text.split()
    chunk_size = max(1, len(words) // max(1, int(duration / 4)))
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    chunk_duration = duration / len(chunks)

    # Build a drawtext filter chain: one caption chunk visible at a time
    filters = []
    for i, chunk in enumerate(chunks):
        wrapped = textwrap.fill(chunk, width=28).replace("'", "\u2019").replace(":", "\\:")
        start = i * chunk_duration
        end = start + chunk_duration
        filters.append(
            f"drawtext=text='{wrapped}':fontcolor=white:fontsize=64:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.5:boxborderw=20:"
            f"enable='between(t,{start:.2f},{end:.2f})'"
        )

    # Title card at the very start
    title_wrapped = title_card.replace("'", "\u2019").replace(":", "\\:")
    filters.insert(0,
        f"drawtext=text='{title_wrapped}':fontcolor=yellow:fontsize=72:"
        f"x=(w-text_w)/2:y=100:box=1:boxcolor=black@0.6:boxborderw=20:"
        f"enable='between(t,0,2)'"
    )

    filter_chain = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x1a1a2e:s={WIDTH}x{HEIGHT}:d={duration}",
        "-i", audio_path,
        "-vf", filter_chain,
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest",
        out_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Video rendered: {out_path}")


def render(script_text, title_card, output_path, tmp_audio="tts_audio.mp3"):
    asyncio.run(generate_tts(script_text, tmp_audio))
    build_video(tmp_audio, script_text, title_card, output_path)
    os.remove(tmp_audio)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True)
    parser.add_argument("--title_card", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    render(args.script, args.title_card, args.output)

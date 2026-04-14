from models import YouTubeReader
from config import Config
from secret_manager import SecretManager
from typing import Optional
from datetime import datetime
from pathlib import Path
import asyncio
import sys


async def read_video(url: str, output_file: Optional[str] = None) -> str:
    config = Config()
    secret_mgr = SecretManager(config.project_id)
    yt = YouTubeReader(config=config, secret_mgr=secret_mgr)
    prompt = yt.get_default_prompt()

    gemini_response = await yt.analyze_video(url, prompt)
    if not gemini_response.candidates:
        raise ValueError("no response from Gemini API's")

    content = gemini_response.candidates[0].content.parts[0].text

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"youtube_analysis_{timestamp}.md"

    # ensure the output path exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # write the content to a file
    output_path.write_text(content, encoding="utf-8")

    print(f"youtube summary written to: {output_path.absolute()}")

    return content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: uv run ytreader.py <youtube_url> [output_file]")
        sys.exit(1)
    video_url = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = asyncio.run(read_video(video_url, output_filename))
        print("\nAnalysis preview:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

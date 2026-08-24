from urllib.parse import urlparse
from pathlib import Path

def is_valid_url_structure(url_string:str) ->bool:
    "Checks if the url is Valid"
    try:
        result = urlparse(url_string.strip())
        return all([result.scheme in ['http', 'https'], result.netloc])
    except (AttributeError, ValueError):
        return False

def collect_urls(count:int) -> list[str]:
    """Ask the user for `count` valid URLs and return them as a list."""
    urls = []
    for i in range(count):
        url = input(f"Enter URL #{i + 1}: ").strip()
        while not is_valid_url_structure(url):
            print("Invalid URL, please try again.")
            url = input(f"Enter URL #{i + 1}: ").strip()
        urls.append(url)
    return urls

def ask_resolution() -> str:
    "Prompts the user for the video resolution"
    options = {1: 'best', 2: '480p', 3: '720p', 4: '1080p'}
    while True:
        try:
            opt = int(input("Resolution:\n1. Best\n2. 480P\n3. 720P\n4. 1080P\nOption (1-4): "))
            if opt in options:
                return options[opt]
            print("Please select a valid option.")
        except ValueError:
            print("Please enter a number.")

def ask_bitrate() -> str:
    "Prompts the user for the audio Bitrate"
    options = {1: '128k', 2: '192k', 3: '256k', 4: '320k'}
    while True:
        try:
            opt = int(input("Bitrate:\n1. 128k\n2. 192k\n3. 256k\n4. 320k\nOption (1-4): "))
            if opt in options:
                return options[opt]
            print("Please select a valid option.")
        except ValueError:
            print("Please enter a number.")

def ask_format() ->str:
    "Prompts the user for the Media Format"
    options = {1: 'mp4', 2: 'mp3'}
    while True:
        try:
            opt = int(input("Download as:\n1. MP4\n2. MP3\nOption (1/2): "))
            if opt in options:
                return options[opt]
            print("Please select a valid option.")
        except ValueError:
            print("Please enter a number.")

def ask_output_path(default:str="downloads") -> Path:
    "Makes the directory for the users save location"
    raw = input(f"Save to [{default}]: ").strip()
    path = Path(raw) if raw else Path(default)
    path.mkdir(parents=True, exist_ok=True)
    return path

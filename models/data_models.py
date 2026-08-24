from dataclasses import dataclass
from pathlib import Path
from errors.errors import FetchError

@dataclass
class url_info:
    url:str
    file_type:str
    selected_res:str
    audio_quality:str
    output_path:Path

@dataclass
class task_completion:
    url:str
    success:bool
    error_type:FetchError|None
    message:str|None
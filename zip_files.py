import zipfile
from pathlib import Path

def zip_downloaded_files(dest_path,temp_folder_path, zip_name="download.zip"):
    zip_path = Path(dest_path)/zip_name
    temp_folder_path=Path(temp_folder_path)
    temp_folder_contents=[f for f in Path(temp_folder_path).iterdir() if f.is_file()]
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in temp_folder_contents:
            if file.suffix.endswith(".zip"):
                continue
            zipf.write(file, arcname=file.name)
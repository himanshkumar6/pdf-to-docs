import tempfile
import aiofiles
import os
from pathlib import Path
from fastapi import UploadFile

async def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    """Saves an UploadFile to a temporary location securely."""
    try:
        suffix = Path(upload_file.filename or ".pdf").suffix
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        
        async with aiofiles.open(path, 'wb') as out_file:
            while content := await upload_file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)
        return Path(path)
    finally:
        await upload_file.seek(0)
        
def cleanup_files(*filepaths):
    """Deletes temporary files and directories securely."""
    for filepath in filepaths:
        if not filepath:
            continue
            
        path = str(filepath)
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                print(f"Error cleaning up {path}: {e}")

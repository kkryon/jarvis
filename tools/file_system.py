import os
from pathlib import Path
import json

class FileSystemAgent:
    def read_file(self, path):
        try:
            return Path(path).read_text(encoding="utf-8")
        except Exception as e:
            return f"[Error: {e}]"

    def write_file(self, path, content):
        try:
            Path(path).write_text(content, encoding="utf-8")
            return f"[File written successfully: {path}]"
        except Exception as e:
            return f"[Error: {e}]"

    def list_dir(self, path="."):
        try:
            return "\n".join(f.name for f in Path(path).iterdir())
        except Exception as e:
            return f"[Error: {e}]"
from pathlib import Path

def check_if_file_is_empty(path: Path):
    try:
        with open(path, "r") as f:
            data = f.read()

        if len(data) > 0:
            return False

    except FileNotFoundError:
        return True
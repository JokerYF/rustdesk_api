from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

LOG_PATH = BASE_DIR / 'logs'
LOG_PATH.mkdir(exist_ok=True)

DATA_PATH = BASE_DIR / 'data'

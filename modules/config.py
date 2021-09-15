import os
from pathlib import Path
import yaml

__all__ = (
    'config'
)

BASE_DIR = Path(__file__).resolve().parent.parent

with open(os.path.join(BASE_DIR, 'config.yml')) as f:
    config = yaml.safe_load(f)

config: dict

OWNERS_IDS = config.get('owners_ids', [])
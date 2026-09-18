from pathlib import Path

import gpu
import organism_v6


source = Path(__file__).resolve().parents[1] / 'source'
gpu.__path__.insert(0, str(source / 'gpu'))
organism_v6.__path__.insert(0, str(source / 'organism_v6'))

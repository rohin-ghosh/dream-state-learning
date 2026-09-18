import importlib.util
from pathlib import Path


directory = Path(__file__).resolve().parent
previous = directory.parent / 'observation_20260917_generation1/save_receipt.py'
spec = importlib.util.spec_from_file_location('receipt', previous)
receipt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receipt)
receipt.DIRECTORY = directory
receipt.AUTHORITY = directory.parent / 'MAIN_INITIAL3_SOURCE_COPY_AUTHORITY_20260917.json'
receipt.save()

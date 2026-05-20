import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
REPOS_DIR = DATA_DIR / "repos"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
CHUNKS_DIR = DATA_DIR / "chunks"

for directory in (REPOS_DIR, VECTOR_DB_DIR, CHUNKS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME = "repository_chunks"
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-5.4-nano")

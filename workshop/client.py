"""One connection helper, shared by the participant runner and the organizer tools."""

import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient


def connect(write=False):
    load_dotenv(".env")
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_API_KEY") if write else (
        os.getenv("QDRANT_READONLY_API_KEY") or os.getenv("QDRANT_API_KEY")
    )
    if not url or not key:
        sys.exit("Set QDRANT_URL and a Qdrant API key in .env")
    return QdrantClient(url=url, api_key=key, timeout=120, cloud_inference=True)


def collection():
    load_dotenv(".env")
    return os.getenv("QDRANT_COLLECTION", "legal_lab_v1")

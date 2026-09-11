"""Start the local app using environment loaded by uv --env-file."""

import os
import uvicorn
from .provider import status


def main():
    info = status()
    print(f"Answer mode: {info['mode']}; model available: {info['available']}")
    uvicorn.run("workshop.app:app", host=os.getenv("APP_HOST", "127.0.0.1"),
                port=int(os.getenv("APP_PORT", "8000")))


if __name__ == "__main__":
    main()

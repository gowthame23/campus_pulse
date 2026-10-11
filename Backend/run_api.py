import os

import uvicorn


def load_env(path=".env"):
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()


if __name__ == "__main__":
    load_env()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "True").lower() == "true"

    print(f"Starting Campus Pulse API on {host}:{port} (reload={reload})...")
    uvicorn.run("api.main:app", host=host, port=port, reload=reload)

"""
Alias for generator_server.py - for platforms expecting app.py
"""
from generator_server import app

if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

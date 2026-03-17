"""Launcher: run app from app.main so PyInstaller and python main.py still work."""
from app.main import main

if __name__ == "__main__":
    main()

"""
Build KIEC ENGINEERING & CONSULTING as a Windows .exe with the KIEC logo as the application icon.

Icon/shortcut: uses app/assets/image/KIEC - 27062025.jpg to create Logo.ico (exe and shortcut icon).

1. Run checks (optional):  python scripts/check_before_build.py
2. Build:                 python scripts/build_exe.py

Requirements: pip install pyinstaller pillow
"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS = PROJECT_ROOT / "app" / "assets"
IMAGE_ASSETS = ASSETS / "image"
ICON_ASSETS = ASSETS / "icon"
# Logo source: KIEC image (build outputs Logo.ico for the .exe)
LOGO_SRC = IMAGE_ASSETS / "KIEC - 27062025.jpg"
LOGO_ICO = ICON_ASSETS / "Logo.ico"


def make_ico():
    """Convert the logo image (KIEC) to Logo.ico for use as the .exe icon. No-op if source missing."""
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed; skipping Logo.ico. Run: pip install pillow (optional).")
        return
    if not LOGO_SRC.exists():
        print(f"Logo source not found: {LOGO_SRC}. Building .exe without custom icon.")
        return
    img = Image.open(LOGO_SRC)
    # Use RGBA if the image has transparency; otherwise convert to RGBA for ico
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    # Windows .ico can contain multiple sizes; use common sizes
    sizes = [(256, 256), (48, 48), (32, 32), (16, 16)]
    img.save(LOGO_ICO, format="ICO", sizes=sizes)
    print(f"Created {LOGO_ICO}")


def build_exe():
    """Run PyInstaller with the project spec."""
    try:
        import PyInstaller.__main__
    except ImportError:
        print("PyInstaller is required. Run: pip install pyinstaller")
        sys.exit(1)
    if not LOGO_ICO.exists():
        try:
            make_ico()
        except Exception as e:
            print(f"Logo.ico not created ({e}). Building .exe without custom icon.")
    spec = PROJECT_ROOT / "scripts" / "app_architect.spec"
    if not spec.exists():
        print(f"Spec file not found: {spec}")
        sys.exit(1)
    os.chdir(PROJECT_ROOT)
    PyInstaller.__main__.run([
        str(spec),
        "--noconfirm",
        "--clean",
    ])
    print("\nDone. Onedir output: dist\\KIEC Engineering Consulting\\KIEC Engineering Consulting.exe")


if __name__ == "__main__":
    # Create Logo.ico from app/assets/image/KIEC - 27062025.jpg first (for exe/shortcut icon)
    try:
        make_ico()
    except Exception as e:
        print(f"Logo.ico: {e}")
    build_exe()

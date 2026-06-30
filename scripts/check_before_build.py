"""
Run this before building the .exe to verify everything is ready.
Uses app/assets/image/KIEC - 27062025.jpg for the exe/shortcut icon (Logo.ico).
Exit code 0 = all checks passed; non-zero = fix issues then run again.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ASSETS = PROJECT_ROOT / "app" / "assets"
IMAGE_ASSETS = ASSETS / "image"
ICON_ASSETS = ASSETS / "icon"
LOGO_SRC = IMAGE_ASSETS / "KIEC - 27062025.jpg"
LOGO_ICO = ICON_ASSETS / "Logo.ico"
SPEC_FILE = PROJECT_ROOT / "scripts" / "app_architect.spec"
MAIN_SCRIPT = PROJECT_ROOT / "app" / "main.py"


def check(condition: bool, message: str) -> bool:
    if condition:
        print(f"  OK: {message}")
        return True
    print(f"  FAIL: {message}")
    return False


def main() -> int:
    print("KIEC ENGINEERING & CONSULTING — Pre-build checks\n")
    all_ok = True

    # 1) Logo image for exe/shortcut icon
    if not check(LOGO_SRC.is_file(), f"Logo source exists: {LOGO_SRC.name}"):
        print(f"      Put your KIEC image at: {LOGO_SRC}")
        all_ok = False
    else:
        print(f"      (Used to create Logo.ico for .exe and shortcut icon)")

    # 2) Pillow to create Logo.ico
    try:
        from PIL import Image  # noqa: F401
        check(True, "Pillow installed (for Logo.ico)")
    except ImportError:
        check(False, "Pillow installed — run: pip install pillow")
        all_ok = False

    # 3) Create Logo.ico from JPG so exe gets the icon
    if LOGO_SRC.is_file():
        try:
            from PIL import Image
            img = Image.open(LOGO_SRC)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            sizes = [(256, 256), (48, 48), (32, 32), (16, 16)]
            img.save(LOGO_ICO, format="ICO", sizes=sizes)
            check(LOGO_ICO.is_file(), f"Logo.ico created from {LOGO_SRC.name}")
        except Exception as e:
            check(False, f"Logo.ico creation: {e}")
            all_ok = False

    # 4) Spec and main script
    if not check(SPEC_FILE.is_file(), f"Spec file exists: {SPEC_FILE.name}"):
        all_ok = False
    if not check(MAIN_SCRIPT.is_file(), f"Entry script exists: {MAIN_SCRIPT.relative_to(PROJECT_ROOT)}"):
        all_ok = False

    # 5) PyInstaller
    try:
        import PyInstaller.__main__  # noqa: F401
        check(True, "PyInstaller installed")
    except ImportError:
        check(False, "PyInstaller installed — run: pip install pyinstaller")
        all_ok = False

    # 6) Quick import check (app package loads)
    try:
        import app.main  # noqa: F401
        check(True, "App package imports (app.main)")
    except Exception as e:
        check(False, f"App import: {e}")
        all_ok = False

    # 7) Assets used at runtime (optional; app may still run without some)
    for name in ["KIEC_logo.png", "road.jpg"]:
        p = IMAGE_ASSETS / name
        if p.is_file():
            print(f"  OK: Runtime asset: {name}")
        else:
            print(f"  Note: Optional asset missing: {name}")

    print()
    if all_ok:
        print("All checks passed. Run:  python scripts/build_exe.py")
        return 0
    print("Fix the issues above, then run:  python scripts/check_before_build.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())

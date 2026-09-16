"""Construye el .exe de un solo archivo.

Requisitos (solo en la maquina donde compilas, no en la del colegio):
    pip install pyinstaller

Uso:
    python build_exe.py

Resultado:
    dist/GeoGuessr-Santander-Offline.exe   <- este archivo es todo lo que llevas
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NOMBRE = "GeoGuessr-Santander-Offline"
DB = os.path.join(HERE, "tiles.db")


def hacer_icono():
    """Convierte assets/logo.png en un .ico si Pillow esta disponible."""
    ico = os.path.join(HERE, "app", "assets", "logo.ico")
    if os.path.exists(ico):
        return ico
    try:
        from PIL import Image
    except ImportError:
        return None
    png = os.path.join(HERE, "app", "assets", "logo.png")
    if not os.path.exists(png):
        return None
    img = Image.open(png).convert("RGBA")
    img.save(ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return ico


def main():
    if not os.path.exists(DB):
        sys.exit("Falta tiles.db. Ejecuta primero:  python download_tiles.py")

    mb = os.path.getsize(DB) / 1e6
    print(f"tiles.db = {mb:.1f} MB  -> el .exe pesara aproximadamente eso mas ~15 MB")

    sep = ";" if os.name == "nt" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", NOMBRE,
        "--add-data", f"{os.path.join(HERE, 'app')}{sep}app",
        "--add-data", f"{DB}{sep}.",
        "--noconfirm",
        "--clean",
        os.path.join(HERE, "server.py"),
    ]
    ico = hacer_icono()
    if ico:
        cmd[-1:-1] = ["--icon", ico]

    print("\n" + " ".join(cmd) + "\n")
    subprocess.check_call(cmd, cwd=HERE)

    exe = os.path.join(HERE, "dist", NOMBRE + (".exe" if os.name == "nt" else ""))
    print("\nListo:", exe, f"({os.path.getsize(exe) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

"""Construye el paquete que se lleva al colegio.

Requisitos (solo en la maquina donde compilas, no en la del colegio):
    pip install pyinstaller

Uso:
    python build_exe.py

Resultado:
    dist/GeoGuessr-Santander-Offline/            <- carpeta con el .exe adentro
    dist/GeoGuessr-Santander-Offline.zip         <- eso mismo, listo para copiar

Se usa el modo CARPETA (--onedir) a proposito, no el de archivo unico. El .exe
de archivo unico se auto-descomprime en memoria al arrancar, que es exactamente
lo que hacen los empaquetadores de malware, y los antivirus lo bloquean por
heuristica aunque este limpio. El modo carpeta no hace eso y pasa sin problema.
"""
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
NOMBRE = "GeoGuessr-Santander-Offline"
DB = os.path.join(HERE, "tiles.db")
DIST = os.path.join(HERE, "dist")

LEEME = """GeoGuessr Santander - version offline
=====================================

COMO SE JUEGA
  Doble clic en:  GeoGuessr-Santander-Offline.exe

Se abre una ventana negra y enseguida el navegador con el juego.
NO CERRAR la ventana negra mientras se juega; al terminar, se cierra y listo.

No necesita internet, ni instalar nada.

IMPORTANTE
  Hay que copiar la carpeta COMPLETA. El .exe solo no funciona: al lado van
  los mapas y las librerias que necesita.

Si Windows avisa "aplicacion desconocida" (pantalla azul de SmartScreen), es
porque el programa no esta firmado digitalmente, no porque tenga algo malo:
  Mas informacion -> Ejecutar de todas formas

Mapas: satelite (c) Esri. Calles y nombres (c) colaboradores de OpenStreetMap.
"""


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
        sys.exit("Falta tiles.db. Ejecuta primero:\n"
                 "  python download_tiles.py\n"
                 "  python download_vector.py")

    sep = ";" if os.name == "nt" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
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

    print(" ".join(cmd) + "\n")
    subprocess.check_call(cmd, cwd=HERE)

    carpeta = os.path.join(DIST, NOMBRE)
    with open(os.path.join(carpeta, "LEEME.txt"), "w", encoding="utf-8") as fh:
        fh.write(LEEME)

    zip_path = carpeta + ".zip"
    print("\nComprimiendo...")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for raiz, _, archivos in os.walk(carpeta):
            for a in archivos:
                completo = os.path.join(raiz, a)
                zf.write(completo, os.path.relpath(completo, DIST))

    total = sum(
        os.path.getsize(os.path.join(r, a))
        for r, _, ar in os.walk(carpeta) for a in ar
    )
    print(f"\nCarpeta: {carpeta}  ({total/1e6:.1f} MB)")
    print(f"Zip:     {zip_path}  ({os.path.getsize(zip_path)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()

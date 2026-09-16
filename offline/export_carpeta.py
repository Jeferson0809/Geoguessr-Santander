"""Exporta el juego como una carpeta normal, sin ningun ejecutable.

Es la alternativa al .exe para maquinas donde el antivirus lo bloquea: aqui no
hay nada que ejecutar, solo archivos. Se abre index.html con doble clic y el
juego corre en el navegador, sin servidor y sin internet.

    python export_carpeta.py

Resultado:
    dist/GeoGuessr-Santander-Offline-carpeta/   <- esta carpeta es lo que llevas
    dist/GeoGuessr-Santander-Offline-carpeta.zip
"""
import os
import shutil
import sqlite3
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "tiles.db")
SALIDA = os.path.join(HERE, "dist", "GeoGuessr-Santander-Offline-carpeta")

LEEME = """GeoGuessr Santander - version offline
=====================================

COMO SE JUEGA
  Doble clic en:  index.html

Se abre en el navegador y ya. No hay que instalar nada, no necesita internet
y no hay ningun programa que ejecutar (por eso ningun antivirus lo bloquea).

Si el doble clic abre un editor de texto en vez del navegador:
  clic derecho sobre index.html -> Abrir con -> Chrome / Edge / Firefox

IMPORTANTE
  Hay que copiar la carpeta COMPLETA. Si copias solo index.html no funciona:
  los mapas estan en la subcarpeta tiles/.

Mapas: Tiles (c) Esri.
"""


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit("Falta tiles.db. Ejecuta primero:  python download_tiles.py")

    if os.path.exists(SALIDA):
        shutil.rmtree(SALIDA)
    os.makedirs(SALIDA)

    # 1. el juego
    shutil.copytree(os.path.join(HERE, "app"), SALIDA, dirs_exist_ok=True)

    # 2. los tiles, como archivos sueltos (el navegador los pide por file://)
    con = sqlite3.connect(DB_PATH)
    n = 0
    for layer, z, x, y, data in con.execute("SELECT layer, z, x, y, data FROM tiles"):
        carpeta = os.path.join(SALIDA, "tiles", layer, str(z), str(x))
        os.makedirs(carpeta, exist_ok=True)
        # la extension es siempre .jpg porque asi la pide game.js; el navegador
        # reconoce la imagen por su contenido, no por el nombre.
        with open(os.path.join(carpeta, f"{y}.jpg"), "wb") as fh:
            fh.write(data)
        n += 1
        if n % 500 == 0:
            print(f"\r  {n} tiles...", end="", flush=True)
    con.close()
    print(f"\r  {n} tiles escritos.      ")

    with open(os.path.join(SALIDA, "LEEME.txt"), "w", encoding="utf-8") as fh:
        fh.write(LEEME)

    # 3. un zip, que es mas comodo de pasar por USB o WhatsApp que 5000 archivos
    zip_path = SALIDA + ".zip"
    print("Comprimiendo...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for raiz, _, archivos in os.walk(SALIDA):
            for a in archivos:
                completo = os.path.join(raiz, a)
                rel = os.path.relpath(completo, os.path.dirname(SALIDA))
                zf.write(completo, rel)

    mb_dir = sum(
        os.path.getsize(os.path.join(r, a))
        for r, _, ar in os.walk(SALIDA) for a in ar
    ) / 1e6
    print(f"\nCarpeta: {SALIDA}  ({mb_dir:.1f} MB, {n} tiles)")
    print(f"Zip:     {zip_path}  ({os.path.getsize(zip_path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

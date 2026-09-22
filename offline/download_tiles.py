"""Descarga la foto satelital de cada ubicacion y la guarda en tiles.db.

Es la capa de la FASE DE PISTAS. El mapa de la fase de adivinar no se baja
aqui: son tiles vectoriales de OpenStreetMap y los trae download_vector.py.

Se ejecuta UNA sola vez, con internet. El juego no vuelve a salir a la red.

    python download_tiles.py

Solo se baja el area minima para jugar y con pocas conexiones en paralelo,
para no abusar de los servidores de Esri.
"""
import json
import math
import os
import sqlite3
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "tiles.db")

UA = "Geoguessr-Santander-Offline/1.0 (uso educativo; descarga unica de area local)"

SAT_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

# --- que descargar -----------------------------------------------------------
SAT_ZOOMS = [16, 17, 18, 19]   # las 4 pistas del juego (Esri no tiene z20 aqui)
SAT_RADIUS_X = 3               # tiles a cada lado del centro
SAT_RADIUS_Y = 2

THREADS = 4


def deg2tile(lat, lon, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    return x, y


def open_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute(
        "CREATE TABLE IF NOT EXISTS tiles ("
        " layer TEXT, z INTEGER, x INTEGER, y INTEGER, data BLOB,"
        " PRIMARY KEY (layer, z, x, y))"
    )
    return con


def plan():
    """Devuelve la lista de (layer, z, x, y) a descargar."""
    # locations.js es "const LOCATIONS_DATA = {...};" -> se saca el JSON del medio
    with open(os.path.join(HERE, "app", "locations.js"), encoding="utf-8") as fh:
        crudo = fh.read()
    crudo = crudo.split("=", 1)[1].rsplit(";", 1)[0]
    locations = json.loads(crudo)["locations"]

    wanted = set()

    for loc in locations:
        for z in SAT_ZOOMS:
            cx, cy = deg2tile(loc["lat"], loc["lon"], z)
            for dx in range(-SAT_RADIUS_X, SAT_RADIUS_X + 1):
                for dy in range(-SAT_RADIUS_Y, SAT_RADIUS_Y + 1):
                    wanted.add(("sat", z, cx + dx, cy + dy))

    return sorted(wanted)


def fetch(job):
    layer, z, x, y = job
    url = SAT_URL.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return job, resp.read()
        except Exception as exc:                      # noqa: BLE001
            if intento == 2:
                return job, None
            time.sleep(1.5 * (intento + 1))
    return job, None


def verificar(con):
    """Avisa si un servidor devolvio tiles de relleno ('sin imagen', 'access blocked').

    Esos tiles llegan con codigo 200 y pasarian por buenos: se detectan porque
    el mismo contenido exacto se repite muchas veces dentro de un mismo zoom.
    """
    import hashlib
    from collections import defaultdict

    problemas = []
    grupos = defaultdict(lambda: defaultdict(int))
    for layer, z, data in con.execute("SELECT layer, z, data FROM tiles"):
        grupos[(layer, z)][hashlib.md5(data).hexdigest()] += 1

    for (layer, z), hashes in sorted(grupos.items()):
        total = sum(hashes.values())
        repetido = max(hashes.values())
        if total >= 20 and repetido > total * 0.5:
            problemas.append(f"  {layer} z{z}: {repetido}/{total} tiles identicos")

    if problemas:
        print("\nAVISO: parece que el servidor devolvio imagenes de relleno en:")
        print("\n".join(problemas))
        print("Revisa esos zooms: puede que no haya cobertura, o que te hayan bloqueado.")
    else:
        print("Verificacion: todos los zooms traen imagenes reales.")


def main():
    con = open_db()
    have = {tuple(r) for r in con.execute("SELECT layer, z, x, y FROM tiles")}
    jobs = [j for j in plan() if j not in have]

    total = len(jobs)
    print(f"Tiles ya guardados: {len(have)}")
    print(f"Tiles por descargar: {total}")
    if not total:
        print("Nada que hacer.")
        verificar(con)
        return

    ok = fail = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        buf = []
        for job, data in pool.map(fetch, jobs):
            if data:
                buf.append((job[0], job[1], job[2], job[3], data))
                ok += 1
            else:
                fail += 1
            if len(buf) >= 200:
                con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
                con.commit()
                buf.clear()
            done = ok + fail
            if done % 100 == 0 or done == total:
                pct = done * 100 // total
                vel = done / max(time.time() - t0, 0.1)
                sys.stdout.write(f"\r  {done}/{total} ({pct}%)  {vel:.0f} tiles/s  fallidos={fail}   ")
                sys.stdout.flush()
        if buf:
            con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
            con.commit()

    print()
    verificar(con)
    con.execute("VACUUM")
    con.close()
    mb = os.path.getsize(DB_PATH) / 1e6
    print(f"Listo: {ok} tiles nuevos, {fail} fallidos. tiles.db = {mb:.1f} MB")


if __name__ == "__main__":
    main()

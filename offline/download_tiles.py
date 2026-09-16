"""Descarga los tiles necesarios y los empaqueta en un SQLite (tiles.db).

Se ejecuta UNA sola vez, con internet, antes de construir el .exe.
El juego offline lee este archivo; no vuelve a salir a la red nunca.

    python download_tiles.py

Nota: se descarga solo el area minima para jugar (unos pocos miles de tiles)
y con pocas conexiones en paralelo, para no abusar de los servidores de Esri.
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
# Capa de calles. NO se usa tile.openstreetmap.org (el del Streamlit): su politica
# prohibe la descarga masiva y responde "Access blocked" con codigo 200, asi que el
# tile malo se cuela como bueno. De las alternativas sin API key, World_Topo_Map es
# la que mejor se lee: trae nombres de carrera y calle desde el zoom 14.
STREET_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"

# --- que descargar -----------------------------------------------------------
SAT_ZOOMS = [16, 17, 18, 19]   # las 4 pistas del juego (Esri no tiene z20 aqui)
SAT_RADIUS_X = 3               # tiles a cada lado del centro
SAT_RADIUS_Y = 2

# Area metropolitana (fase de adivinar)
METRO_BBOX = (7.020, -73.230, 7.200, -73.040)   # (lat_min, lon_min, lat_max, lon_max)
METRO_ZOOMS = [11, 12, 13, 14, 15, 16]

# Nucleo urbano con un zoom extra de detalle
CORE_BBOX = (7.060, -73.160, 7.160, -73.090)
CORE_ZOOMS = [17]

MARGEN = 2                     # tiles extra alrededor de cada bbox

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

    for bbox, zooms in ((METRO_BBOX, METRO_ZOOMS), (CORE_BBOX, CORE_ZOOMS)):
        lat_min, lon_min, lat_max, lon_max = bbox
        for z in zooms:
            x0, y0 = deg2tile(lat_max, lon_min, z)
            x1, y1 = deg2tile(lat_min, lon_max, z)
            # MARGEN: un par de tiles extra alrededor, si no a zoom bajo quedan
            # franjas negras a los lados en pantallas anchas.
            for x in range(min(x0, x1) - MARGEN, max(x0, x1) + MARGEN + 1):
                for y in range(min(y0, y1) - MARGEN, max(y0, y1) + MARGEN + 1):
                    wanted.add(("street", z, x, y))

    return sorted(wanted)


def fetch(job):
    layer, z, x, y = job
    url = (SAT_URL if layer == "sat" else STREET_URL).format(z=z, x=x, y=y)
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

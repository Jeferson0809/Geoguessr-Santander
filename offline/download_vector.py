"""Descarga tiles VECTORIALES de OpenStreetMap para el area metropolitana.

Por que vectorial y no imagenes: los tiles ya dibujados de OSM no se pueden
bajar en bloque (su politica lo prohibe) y las alternativas de imagenes (Esri)
no rotulan colegios, parques ni barrios. Con tiles vectoriales guardamos los
DATOS -- calles, manzanas, parques, nombres -- y el navegador los dibuja en el
momento con MapLibre, igual que hace la version online.

La fuente es el planet de Protomaps, que se sirve como un unico archivo PMTiles
con soporte de rangos HTTP: en vez de bajar los 138 GB, pedimos solo los pedazos
del area que nos interesa. Protomaps existe justamente para este uso offline.

    python download_vector.py

Los tiles quedan en tiles.db (capa "vt"), junto a los de satelite.
"""
import gzip
import io
import math
import os
import sqlite3
import sys
import time
import urllib.request

from pmtiles.tile import deserialize_header, deserialize_directory, find_tile, zxy_to_tileid

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "tiles.db")

UA = "Geoguessr-Santander-Offline/1.0 (extracto local para uso educativo offline)"

# Misma area que METRO_BBOX en download_tiles.py
BBOX = (7.020, -73.230, 7.200, -73.040)   # lat_min, lon_min, lat_max, lon_max

# Protomaps corta el basemap en zoom 15; de ahi para arriba MapLibre reescala
# los mismos datos, y como son vectores el texto sigue saliendo nitido.
ZOOM_MAX = 15


def url_build(fecha=None):
    """El planet se publica a diario. Busca el build mas reciente que exista."""
    import datetime
    hoy = datetime.date.today()
    for i in range(0, 14):
        d = (hoy - datetime.timedelta(days=i)).strftime("%Y%m%d")
        u = f"https://build.protomaps.com/{d}.pmtiles"
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Range": "bytes=0-6"})
            if urllib.request.urlopen(req, timeout=45).read() == b"PMTiles":
                return u
        except Exception:
            continue
    raise SystemExit("No encontre ningun build de Protomaps disponible.")


def fuente_http(url):
    """get_bytes(offset, length) por rangos HTTP, con cache.

    El cache importa: para llegar a un tile hay que leer el directorio raiz y
    uno o dos directorios hoja, y esos se repiten en cada consulta.
    """
    cache = {}
    stats = {"peticiones": 0, "bytes": 0}

    def get_bytes(offset, length):
        clave = (offset, length)
        if clave in cache:
            return cache[clave]
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Range": f"bytes={offset}-{offset + length - 1}"}
        )
        for intento in range(4):
            try:
                datos = urllib.request.urlopen(req, timeout=90).read()
                break
            except Exception:
                if intento == 3:
                    raise
                time.sleep(2 * (intento + 1))
        stats["peticiones"] += 1
        stats["bytes"] += len(datos)
        if length < 4_000_000:          # no cachear lecturas de tiles grandes
            cache[clave] = datos
        return datos

    return get_bytes, stats


def leer_tile(get_bytes, header, z, x, y):
    """Reader.get de pmtiles, pero reusando el header ya leido."""
    tile_id = zxy_to_tileid(z, x, y)
    dir_offset = header["root_offset"]
    dir_length = header["root_length"]
    for _ in range(4):
        entradas = deserialize_directory(get_bytes(dir_offset, dir_length))
        r = find_tile(entradas, tile_id)
        if not r:
            return None
        if r.run_length == 0:
            dir_offset = header["leaf_directory_offset"] + r.offset
            dir_length = r.length
        else:
            return get_bytes(header["tile_data_offset"] + r.offset, r.length)
    return None


def deg2tile(lat, lon, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return x, y


def main():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute(
        "CREATE TABLE IF NOT EXISTS tiles ("
        " layer TEXT, z INTEGER, x INTEGER, y INTEGER, data BLOB,"
        " PRIMARY KEY (layer, z, x, y))"
    )

    url = url_build()
    print("Fuente:", url)
    get_bytes, stats = fuente_http(url)
    header = deserialize_header(get_bytes(0, 127))
    zmax = min(ZOOM_MAX, header["max_zoom"])
    print(f"  zoom maximo del archivo: {header['max_zoom']}, usaremos hasta {zmax}")

    lat_min, lon_min, lat_max, lon_max = BBOX
    trabajos = []
    for z in range(0, zmax + 1):
        x0, y0 = deg2tile(lat_max, lon_min, z)
        x1, y1 = deg2tile(lat_min, lon_max, z)
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                trabajos.append((z, x, y))

    ya = {(z, x, y) for z, x, y in con.execute("SELECT z,x,y FROM tiles WHERE layer='vt'")}
    trabajos = [t for t in trabajos if t not in ya]
    print(f"Tiles vectoriales por descargar: {len(trabajos)}  (ya guardados: {len(ya)})")
    if not trabajos:
        print("Nada que hacer.")
        return

    guardados = vacios = 0
    t0 = time.time()
    buf = []
    for i, (z, x, y) in enumerate(trabajos, 1):
        datos = leer_tile(get_bytes, header, z, x, y)
        if datos:
            buf.append(("vt", z, x, y, datos))
            guardados += 1
        else:
            vacios += 1                 # mar, o zona sin datos: normal
        if len(buf) >= 50:
            con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
            con.commit()
            buf.clear()
        if i % 20 == 0 or i == len(trabajos):
            mb = stats["bytes"] / 1e6
            sys.stdout.write(
                f"\r  {i}/{len(trabajos)}  guardados={guardados} vacios={vacios}  "
                f"bajados={mb:.1f} MB  {time.time()-t0:.0f}s   "
            )
            sys.stdout.flush()
    if buf:
        con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
        con.commit()

    print()
    tam = con.execute(
        "SELECT COUNT(*), SUM(LENGTH(data)) FROM tiles WHERE layer='vt'"
    ).fetchone()
    con.execute("VACUUM")
    con.close()
    print(f"Listo: {tam[0]} tiles vectoriales, {tam[1]/1e6:.1f} MB de datos.")
    print(f"tiles.db = {os.path.getsize(DB_PATH)/1e6:.1f} MB")


if __name__ == "__main__":
    main()

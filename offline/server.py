"""Servidor local del GeoGuessr offline.

Sirve la carpeta app/ y los tiles guardados en tiles.db, y abre el navegador.
No hace ni una sola peticion a internet.

Funciona igual ejecutado como script (python server.py) que empaquetado con
PyInstaller dentro del .exe de un solo archivo.
"""
import http.server
import os
import socket
import socketserver
import sqlite3
import sys
import threading
import webbrowser

APP_NAME = "GeoGuessr Santander - offline"


def base_dir():
    """Carpeta donde viven app/ y tiles.db (dentro del .exe o al lado del .py)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


BASE = base_dir()
APP_DIR = os.path.join(BASE, "app")
DB_PATH = os.path.join(BASE, "tiles.db")

_db = sqlite3.connect(DB_PATH, check_same_thread=False)
_db_lock = threading.Lock()


def get_tile(layer, z, x, y):
    with _db_lock:
        row = _db.execute(
            "SELECT data FROM tiles WHERE layer=? AND z=? AND x=? AND y=?",
            (layer, z, x, y),
        ).fetchone()
    return row[0] if row else None


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def do_GET(self):
        partes = self.path.lstrip("/").split("?")[0].split("/")
        if len(partes) == 5 and partes[0] == "tiles":
            self.serve_tile(partes[1:])
            return
        super().do_GET()

    def serve_tile(self, partes):
        layer, z, x, y = partes
        try:
            data = get_tile(layer, int(z), int(x), int(y))
        except ValueError:
            data = None
        if data is None:
            self.send_error(404, "tile fuera del area descargada")
            return
        ctype = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "max-age=86400")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass  # silencio: la consola solo muestra el mensaje de bienvenida


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    if not os.path.exists(DB_PATH):
        print("ERROR: no encuentro tiles.db (los mapas offline).")
        print("Ejecuta primero:  python download_tiles.py")
        input("\nEnter para cerrar...")
        return

    n = _db.execute("SELECT COUNT(*) FROM tiles").fetchone()[0]
    port = puerto_libre()
    url = f"http://127.0.0.1:{port}/index.html"

    print("=" * 58)
    print(f"  {APP_NAME}")
    print("=" * 58)
    print(f"  Mapas cargados: {n} tiles  (todo local, sin internet)")
    print(f"  Abriendo: {url}")
    print()
    print("  >> NO CIERRES ESTA VENTANA mientras juegas. <<")
    print("  Para terminar, cierra esta ventana o presiona Ctrl+C.")
    print("=" * 58)

    with Server(("127.0.0.1", port), Handler) as httpd:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nHasta luego.")


if __name__ == "__main__":
    main()

# GeoGuessr Santander — versión offline

Misma dinámica que la app de Streamlit (`demo.py`), pero en **un solo `.exe`** que
funciona sin internet: lo copias a un USB, lo abres en el portátil del colegio y ya.

No necesita Python, ni Streamlit, ni conexión. Los mapas van dentro del ejecutable.

---

## Para el que solo quiere jugar

1. Copiar `GeoGuessr-Santander-Offline.exe` al computador.
2. Doble clic.
3. Se abre una ventana negra (el servidor local) y enseguida el navegador con el juego.
4. **No cerrar la ventana negra** mientras juegas. Al terminar, se cierra y listo.

> Windows Defender / SmartScreen puede avisar "aplicación desconocida" la primera vez
> (pasa con cualquier .exe sin firma digital). Se acepta con *Más información → Ejecutar de todas formas*.

---

## Para reconstruirlo (con internet, una sola vez)

```
cd offline
python download_tiles.py      # descarga los mapas -> tiles.db  (~10 min)
pip install pyinstaller
python build_exe.py           # arma dist/GeoGuessr-Santander-Offline.exe
```

Para probar sin empaquetar: `python server.py` (o doble clic en `jugar_local.bat`).

---

## Qué hay adentro

| Archivo | Para qué |
|---|---|
| `app/locations.json` | Las ubicaciones del juego. El que tiene `"pinned": true` **siempre sale en la primera ronda**. |
| `download_tiles.py` | Baja los tiles de satélite y de calles (ambos de Esri) y los mete en `tiles.db`. |
| `app/` | El juego: `index.html` + `game.js` + Leaflet vendorizado. Cero CDN. |
| `server.py` | Servidor local que sirve `app/` y saca los tiles de `tiles.db`. Es el punto de entrada del `.exe`. |
| `build_exe.py` | Empaqueta todo lo anterior en un único ejecutable con PyInstaller. |
| `tiles.db` | Los mapas (no se sube a git, se regenera con `download_tiles.py`). |

---

## Agregar o cambiar colegios

1. Editar `app/locations.json` (nombre, `lat`, `lon`).
2. `python download_tiles.py` — solo baja lo que falta, lo ya descargado no se repite.
3. `python build_exe.py`.

Para que un lugar salga siempre de primero, ponerle `"pinned": true` (solo uno).

---

## Cobertura de los mapas descargados

- **Satélite (fase de pistas):** zoom 16–19 alrededor de cada ubicación de `app/locations.json`.
  La escalera de pistas es 19 → 18 → 17 → 16. **No se usa zoom 20**: Esri no tiene
  imagen a ese detalle en Bucaramanga y devuelve un tile gris que dice
  *"Map data not yet available"* (es lo que se ve hoy en la versión de Streamlit).
- **Calles (fase de adivinar):** zoom 11–16 en el área metropolitana
  (lat 7.020–7.200, lon −73.230 → −73.040) y zoom 17 en el núcleo urbano.

Fuera de esa zona el mapa se ve gris: no está descargado. Si necesitas más área,
se ajustan `METRO_BBOX` / `CORE_BBOX` en `download_tiles.py` y se vuelve a bajar.

Las dos capas salen de los servicios públicos de ArcGIS Online (`World_Imagery` y
`World_Street_Map`). **No se usa `tile.openstreetmap.org`**: su política prohíbe la
descarga masiva y responde con un tile *"Access blocked"* que llega con código 200,
así que se cuela como si fuera un mapa bueno. Por eso `download_tiles.py` corre una
verificación al final y avisa si un zoom trae imágenes repetidas.

Atribución: Tiles © Esri.

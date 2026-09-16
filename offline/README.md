# GeoGuessr Santander — versión offline

Misma dinámica que la app de Streamlit (`demo.py`), pero funcionando **sin internet**:
se copia a un USB, se abre en el portátil del colegio y ya. No necesita Python,
ni Streamlit, ni conexión. Los mapas viajan adentro del paquete.

Hay **dos formatos** del mismo juego. Se generan del mismo código:

| | `.exe` | Carpeta |
|---|---|---|
| Qué es | Un solo archivo de ~73 MB | Una carpeta (o su `.zip`) de ~68 MB |
| Cómo se abre | Doble clic al `.exe` | Doble clic a `index.html` |
| Ventaja | Un archivo, nada más que copiar | **Ningún ejecutable**, así que ningún antivirus lo toca |
| Desventaja | Algunos antivirus lo bloquean (ver abajo) | Son ~5.000 archivos, copiar al USB tarda |

**Si el antivirus bloquea el `.exe`, hay que usar la carpeta.** No es un falso
"quizás": PyInstaller arma un ejecutable que se auto-descomprime en memoria, que es
justo lo que hacen los empaquetadores de malware, así que salta por heurística.
Firmarlo requiere un certificado de pago. La carpeta esquiva el problema entero
porque no contiene nada ejecutable, solo HTML, JS e imágenes.

---

## Para el que solo quiere jugar

**Con el .exe:** doble clic → se abre una ventana negra y enseguida el navegador.
**No cerrar la ventana negra** mientras se juega.

**Con la carpeta:** descomprimir el zip y doble clic en `index.html`. Hay que copiar
la carpeta **completa**: los mapas están en la subcarpeta `tiles/`.

> Windows SmartScreen puede avisar "aplicación desconocida" la primera vez que se
> abre el `.exe` (pasa con cualquier ejecutable sin firma). Eso no es el antivirus:
> se pasa con *Más información → Ejecutar de todas formas*.

---

## Para reconstruirlo (con internet, una sola vez)

```
cd offline
python download_tiles.py      # descarga los mapas -> tiles.db  (~10 min)
pip install pyinstaller
python build_exe.py           # -> dist/GeoGuessr-Santander-Offline.exe
python export_carpeta.py      # -> dist/GeoGuessr-Santander-Offline-carpeta(.zip)
```

Para probar sin empaquetar: `python server.py` (o doble clic en `jugar_local.bat`).

---

## Qué hay adentro

| Archivo | Para qué |
|---|---|
| `app/locations.js` | Las ubicaciones del juego. El que tiene `"pinned": true` **siempre sale en la primera ronda**. |
| `download_tiles.py` | Baja los tiles de satélite y de calles (ambos de Esri) y los mete en `tiles.db`. |
| `app/` | El juego: `index.html` + `game.js` + Leaflet vendorizado. Cero CDN. |
| `server.py` | Servidor local que sirve `app/` y saca los tiles de `tiles.db`. Es el punto de entrada del `.exe`. |
| `build_exe.py` | Empaqueta todo en un único ejecutable con PyInstaller. |
| `export_carpeta.py` | Escupe la versión carpeta: los tiles como archivos sueltos, sin ejecutable. |
| `tiles.db` | Los mapas (no se sube a git, se regenera con `download_tiles.py`). |

Las ubicaciones están en un `.js` y no en un `.json` a propósito: así la carpeta
funciona abriendo `index.html` con doble clic, donde el navegador bloquea el
`fetch()` de un `.json` local.

---

## Agregar o cambiar colegios

1. Editar `app/locations.js` (nombre, `lat`, `lon`).
2. `python download_tiles.py` — solo baja lo que falta, lo ya descargado no se repite.
3. `python build_exe.py` y/o `python export_carpeta.py`.

Para que un lugar salga siempre de primero, ponerle `"pinned": true` (solo uno).

---

## Cobertura de los mapas descargados

- **Satélite (fase de pistas):** zoom 16–19 alrededor de cada ubicación de `app/locations.js`.
  La escalera de pistas es 19 → 18 → 17 → 16. **No se usa zoom 20**: Esri no tiene
  imagen a ese detalle en Bucaramanga y devuelve un tile gris que dice
  *"Map data not yet available"* (es lo que se ve hoy en la versión de Streamlit).
- **Calles (fase de adivinar):** zoom 11–16 en el área metropolitana
  (lat 7.020–7.200, lon −73.230 → −73.040) y zoom 17 en el núcleo urbano.

Fuera de esa zona el mapa se ve gris: no está descargado. Si se necesita más área,
se ajustan `METRO_BBOX` / `CORE_BBOX` en `download_tiles.py` y se vuelve a bajar.

### Por qué el mapa de calles no es el de OpenStreetMap

La versión online usa el OSM estándar, pero ese no se puede empaquetar: la política
de `tile.openstreetmap.org` prohíbe la descarga masiva, y el servidor responde con
un tile *"Access blocked"* que llega con **código 200**, así que se cuela como si
fuera un mapa bueno. (Pasó: la primera versión de esto quedó con el mapa lleno de
carteles de error.) Los espejos de la comunidad (`.fr`, `.de`) tienen la misma
política, y CARTO ahora exige API key.

De las alternativas sin API key, `World_Topo_Map` de Esri es la que mejor se lee:
trae nombres de carrera y calle desde el zoom 14. Por eso `download_tiles.py`
verifica al final que ningún zoom traiga imágenes repetidas — así un bloqueo de
este tipo se detecta en la descarga y no en pleno colegio.

Atribución: Tiles © Esri (`World_Imagery` y `World_Topo_Map`).

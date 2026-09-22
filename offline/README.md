# GeoGuessr Santander — versión offline

Misma dinámica que la app de Streamlit (`demo.py`), pero funcionando **sin internet**:
se copia a un USB, se abre en el portátil del colegio y ya. No necesita Python,
ni Streamlit, ni conexión. Los mapas viajan adentro del paquete.

Se entrega como una **carpeta con un `.exe` adentro** (~52 MB, 41 MB comprimida).

---

## Para el que solo quiere jugar

1. Descomprimir el zip y copiar la carpeta **completa** al computador o al USB.
2. Doble clic en `GeoGuessr-Santander-Offline.exe`.
3. Se abre una ventana negra y enseguida el navegador con el juego.
4. **No cerrar la ventana negra** mientras se juega.

> El `.exe` solo no sirve: al lado van los mapas y las librerías, en `_internal/`.
>
> Windows puede avisar "aplicación desconocida" (SmartScreen) porque el programa
> no está firmado digitalmente: *Más información → Ejecutar de todas formas*.

---

## Cómo se ve igual que el online

La versión online usa tiles de OpenStreetMap, que el navegador de cada estudiante
pide en vivo. Eso está permitido; lo que **no** se puede es bajarlos en bloque para
guardarlos, y ahí se rompía todo intento de copiar ese aspecto:

- `tile.openstreetmap.org` bloquea la descarga masiva, y encima responde con un
  tile *"Access blocked"* que llega con **código 200**, así que se cuela como si
  fuera un mapa bueno. (Pasó: una versión quedó con el mapa lleno de carteles de error.)
- Los espejos de la comunidad (`.fr`, `.de`) tienen la misma política.
- CARTO ahora exige API key y estampa una marca de agua sin ella.
- Las capas de Esri sí se pueden usar, pero **no rotulan lugares**: ni colegios, ni
  parques, ni barrios. Solo calles. Sin esos nombres el estudiante no tiene de dónde
  agarrarse para ubicarse.

La salida fue separar los datos del dibujo. En vez de guardar imágenes ya
dibujadas, se guardan los **datos vectoriales** de OSM y el navegador los dibuja en
el momento con MapLibre. La fuente es [Protomaps](https://protomaps.com), que publica
el planeta como un único archivo PMTiles pensado justamente para uso offline.

Resultado: el aspecto del OSM real —parques verdes, manzanas, cada colegio y parque
rotulado, texto nítido a cualquier zoom— en **4,9 MB** de datos para toda el área
metropolitana. La versión anterior, con imágenes de Esri, gastaba 45 MB y se veía peor.

---

## Para reconstruirlo (con internet, una sola vez)

```
cd offline
python download_tiles.py      # foto satelital de cada ubicacion -> tiles.db
python download_vector.py     # mapa vectorial de OSM            -> tiles.db
pip install pyinstaller
python build_exe.py           # -> dist/GeoGuessr-Santander-Offline(.zip)
```

Para probar sin empaquetar: `python server.py`.

---

## Qué hay adentro

| Archivo | Para qué |
|---|---|
| `app/locations.js` | Las ubicaciones del juego. El que tiene `"pinned": true` **siempre sale en la primera ronda**. |
| `download_tiles.py` | Baja la foto satelital (Esri) de cada ubicación: es la capa de la fase de pistas. |
| `download_vector.py` | Baja el mapa vectorial de OSM (Protomaps) del área metropolitana: es la fase de adivinar. |
| `app/` | El juego: `index.html` + `game.js` + MapLibre, el tema de Protomaps, fuentes y sprites. Cero CDN. |
| `server.py` | Servidor local que sirve `app/` y saca los tiles de `tiles.db`. Es el punto de entrada del `.exe`. |
| `build_exe.py` | Empaqueta todo con PyInstaller. |
| `tiles.db` | Los mapas (no se sube a git, se regenera con los dos descargadores). |

---

## Por qué el paquete es una carpeta y no un solo .exe

Antes era un `.exe` único y **el antivirus lo bloqueaba**. No es casualidad: el modo
archivo único de PyInstaller arma un ejecutable que se auto-descomprime en memoria
al arrancar, que es exactamente lo que hacen los empaquetadores de malware, así que
salta por heurística aunque esté limpio. Firmarlo requiere un certificado de pago.

El modo carpeta (`--onedir`) no hace eso y pasa sin problema. Por eso `build_exe.py`
usa `--onedir`; no cambiarlo a `--onefile` sin recordar este párrafo.

---

## Agregar o cambiar colegios

1. Editar `app/locations.js` (nombre, `lat`, `lon`).
2. `python download_tiles.py` — solo baja lo que falta.
3. `python build_exe.py`.

`download_vector.py` no hace falta correrlo de nuevo salvo que la ubicación nueva
quede fuera del área metropolitana; en ese caso se amplía `BBOX` y se vuelve a bajar.

Para que un lugar salga siempre de primero, ponerle `"pinned": true` (solo uno).

---

## Cobertura de los mapas descargados

- **Satélite (fase de pistas):** zoom 16–19 alrededor de cada ubicación de `app/locations.js`.
  La escalera de pistas es 19 → 18 → 17 → 16. **No se usa zoom 20**: Esri no tiene
  imagen a ese detalle en Bucaramanga y devuelve un tile gris que dice
  *"Map data not yet available"* (es lo que se ve hoy en la versión de Streamlit).
- **Mapa vectorial (fase de adivinar):** zoom 0–15 sobre el área metropolitana
  (lat 7.020–7.200, lon −73.230 → −73.040). Arriba de 15 no hace falta bajar nada:
  MapLibre reescala los mismos vectores y el texto sigue saliendo nítido.

Fuera de esa zona el mapa se ve vacío. Si se necesita más área, se ajusta `BBOX` en
`download_vector.py` (y `METRO_BOUNDS` en `app/game.js`) y se vuelve a bajar.

El juego necesita **WebGL**, que es lo que usa MapLibre para dibujar. Cualquier
Chrome o Edge de los últimos años lo tiene; si falta, la app lo avisa en pantalla
en vez de mostrar un mapa en blanco.

Atribución: satélite © Esri (`World_Imagery`).
Mapa y nombres © colaboradores de OpenStreetMap (ODbL), vía Protomaps.

# GeoGuessr Santander

Juego tipo GeoGuessr con fotos aéreas de Bucaramanga, para las sesiones de
**Hands-on Computer Vision** en colegios.

Se ve un lugar desde arriba, solo se puede hacer zoom out (3 pistas), y luego hay
que marcar en el mapa dónde queda. El puntaje baja con la distancia.

---

## Las dos versiones

| | Online | Offline |
|---|---|---|
| **Link** | **[geoguessr-hocv.streamlit.app](https://geoguessr-hocv.streamlit.app/)** | **[Descargar](https://github.com/Jeferson0809/Geoguessr-Santander/releases/latest)** |
| Necesita internet | Sí | **No** |
| Necesita instalar algo | No | No |
| Hecho con | Streamlit + Folium ([`demo.py`](demo.py)) | HTML + MapLibre + tiles vectoriales ([`offline/`](offline/)) |
| Cuándo usarla | Salón con buen wifi | **Colegios** — es la que hay que llevar |

### Offline: cómo se usa

Se descarga `GeoGuessr-Santander-Offline.zip` (~41 MB), se descomprime y se copia
la carpeta **completa** al computador o al USB. Doble clic en
`GeoGuessr-Santander-Offline.exe`: se abre una ventana negra y enseguida el
navegador con el juego. **No cerrar la ventana negra** mientras se juega.

El `.exe` solo no sirve: al lado van los mapas y las librerías, en `_internal/`.

> Windows puede avisar "aplicación desconocida" (SmartScreen) porque el programa no
> está firmado: *Más información → Ejecutar de todas formas*. Eso no es el antivirus.

El mapa es el mismo de OpenStreetMap que ves online — parques, manzanas y el nombre
de cada colegio y parque — pero dibujado desde datos guardados en el paquete, sin
tocar internet. El cómo está en [`offline/README.md`](offline/README.md).

### Online: cómo se usa

Se abre el link y ya: **[geoguessr-hocv.streamlit.app](https://geoguessr-hocv.streamlit.app/)**.
No hay que instalar ni correr nada.

<details>
<summary>Solo para desarrollo: correr esa misma versión en tu computador</summary>

```bash
pip install -r requirements.txt
streamlit run demo.py
```

Sirve para probar cambios antes de subirlos. Para jugar no hace falta.
</details>

---

## Ubicaciones

Las dos versiones arrancan **siempre** en el colegio que toca visitar, y después
pasan al resto de lugares al azar.

- Offline: se edita [`offline/app/locations.js`](offline/app/locations.js) (el que tiene `"pinned": true` va primero).
- Online: se edita la lista `LOCATIONS` en [`demo.py`](demo.py) (`PINNED` va primero).

Para reconstruir el paquete después de cambiar ubicaciones, ver [`offline/README.md`](offline/README.md).

---

Mapas: satélite © Esri. Calles y nombres © colaboradores de OpenStreetMap (ODbL),
en la versión offline vía Protomaps.

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
| Hecho con | Streamlit + Folium ([`demo.py`](demo.py)) | HTML + Leaflet, sin servidor ([`offline/`](offline/)) |
| Cuándo usarla | Salón con buen wifi | **Colegios** — es la que hay que llevar |

### Offline: cómo se usa

En la [página de descargas](https://github.com/Jeferson0809/Geoguessr-Santander/releases/latest)
hay **dos formatos del mismo juego**. Los dos funcionan sin internet.

**`GeoGuessr-Santander-Offline.exe`** (~73 MB) — un solo archivo.
Doble clic, se abre una ventana negra y enseguida el navegador.
**No cerrar la ventana negra** mientras se juega.

**`GeoGuessr-Santander-Offline-carpeta.zip`** (~67 MB) — sin ejecutable.
Descomprimir y doble clic en `index.html`. Hay que copiar la carpeta **completa**:
los mapas están en la subcarpeta `tiles/`.

> **¿Cuál llevar?** El `.exe` es más cómodo, pero algunos antivirus lo bloquean:
> PyInstaller arma un ejecutable que se auto-descomprime, que es lo mismo que hacen
> los empaquetadores de malware, así que salta por heurística aunque esté limpio.
> **Si el antivirus lo borra o lo manda a cuarentena, usá la carpeta**, que no tiene
> nada que ejecutar. Cosa distinta es el aviso azul de "aplicación desconocida"
> (SmartScreen): eso no es el antivirus y se pasa con
> *Más información → Ejecutar de todas formas*.

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

Para reconstruir el .exe después de cambiar ubicaciones, ver [`offline/README.md`](offline/README.md).

---

Mapas: Tiles © Esri (World Imagery y World Topo Map). La versión online usa OpenStreetMap;
la offline no puede, porque sus tiles no se permiten descargar en bloque — el detalle está
en [`offline/README.md`](offline/README.md).

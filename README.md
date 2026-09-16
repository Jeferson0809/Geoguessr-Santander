# GeoGuessr Santander

Juego tipo GeoGuessr con fotos aéreas de Bucaramanga, para las sesiones de
**Hands-on Computer Vision** en colegios.

Se ve un lugar desde arriba, solo se puede hacer zoom out (3 pistas), y luego hay
que marcar en el mapa dónde queda. El puntaje baja con la distancia.

---

## Las dos versiones

| | Online | Offline |
|---|---|---|
| **Link** | **[geoguessr-hocv.streamlit.app](https://geoguessr-hocv.streamlit.app/)** | **[Descargar el .exe](https://github.com/Jeferson0809/Geoguessr-Santander/releases/latest)** |
| Necesita internet | Sí | **No** |
| Necesita instalar algo | No | No |
| Hecho con | Streamlit + Folium ([`demo.py`](demo.py)) | HTML + Leaflet en un solo .exe ([`offline/`](offline/)) |
| Cuándo usarla | Salón con buen wifi | **Colegios** — es la que hay que llevar |

### Offline: cómo se usa

1. Descargar `GeoGuessr-Santander-Offline.exe` y copiarlo al portátil (o a un USB).
2. Doble clic.
3. Se abre una ventana negra y enseguida el navegador con el juego.
4. **No cerrar la ventana negra** mientras se juega.

Pesa ~68 MB porque los mapas van **dentro** del ejecutable. No hace ni una sola
petición a internet. Windows puede mostrar el aviso de "aplicación desconocida"
la primera vez (pasa con cualquier .exe sin firma): *Más información → Ejecutar de todas formas*.

### Online: cómo se corre localmente

```bash
pip install -r requirements.txt
streamlit run demo.py
```

---

## Ubicaciones

Las dos versiones arrancan **siempre** en el colegio que toca visitar, y después
pasan al resto de lugares al azar.

- Offline: se edita [`offline/app/locations.json`](offline/app/locations.json) (el que tiene `"pinned": true` va primero).
- Online: se edita la lista `LOCATIONS` en [`demo.py`](demo.py) (`PINNED` va primero).

Para reconstruir el .exe después de cambiar ubicaciones, ver [`offline/README.md`](offline/README.md).

---

Mapas: Tiles © Esri (World Imagery y World Street Map).

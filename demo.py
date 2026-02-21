import random
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
def add_crosshair(m, size=28, thickness=3, color="#32CD32", glow=True):
    glow_css = f"filter: drop-shadow(0 0 8px {color});" if glow else ""
    html = f"""
    <style>
      .crosshair {{
        position: absolute;
        top: 50%;
        left: 50%;
        width: {size}px;
        height: {size}px;
        margin-left: -{size//2}px;
        margin-top: -{size//2}px;
        pointer-events: none;
        z-index: 999999;
      }}
      .crosshair:before, .crosshair:after {{
        content: "";
        position: absolute;
        background: {color};
        {glow_css}
        opacity: 0.95;
      }}
      .crosshair:before {{
        left: 50%;
        top: 0%;
        width: {thickness}px;
        height: 100%;
        margin-left: -{thickness//2}px;
        border-radius: 999px;
      }}
      .crosshair:after {{
        top: 50%;
        left: 0%;
        height: {thickness}px;
        width: 100%;
        margin-top: -{thickness//2}px;
        border-radius: 999px;
      }}
      /* puntito central */
      .crosshair .dot {{
        position:absolute;
        top:50%;
        left:50%;
        width:{thickness*2}px;
        height:{thickness*2}px;
        margin-left:-{thickness}px;
        margin-top:-{thickness}px;
        border-radius:999px;
        background:{color};
        {glow_css}
      }}
    </style>

    <div class="crosshair"><div class="dot"></div></div>
    """
    m.get_root().html.add_child(folium.Element(html))
# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Hands-on Computer Vision | GeoGuessr", layout="wide")

# -----------------------------
# Ocultar barra superior Streamlit + ajustar layout
# -----------------------------
st.markdown(
    """
    <style>
      header {visibility: hidden;}
      [data-testid="stToolbar"] {visibility: hidden;}
      [data-testid="stDecoration"] {visibility: hidden;}
      [data-testid="stStatusWidget"] {visibility: hidden;}
      [data-testid="stHeader"] {visibility: hidden;}

      /* Más ancho, menos padding */
      .block-container {
        padding-top: 0.2rem !important;
        padding-bottom: 1.2rem !important;
        max-width: 1500px !important;
      }

      /* Reducir espacios grandes */
      .stMarkdown { margin-bottom: 0.2rem; }

      /* Botones estilo “chip” */
      .stButton>button {
        border-radius: 14px;
        border: 1px solid rgba(50,205,50,0.35);
        background: linear-gradient(180deg, rgba(13,21,32,0.92), rgba(8,12,18,0.92));
        transition: transform 0.06s ease, border 0.2s ease, box-shadow 0.2s ease;
        padding: 0.45rem 0.8rem;
      }
      .stButton>button:hover {
        border: 1px solid rgba(50,205,50,0.65);
        box-shadow: 0 0 18px rgba(50,205,50,0.14);
      }
      .stButton>button:active { transform: translateY(1px); }

      /* Fondo */
      .stApp {
        background: radial-gradient(1200px 600px at 20% 0%, rgba(50,205,50,0.12), transparent 60%),
                    radial-gradient(900px 500px at 90% 10%, rgba(0,255,180,0.08), transparent 55%),
                    linear-gradient(180deg, #05070C 0%, #05070C 100%);
      }

      div[data-testid="stAlert"] {
        border-radius: 14px;
        border: 1px solid rgba(50,205,50,0.18);
        background: rgba(13,21,32,0.65);
      }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Config
# -----------------------------
LOCATIONS = [
    {"name": "Parque del Agua", "lat": 7.1224, "lon": -73.1155},
    {"name": "Biblioteca UIS", "lat": 7.140988, "lon": -73.120911},
    {"name": "Estadio Américo Montanini", "lat": 7.136685, "lon": -73.116535},
    {"name": "Parque San Pio", "lat": 7.118566, "lon": -73.110505},
    {"name": "Parque de los niños", "lat": 7.125140, "lon": -73.119015},
    {"name": "Aeropuerto Palonegro", "lat": 7.127934, "lon": -73.183150},
    {"name": "Parque La Flora", "lat":  7.108590, "lon": -73.107533},
    {"name": "Centro Comercial el Cacique", "lat": 7.099290, "lon":  -73.107281},
    {"name": "Centro Comercial Sandresito La Isla", "lat": 7.108622, "lon": -73.117683},
    {"name": "Parque las cigarras", "lat": 7.103767, "lon": -73.121245},

]

# Pistas: inicio + 3 zoom-outs
ZOOM_LEVELS = [20, 19, 18, 17]
MAX_SCORE = 1000

# Satélite (drone)
SAT_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
SAT_ATTR = "Tiles © Esri"

# Adivinar inicia centrado en Bucaramanga
GUESS_CENTER_DEFAULT = (7.119, -73.123)
GUESS_ZOOM_DEFAULT = 12

# Altura del mapa (encaja mejor a 100%)
MAP_HEIGHT = 540

# -----------------------------
# State
# -----------------------------
if "target" not in st.session_state:
    st.session_state.target = random.choice(LOCATIONS)
if "zoom_idx" not in st.session_state:
    st.session_state.zoom_idx = 0
if "phase" not in st.session_state:
    st.session_state.phase = "clue"  # clue -> guess -> result
if "guess" not in st.session_state:
    st.session_state.guess = None

# 👇 clave para NO resetear al mover
if "guess_view" not in st.session_state:
    st.session_state.guess_view = {"center": GUESS_CENTER_DEFAULT, "zoom": GUESS_ZOOM_DEFAULT}

def reset_game():
    st.session_state.target = random.choice(LOCATIONS)
    st.session_state.zoom_idx = 0
    st.session_state.phase = "clue"
    st.session_state.guess = None
    st.session_state.guess_view = {"center": GUESS_CENTER_DEFAULT, "zoom": GUESS_ZOOM_DEFAULT}

target = st.session_state.target
target_latlon = (target["lat"], target["lon"])

# -----------------------------
# Header (logo + nombre)
# -----------------------------
header_l, header_r = st.columns([1, 8])
with header_l:
    try:
        st.image("assets/logo.png", width=200)
    except Exception:
        pass
with header_r:
    st.markdown(
        """
        <div style="display:flex;flex-direction:column;gap:2px;">
          <div style="font-size:40px;font-weight:700;line-height:1.1;color:#EAF2FF;">
            Hands-on Computer Vision
          </div>
          <div style="opacity:0.80;font-size:30px;margin-top:-2px;color:#C9D6FF;">
            GeoGuessr Aéreo — Zoom-only • Bucaramanga/Santander
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<hr style='opacity:0.25;margin:0.8rem 0 0.8rem 0;'/>", unsafe_allow_html=True)

# -----------------------------
# Controls
# -----------------------------
top1, top2, top3, top4 = st.columns([1, 1, 1, 1])

with top1:
    if st.button("🔄 Nuevo lugar", use_container_width=True):
        reset_game()
        st.rerun()

with top2:
    if st.button("➕ Zoom IN", use_container_width=True, disabled=(st.session_state.phase != "clue")):
        if st.session_state.zoom_idx > 0:
            st.session_state.zoom_idx -= 1
            st.rerun()

with top3:
    if st.button("➖ Zoom OUT", use_container_width=True, disabled=(st.session_state.phase != "clue")):
        if st.session_state.zoom_idx < len(ZOOM_LEVELS) - 1:
            st.session_state.zoom_idx += 1
            st.rerun()

with top4:
    if st.session_state.phase == "clue":
        if st.button("🎯 Ir a adivinar", use_container_width=True):
            st.session_state.phase = "guess"
            st.rerun()
    elif st.session_state.phase == "guess":
        if st.button("✅ Finalizar", use_container_width=True, disabled=(st.session_state.guess is None)):
            st.session_state.phase = "result"
            st.rerun()
    else:
        if st.button("🔁 Jugar de nuevo", use_container_width=True):
            reset_game()
            st.rerun()

# -----------------------------
# Phase: CLUE (satélite, NO pan, NO scroll zoom, NO click)
# -----------------------------
if st.session_state.phase == "clue":
    zoom = ZOOM_LEVELS[st.session_state.zoom_idx]
    st.caption(f"FASE 1/2 — Pistas | Zoom {zoom} | {st.session_state.zoom_idx}/{len(ZOOM_LEVELS)-1} zoom-outs usados")

    m = folium.Map(
        location=target_latlon,
        zoom_start=zoom,
        tiles=SAT_TILES,
        attr=SAT_ATTR,
        zoom_control=False,
        control_scale=False,
    )

    # Anti-trampa
    m.options["dragging"] = False
    m.options["scrollWheelZoom"] = False
    m.options["doubleClickZoom"] = False
    m.options["touchZoom"] = False
    m.options["boxZoom"] = False
    m.options["keyboard"] = False
    add_crosshair(m, size=34, thickness=3, color="#32CD32", glow=True)
    st_folium(
        m,
        height=MAP_HEIGHT,
        use_container_width=True,
        key="clue_map_main",
        returned_objects=[]  # no necesitamos nada aquí, y reduce “eventos”
    )

    st.info("Usa Zoom IN/OUT arriba. Luego pasa a **Ir a adivinar**.")

# -----------------------------
# Phase: GUESS (PAN + ZOOM libre, NO se resetea al mover)
# -----------------------------
elif st.session_state.phase == "guess":
    st.caption("FASE 2/2 — Adivinar | Muévete y haz zoom libremente. Haz 1 click donde crees que estaba el lugar.")

    # ✅ Arranca donde quedó guardado (o Bucaramanga al inicio)
    start_center = st.session_state.guess_view["center"]
    start_zoom = st.session_state.guess_view["zoom"]

    guess_map = folium.Map(
        location=start_center,
        zoom_start=start_zoom,
        tiles="OpenStreetMap",
        control_scale=True,
        zoom_control=True,
    )
    
    # Mostrar marcador si ya hay guess
    if st.session_state.guess is not None:
        folium.Marker(
            st.session_state.guess,
            tooltip="Tu guess",
            icon=folium.Icon(color="blue"),
        ).add_to(guess_map)

    # 🔥 Solo last_clicked para que pan/zoom NO haga rerun
    out = st_folium(
        guess_map,
        height=MAP_HEIGHT,
        use_container_width=True,
        key="guess_map_main",
        returned_objects=["last_clicked"]
    )

    # Guardar click (1 sola vez) + guardar vista centrada ahí
    lc = out.get("last_clicked") if out else None
    if st.session_state.guess is None and lc:
        st.session_state.guess = (lc["lat"], lc["lng"])

        # ✅ guardar vista para que al rerun NO “salte”
        st.session_state.guess_view = {
            "center": (lc["lat"], lc["lng"]),
            "zoom": max(12, GUESS_ZOOM_DEFAULT)  # o fija 12
        }
        st.rerun()

    cA, cB = st.columns([1, 2])
    with cA:
        if st.session_state.guess is None:
            st.warning("Aún no has hecho click.")
        else:
            st.write(f"📍 Guess: **{st.session_state.guess[0]:.6f}, {st.session_state.guess[1]:.6f}**")
            if st.button("🧹 Borrar guess", use_container_width=True):
                st.session_state.guess = None
                st.session_state.guess_view = {"center": GUESS_CENTER_DEFAULT, "zoom": GUESS_ZOOM_DEFAULT}
                st.rerun()

            if st.button("🎯 Recentrar Bucaramanga", use_container_width=True):
                st.session_state.guess_view = {"center": GUESS_CENTER_DEFAULT, "zoom": GUESS_ZOOM_DEFAULT}
                st.rerun()
    with cB:
        st.info("Cuando tengas tu guess, presiona **Finalizar** arriba.")

# -----------------------------
# Phase: RESULT
# -----------------------------
else:
    st.caption("RESULTADO — Distancia y score.")

    view = st.session_state.guess_view

    res_map = folium.Map(
        location=view["center"],
        zoom_start=view["zoom"],
        tiles="OpenStreetMap",
        control_scale=True,
        zoom_control=True,
    )

    # Real
    folium.Marker(target_latlon, tooltip="Ubicación real", icon=folium.Icon(color="red")).add_to(res_map)

    if st.session_state.guess is not None:
        folium.Marker(st.session_state.guess, tooltip="Tu guess", icon=folium.Icon(color="blue")).add_to(res_map)
        folium.PolyLine([st.session_state.guess, target_latlon], weight=4).add_to(res_map)

        d_km = geodesic(st.session_state.guess, target_latlon).km
        score = max(0, int(MAX_SCORE - d_km * 50))

        m1, m2, m3 = st.columns(3)
        m1.metric("Distancia (km)", f"{d_km:.2f}")
        m2.metric("Score", f"{score}/{MAX_SCORE}")
        m3.success(f"Era: {target['name']}")
    else:
        st.warning("No hubo guess.")
        st.success(f"Era: {target['name']}")

    st_folium(
        res_map,
        height=MAP_HEIGHT,
        use_container_width=True,
        key="result_map_main",
        returned_objects=[]
    )

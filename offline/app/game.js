/* GeoGuessr Santander - version offline.

   Misma dinamica que demo.py (Streamlit), pero con MapLibre:
   - fase de pistas: foto satelital de Esri, guardada como imagenes (raster)
   - fase de adivinar: mapa de OpenStreetMap dibujado en vivo desde tiles
     vectoriales de Protomaps, que es lo que hace que se vea igual al online
     (parques, manzanas, y el nombre de cada colegio, parque y barrio)
   Todo sale del servidor local; no se toca internet. */

const ZOOM_LEVELS = [19, 18, 17, 16];   // pista inicial + 3 zoom-outs
const MAX_SCORE = 1000;
const GUESS_CENTER_DEFAULT = [-73.123, 7.119];   // MapLibre usa [lon, lat]
const GUESS_ZOOM_DEFAULT = 13;

// Debe coincidir con BBOX / METRO_BBOX de los descargadores
const METRO_BOUNDS = [[-73.230, 7.020], [-73.040, 7.200]];
const CALLES_MIN_ZOOM = 11;
const CALLES_MAX_ZOOM = 18;
const VT_MAX_ZOOM = 15;      // hasta donde hay datos; MapLibre reescala arriba
const SAT_MIN_ZOOM = 16;
const SAT_MAX_ZOOM = 19;

// Rutas absolutas: MapLibre no resuelve rutas relativas en el estilo.
const BASE = location.href.replace(/[^/]*$/, "");

let LOCATIONS = [];
let PINNED = null;

const state = {
  target: null,
  zoomIdx: 0,
  phase: "clue",          // clue -> guess -> result
  guess: null,
  guessView: { center: GUESS_CENTER_DEFAULT, zoom: GUESS_ZOOM_DEFAULT },
  primeraRonda: true,
};

let map = null;

const $ = (id) => document.getElementById(id);

// --------------------------------------------------------------------------
// Estilos de mapa
// --------------------------------------------------------------------------
function estiloSatelite() {
  return {
    version: 8,
    sources: {
      sat: {
        type: "raster",
        tiles: [BASE + "tiles/sat/{z}/{x}/{y}.jpg"],
        tileSize: 256,
        minzoom: SAT_MIN_ZOOM,
        maxzoom: SAT_MAX_ZOOM,
        attribution: "Imagenes &copy; Esri (copia local)",
      },
    },
    layers: [{ id: "sat", type: "raster", source: "sat" }],
  };
}

function estiloCalles() {
  return {
    version: 8,
    glyphs: BASE + "vendor/fonts/{fontstack}/{range}.pbf",
    sprite: BASE + "vendor/sprites/light",
    sources: {
      protomaps: {
        type: "vector",
        tiles: [BASE + "tiles/vt/{z}/{x}/{y}.mvt"],
        minzoom: 0,
        maxzoom: VT_MAX_ZOOM,
        attribution: "&copy; OpenStreetMap (copia local)",
      },
    },
    // Ojo: el 2do argumento es el OBJETO del tema, no su nombre. Pasando la
    // cadena "light" devuelve capas con todos los colores en undefined y
    // MapLibre rechaza el estilo entero (mapa en negro).
    layers: protomaps_themes_base.layers(
      "protomaps", protomaps_themes_base.namedTheme("light"), { lang: "es" }
    ),
  };
}

// --------------------------------------------------------------------------
function distanciaKm(a, b) {                 // a y b son [lon, lat]
  const R = 6371.0088;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(b[1] - a[1]);
  const dLon = toRad(b[0] - a[0]);
  const h = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(a[1])) * Math.cos(toRad(b[1])) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

function nuevoTarget() {
  if (state.primeraRonda && PINNED) {
    state.primeraRonda = false;
    return PINNED;
  }
  const pool = LOCATIONS.filter((l) => l !== PINNED && l !== state.target);
  const lista = pool.length ? pool : LOCATIONS;
  return lista[Math.floor(Math.random() * lista.length)];
}

function resetGame() {
  state.target = nuevoTarget();
  state.zoomIdx = 0;
  state.phase = "clue";
  state.guess = null;
  state.guessView = { center: GUESS_CENTER_DEFAULT, zoom: GUESS_ZOOM_DEFAULT };
  render();
}

let observador = null;

/* MapLibre fija el tamano del canvas al construirse, y si en ese momento el
   navegador todavia no termino el layout queda con un canvas mas chico que el
   div (el mapa aparece recortado en una esquina). El observador lo mantiene
   sincronizado, y de paso sirve si se cambia el tamano de la ventana o se
   conecta un proyector. */
function crearMapa(opciones) {
  const contenedor = $("mapa");
  const m = new maplibregl.Map(Object.assign({ container: "mapa" }, opciones));
  m.resize();
  if (window.ResizeObserver) {
    observador = new ResizeObserver(function () { m.resize(); });
    observador.observe(contenedor);
  }
  m.once("load", function () { m.resize(); });
  return m;
}

function destruirMapa() {
  if (observador) { observador.disconnect(); observador = null; }
  if (map) { map.remove(); map = null; }
}

function marcador(lonlat, color) {
  return new maplibregl.Marker({ color: color }).setLngLat(lonlat).addTo(map);
}

// --------------------------------------------------------------------------
// FASE 1 - pistas (satelite, sin pan, sin scroll, sin click)
// --------------------------------------------------------------------------
function renderClue() {
  const zoom = ZOOM_LEVELS[state.zoomIdx];
  const target = [state.target.lon, state.target.lat];

  $("caption").textContent =
    "FASE 1/2 - Pistas | Zoom " + zoom + " | " + state.zoomIdx + "/" +
    (ZOOM_LEVELS.length - 1) + " zoom-outs usados";

  destruirMapa();
  map = crearMapa({
    style: estiloSatelite(),
    center: target,
    zoom: zoom,
    interactive: false,        // anti-trampa: ni arrastrar, ni rueda, ni click
    attributionControl: { compact: true },
  });

  $("mira").style.display = "block";
  $("panel").innerHTML =
    '<div class="aviso">Usa <b>Zoom IN / OUT</b> arriba. Luego pasa a <b>Ir a adivinar</b>.</div>';
}

// --------------------------------------------------------------------------
// FASE 2 - adivinar (pan y zoom libres, 1 click)
// --------------------------------------------------------------------------
function renderGuess() {
  $("caption").textContent =
    "FASE 2/2 - Adivinar | Muevete y haz zoom libremente. Haz 1 click donde crees que estaba el lugar.";

  destruirMapa();
  map = crearMapa({
    style: estiloCalles(),
    center: state.guessView.center,
    zoom: state.guessView.zoom,
    minZoom: CALLES_MIN_ZOOM,
    maxZoom: CALLES_MAX_ZOOM,
    maxBounds: METRO_BOUNDS,
    attributionControl: { compact: true },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }));
  $("mira").style.display = "none";

  if (state.guess) marcador(state.guess, "#2b6cb0");

  map.on("click", function (ev) {
    if (state.guess) return;               // 1 solo click, igual que el original
    state.guess = [ev.lngLat.lng, ev.lngLat.lat];
    state.guessView = { center: state.guess, zoom: map.getZoom() };
    render();
  });

  map.on("moveend", function () {
    const c = map.getCenter();
    state.guessView = { center: [c.lng, c.lat], zoom: map.getZoom() };
  });

  if (!state.guess) {
    $("panel").innerHTML =
      '<div class="aviso warn">Aun no has hecho click.</div>' +
      '<div class="aviso">Cuando tengas tu guess, presiona <b>Finalizar</b> arriba.</div>';
  } else {
    $("panel").innerHTML =
      '<div class="aviso">&#128205; Guess: <b>' + state.guess[1].toFixed(6) + ", " +
      state.guess[0].toFixed(6) + '</b></div>' +
      '<div class="fila">' +
      '  <button class="mini" id="btnBorrar">&#129529; Borrar guess</button>' +
      '  <button class="mini" id="btnRecentrar">&#127919; Recentrar Bucaramanga</button>' +
      '</div>' +
      '<div class="aviso">Cuando tengas tu guess, presiona <b>Finalizar</b> arriba.</div>';
    $("btnBorrar").onclick = function () {
      state.guess = null;
      state.guessView = { center: GUESS_CENTER_DEFAULT, zoom: GUESS_ZOOM_DEFAULT };
      render();
    };
    $("btnRecentrar").onclick = function () {
      state.guessView = { center: GUESS_CENTER_DEFAULT, zoom: GUESS_ZOOM_DEFAULT };
      render();
    };
  }
}

// --------------------------------------------------------------------------
// FASE 3 - resultado
// --------------------------------------------------------------------------
function renderResult() {
  $("caption").textContent = "RESULTADO - Distancia y score.";
  const target = [state.target.lon, state.target.lat];

  destruirMapa();
  map = crearMapa({
    style: estiloCalles(),
    center: state.guessView.center,
    zoom: state.guessView.zoom,
    minZoom: CALLES_MIN_ZOOM,
    maxZoom: CALLES_MAX_ZOOM,
    attributionControl: { compact: true },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }));
  $("mira").style.display = "none";

  map.on("load", function () {
    marcador(target, "#e53e3e");
    if (!state.guess) {
      map.jumpTo({ center: target, zoom: 15 });
      return;
    }
    marcador(state.guess, "#2b6cb0");
    map.addSource("linea", {
      type: "geojson",
      data: {
        type: "Feature",
        geometry: { type: "LineString", coordinates: [state.guess, target] },
      },
    });
    map.addLayer({
      id: "linea",
      type: "line",
      source: "linea",
      paint: { "line-color": "#32CD32", "line-width": 4 },
    });
    map.fitBounds([state.guess, target], { padding: 90, maxZoom: 16, duration: 0 });
  });

  if (state.guess) {
    const dKm = distanciaKm(state.guess, target);
    const score = Math.max(0, Math.round(MAX_SCORE - dKm * 50));
    $("panel").innerHTML =
      '<div class="fila">' +
      '  <div class="metrica"><div class="k">Distancia (km)</div><div class="v">' +
      dKm.toFixed(2) + '</div></div>' +
      '  <div class="metrica"><div class="k">Score</div><div class="v">' +
      score + "/" + MAX_SCORE + '</div></div>' +
      '  <div class="metrica"><div class="k">Era</div><div class="v" style="font-size:20px">' +
      state.target.name + '</div></div>' +
      '</div>';
  } else {
    $("panel").innerHTML =
      '<div class="aviso warn">No hubo guess.</div>' +
      '<div class="aviso ok">Era: <b>' + state.target.name + '</b></div>';
  }
}

// --------------------------------------------------------------------------
function render() {
  const esClue = state.phase === "clue";
  $("btnIn").disabled = !esClue || state.zoomIdx === 0;
  $("btnOut").disabled = !esClue || state.zoomIdx === ZOOM_LEVELS.length - 1;

  const fase = $("btnFase");
  if (state.phase === "clue") {
    fase.innerHTML = "&#127919; Ir a adivinar";
    fase.disabled = false;
    fase.onclick = function () { state.phase = "guess"; render(); };
  } else if (state.phase === "guess") {
    fase.innerHTML = "&#9989; Finalizar";
    fase.disabled = state.guess === null;
    fase.onclick = function () { state.phase = "result"; render(); };
  } else {
    fase.innerHTML = "&#128257; Jugar de nuevo";
    fase.disabled = false;
    fase.onclick = resetGame;
  }

  if (state.phase === "clue") renderClue();
  else if (state.phase === "guess") renderGuess();
  else renderResult();
}

$("btnNuevo").onclick = resetGame;
$("btnIn").onclick = function () {
  if (state.zoomIdx > 0) { state.zoomIdx--; render(); }
};
$("btnOut").onclick = function () {
  if (state.zoomIdx < ZOOM_LEVELS.length - 1) { state.zoomIdx++; render(); }
};

// --------------------------------------------------------------------------
if (!maplibregl.supported || maplibregl.supported()) {
  LOCATIONS = LOCATIONS_DATA.locations;
  PINNED = LOCATIONS.filter(function (l) { return l.pinned; })[0] || null;
  resetGame();
} else {
  $("panel").innerHTML =
    '<div class="aviso warn">Este navegador no soporta WebGL, que es lo que ' +
    'necesita el mapa. Proba con Chrome o Edge actualizado.</div>';
}

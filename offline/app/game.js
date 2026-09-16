/* GeoGuessr Santander - version offline.
   Mismo juego que demo.py (Streamlit) pero en Leaflet puro, leyendo los tiles
   desde el servidor local que va dentro del .exe. */

const ZOOM_LEVELS = [19, 18, 17, 16];   // pista inicial + 3 zoom-outs
const MAX_SCORE = 1000;
const GUESS_CENTER_DEFAULT = [7.119, -73.123];
const GUESS_ZOOM_DEFAULT = 12;

// Debe coincidir con METRO_BBOX / zooms de download_tiles.py
const METRO_BOUNDS = L.latLngBounds([7.020, -73.230], [7.200, -73.040]);
const CALLES_MIN_ZOOM = 11;
const CALLES_MAX_ZOOM = 17;
const SAT_MIN_ZOOM = 16;
const SAT_MAX_ZOOM = 19;

// tile gris para huecos (no deberia verse si la descarga esta completa)
const TILE_VACIO =
  "data:image/svg+xml;base64," +
  btoa('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256">' +
       '<rect width="256" height="256" fill="#0b0f16"/></svg>');

L.Icon.Default.prototype.options.imagePath = "vendor/images/";

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

function capaSat() {
  return L.tileLayer("tiles/sat/{z}/{x}/{y}", {
    minZoom: SAT_MIN_ZOOM, maxZoom: SAT_MAX_ZOOM,
    minNativeZoom: SAT_MIN_ZOOM, maxNativeZoom: SAT_MAX_ZOOM,
    errorTileUrl: TILE_VACIO, attribution: "Tiles &copy; Esri (copia local)",
  });
}

function capaCalles() {
  return L.tileLayer("tiles/street/{z}/{x}/{y}", {
    minZoom: CALLES_MIN_ZOOM, maxZoom: CALLES_MAX_ZOOM,
    minNativeZoom: CALLES_MIN_ZOOM, maxNativeZoom: CALLES_MAX_ZOOM,
    errorTileUrl: TILE_VACIO, attribution: "Tiles &copy; Esri (copia local)",
  });
}

function distanciaKm(a, b) {
  const R = 6371.0088;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(b[0] - a[0]);
  const dLon = toRad(b[1] - a[1]);
  const h = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(a[0])) * Math.cos(toRad(b[0])) * Math.sin(dLon / 2) ** 2;
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

function destruirMapa() {
  if (map) { map.remove(); map = null; }
}

// --------------------------------------------------------------------------
// FASE 1 - pistas (satelite, sin pan, sin scroll, sin click)
// --------------------------------------------------------------------------
function renderClue() {
  const zoom = ZOOM_LEVELS[state.zoomIdx];
  const target = [state.target.lat, state.target.lon];

  $("caption").textContent =
    "FASE 1/2 - Pistas | Zoom " + zoom + " | " + state.zoomIdx + "/" +
    (ZOOM_LEVELS.length - 1) + " zoom-outs usados";

  destruirMapa();
  map = L.map("mapa", {
    center: target, zoom: zoom,
    dragging: false, scrollWheelZoom: false, doubleClickZoom: false,
    touchZoom: false, boxZoom: false, keyboard: false,
    zoomControl: false, attributionControl: true,
  });
  capaSat().addTo(map);

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
  map = L.map("mapa", {
    center: state.guessView.center, zoom: state.guessView.zoom,
    zoomControl: true, maxBounds: METRO_BOUNDS, maxBoundsViscosity: 0.8,
    minZoom: CALLES_MIN_ZOOM, maxZoom: CALLES_MAX_ZOOM,
  });
  capaCalles().addTo(map);
  L.control.scale({ imperial: false }).addTo(map);
  $("mira").style.display = "none";

  if (state.guess) {
    L.marker(state.guess).addTo(map).bindTooltip("Tu guess");
  }

  map.on("click", function (ev) {
    if (state.guess) return;               // 1 solo click, igual que el original
    state.guess = [ev.latlng.lat, ev.latlng.lng];
    state.guessView = { center: state.guess, zoom: map.getZoom() };
    render();
  });

  map.on("moveend", function () {
    state.guessView = {
      center: [map.getCenter().lat, map.getCenter().lng],
      zoom: map.getZoom(),
    };
  });

  if (!state.guess) {
    $("panel").innerHTML =
      '<div class="aviso warn">Aun no has hecho click.</div>' +
      '<div class="aviso">Cuando tengas tu guess, presiona <b>Finalizar</b> arriba.</div>';
  } else {
    $("panel").innerHTML =
      '<div class="aviso">&#128205; Guess: <b>' + state.guess[0].toFixed(6) + ", " +
      state.guess[1].toFixed(6) + '</b></div>' +
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
  const target = [state.target.lat, state.target.lon];

  destruirMapa();
  map = L.map("mapa", {
    center: state.guessView.center, zoom: state.guessView.zoom,
    zoomControl: true, minZoom: CALLES_MIN_ZOOM, maxZoom: CALLES_MAX_ZOOM,
  });
  capaCalles().addTo(map);
  L.control.scale({ imperial: false }).addTo(map);
  $("mira").style.display = "none";

  const real = L.marker(target).addTo(map).bindTooltip("Ubicacion real");
  if (real._icon) real._icon.style.filter = "hue-rotate(140deg) saturate(2.2)";

  if (state.guess) {
    L.marker(state.guess).addTo(map).bindTooltip("Tu guess");
    L.polyline([state.guess, target], { weight: 4, color: "#32CD32" }).addTo(map);
    map.fitBounds(L.latLngBounds([state.guess, target]).pad(0.35), { maxZoom: CALLES_MAX_ZOOM });

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
    map.setView(target, 14);
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

fetch("locations.json")
  .then(function (r) { return r.json(); })
  .then(function (data) {
    LOCATIONS = data.locations;
    PINNED = LOCATIONS.filter(function (l) { return l.pinned; })[0] || null;
    resetGame();
  })
  .catch(function (err) {
    $("panel").innerHTML =
      '<div class="aviso warn">No pude cargar locations.json: ' + err + "</div>";
  });

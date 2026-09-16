// Ubicaciones del juego.
// El que tiene "pinned": true SIEMPRE sale en la primera ronda.
//
// Es un .js y no un .json a proposito: asi la carpeta funciona abriendo
// index.html con doble clic (file://), donde fetch() de un .json esta
// bloqueado por el navegador.
const LOCATIONS_DATA =
{
  "_comment": "El primer elemento (pinned=true) siempre sale en la primera ronda. Los demas salen al azar.",
  "locations": [
    {
      "name": "Colegio del Sagrado Corazón de Jesús (Hnas. Bethlemitas)",
      "lat": 7.13543,
      "lon": -73.13055,
      "pinned": true
    },
    {
      "name": "Parque del Agua",
      "lat": 7.130071,
      "lon": -73.109332
    },
    {
      "name": "Biblioteca UIS",
      "lat": 7.140988,
      "lon": -73.120911
    },
    {
      "name": "Estadio Americo Montanini",
      "lat": 7.136685,
      "lon": -73.116535
    },
    {
      "name": "Parque San Pio",
      "lat": 7.118566,
      "lon": -73.110505
    },
    {
      "name": "Parque de los ninos",
      "lat": 7.12514,
      "lon": -73.119015
    },
    {
      "name": "Aeropuerto Palonegro",
      "lat": 7.127934,
      "lon": -73.18315
    },
    {
      "name": "Parque La Flora",
      "lat": 7.10859,
      "lon": -73.107533
    },
    {
      "name": "Centro Comercial el Cacique",
      "lat": 7.09929,
      "lon": -73.107281
    },
    {
      "name": "Centro Comercial Sandresito La Isla",
      "lat": 7.108622,
      "lon": -73.117683
    },
    {
      "name": "Parque las cigarras",
      "lat": 7.103767,
      "lon": -73.121245
    },
    {
      "name": "Parque San Francisco",
      "lat": 7.131202,
      "lon": -73.125035
    },
    {
      "name": "Club Campestre",
      "lat": 7.064437,
      "lon": -73.115783
    }
  ]
};

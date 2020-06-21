
var map = L.map('map').setView([37, -6.4], 10);

L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
  attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

////////////////////////////////////////////////
//////// OLD simple example --> empty overlay
var imageUrl = 'D:/GEO450_data/grass/output/cog_4326/test_cog.tif',
imageBounds = [[36.732445, -6.594324], [37.266466, -6.147788]];

L.imageOverlay(imageUrl, imageBounds).addTo(map);


//////// FROM load-file example
var file = "file:///D:/GEO450_data/grass/output/cog_4326/test_cog.tif";


var reader = new FileReader();

var file_data_url = reader.readAsDataURL(file)

reader.readAsArrayBuffer(file_data_url);
reader.onloadend = function() {
    var arrayBuffer = reader.result;
    parseGeoraster(arrayBuffer).then(georaster => {
    console.log("georaster:", georaster);

    var layer = new GeoRasterLayer({
        georaster: georaster,
        opacity: 0.8,
        resolution: 256
    });

    layer.addTo(map);

    map.fitBounds(layer.getBounds());

  });
};

//////// FROM main.js (local hosting)
var file = "file:///D:/GEO450_data/grass/output/cog_4326/test_cog.tif";

fetch(file)
  .then(response => response.arrayBuffer())
  .then(arrayBuffer => {
    parse_georaster(arrayBuffer).then(georaster => {
      console.log("georaster:", georaster);


      var layer = new GeoRasterLayer({
          georaster: georaster,
          opacity: 0.8,
          resolution: 256
      });

      layer.addTo(map);

      map.fitBounds(layer.getBounds());

  });
});
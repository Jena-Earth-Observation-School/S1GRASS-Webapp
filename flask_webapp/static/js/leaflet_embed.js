// center of the map
var center = [50.926453, 11.587832];

// The first parameter are the coordinates of the center of the map
// The second parameter is the zoom level
var map = L.map('map').setView(center, 11);

// {s}, {z}, {x} and {y} are placeholders for map tiles
// {x} and {y} are the map coordinates
// {z} is the zoom level
// {s} is the subdomain
var layer = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> Contributors',
    maxZoom: 18
});

//CartoDB map alternative
//var layer = L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
//    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'
//});

// Now add the layer onto the map
map.addLayer(layer);

// add marker with popup
//L.marker(center).addTo(map)
//    .bindPopup("<strong>Crazy People</strong>").openPopup();

// Initialise the FeatureGroup to store editable layers
var editableLayers = new L.FeatureGroup();
map.addLayer(editableLayers);

///////////////////////////////////////////////////////////////////////
//options for Leaflet.Draw to get a toolbar for drawing geometries
var drawPluginOptions = {
//    position: 'topright',
    draw: {
//        disable toolbar item by setting it to false
        polyline: false,
//        circle: false,
        circlemarker: false,
//        rectangle: false,
        marker: false
//    polygon: {
//        allowIntersection: false, // Restricts shapes to simple polygons
//        drawError: {
//            color: '#e1e100', // Color the shape will turn when intersects
//            message: '<strong>Oh snap!<strong> you can\'t draw that!' // Message that will show when intersect
//        },
//        shapeOptions: {
//            color: '#97009c'
//        }
//    },
    },
    edit: {
        featureGroup: editableLayers, //REQUIRED!!
        remove: true
    }
};
///////////////////////////////////////////////////////////////////////
// Initialise the draw control and pass it the FeatureGroup of editable layers
// L is the Leaflet library
var drawControl = new L.Control.Draw(drawPluginOptions);
map.addControl(drawControl);

map.on('draw:created', function(e) {
    var type = e.layerType,
        layer = e.layer;
//    if (type === 'marker') {
//        layer.bindPopup('A popup!');
//    }
//    if (type === 'rectangle') {
//        layer.on('mouseover', function() {
//            alert(layer.getLatLngs());
//        });
//    }
    editableLayers.addLayer(layer);
});

//execute function exportGeoJSON on clicking the export button (defined in home.html)
//the document object represents the HTML document that is displayed in that window
document.getElementById('export').onclick = exportGeoJSON;

//alternative click action execution using jQuery
//here: open a file import dialog on click of the Import button
$('#import').on('click', importDialog);

//import and display file-select in the map once it changes
$("#file-select").change(importSHP);

function exportGeoJSON() {
    if (editableLayers.getLayers().length > 0){
        // Extract GeoJSON from featureGroup
        var data = editableLayers.toGeoJSON();

        // Stringify the GeoJSON
        var convertedData = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(data));

        var element = document.createElement('a');
        element.setAttribute('href', convertedData);
        element.setAttribute('download', 'drawnItems.geojson');

        element.style.display = 'none';
        document.body.appendChild(element);

        element.click();

        document.body.removeChild(element);
    } else {
        alert("no geometries found");
    }
}

//taken from http://jsfiddle.net/ashalota/ov0p4ajh/10/
function importSHP(){
	var files = document.getElementById('file-select').files;
	if (files.length == 0) {
	  return; //do nothing if no file given yet
  }

  var file = files[0];

    if (file.name.slice(-3) != 'zip'){ //Demo only tested for .zip. All others, return.
        alert("Please provide a zip file!");
        return;
    } else {
        document.getElementById('warning').innerHTML = ''; //clear warning message.
        handleZipFile(file);
    }
};

function importDialog() {
    $('#file-select').trigger('click');
}
///////////////////////////////////////////////////////////////////////
//More info: https://developer.mozilla.org/en-US/docs/Web/API/FileReader
//taken from http://jsfiddle.net/ashalota/ov0p4ajh/10/
function handleZipFile(file){
    var reader = new FileReader();
    reader.onload = function(){
        if (reader.readyState != 2 || reader.error){
            alert("cannot read file");
            return;
        } else {
            convertToLayer(reader.result);
        }
    }
    reader.readAsArrayBuffer(file);
}

//taken from http://jsfiddle.net/ashalota/ov0p4ajh/10/
function convertToLayer(buffer){
    shp(buffer).then(function(geojson){	//More info: https://github.com/calvinmetcalf/shapefile-js
        var layer = L.geoJson(geojson).addTo(map);
        editableLayers.addLayer(layer);
    });
}
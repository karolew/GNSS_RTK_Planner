/*
Define Map Layers
*/

const OSMLayer = new ol.layer.Tile({
    source: new ol.source.OSM(),
});

const sourceDrawVector = new ol.source.Vector({ wrapX: false });
const vectorDrawLayer = new ol.layer.Vector({
    source: sourceDrawVector,
});

const vectorSource = new ol.source.Vector();
const vectorLayer = new ol.layer.Vector({
    source: vectorSource,
    style: function (feature) {
        // Style function to customize marker appearance based on MAC
        const mac = feature.get('mac');
        return new ol.style.Style({
            image: new ol.style.Circle({
                radius: 6,
                fill: new ol.style.Fill({
                    // Generate a consistent color based on MAC address
                    color: getColorFromMac(mac)
                }),
                stroke: new ol.style.Stroke({
                    color: '#fff',
                    width: 2
                })
            }),
            text: new ol.style.Text({
                text: mac,
                offsetY: -15,
                fill: new ol.style.Fill({
                    color: '#000'
                }),
                stroke: new ol.style.Stroke({
                    color: '#fff',
                    width: 3
                })
            })
        });
    }
});

/*
Define Map
*/
const map = new ol.Map({
    target: 'map',
    layers: [OSMLayer, vectorDrawLayer, vectorLayer],
    view: new ol.View({
        center: ol.proj.fromLonLat([0, 0]),
        zoom: 2
    })
});

/*
Functionalities
*/
// Draw Methods
const drawTypeSelect = document.getElementById('draw-type');

let draw; // global so we can remove it later
export function addInteraction() {
    const value = drawTypeSelect.value;
    if (value !== 'None') {
        draw = new ol.interaction.Draw({
            source: sourceDrawVector,
            type: drawTypeSelect.value,
        });
        map.addInteraction(draw);
    }
}

// Handle draw event
drawTypeSelect.onchange = function () {
    map.removeInteraction(draw);
    addInteraction();
};

document.getElementById('undo').addEventListener('click', function () {
    draw.removeLastPoint();
});


// Initialize a map to store features by MAC address
const macFeatures = {};

function formatUtcTime(timeStr) {
    if (!timeStr) return '-';
    return `${timeStr.slice(0, 2)}:${timeStr.slice(2, 4)}:${timeStr.slice(4, 6)} UTC`;
}

export function updateStatus() {
    fetch('/rover/get_coords')
        .then(response => response.json())
        .then(data => {
            if (data) {
                // Update status panel
                document.getElementById(data.mac + '-fix-status').textContent = data.fix_status;
                document.getElementById(data.mac + '-fix-status').className =
                    data.fix_status === 'Valid' ? 'status-valid' : 'status-invalid';

                document.getElementById(data.mac + '-raw-coords').textContent =
                    data.lat_raw && data.lon_raw ? `${data.lat_raw} / ${data.lon_raw}` : '-';

                document.getElementById(data.mac + '-dec-coords').textContent =
                    data.latitude && data.longitude ?
                        `${data.latitude.toFixed(7)}, ${data.longitude.toFixed(7)}` : '-';

                document.getElementById(data.mac + '-speed').textContent =
                    data.speed !== null ? `${data.speed} knots` : '-';

                document.getElementById(data.mac + '-course').textContent =
                    data.course !== null ? `${data.course}` : '-';

                document.getElementById(data.mac + '-gps-time').textContent =
                    data.time_utc ? formatUtcTime(data.time_utc) : '-';

                document.getElementById(data.mac + '-last-update').textContent =
                    data.last_update || '-';

                // Update map marker
                if (data.latitude && data.longitude && data.mac) {
                    updateMarker(data.mac, data.longitude, data.latitude);
                }
            }
        });
}


function updateMarker(mac, lon, lat) {
    // Convert coordinates to the map's projection (assuming EPSG:3857)
    const coordinates = ol.proj.fromLonLat([parseFloat(lon), parseFloat(lat)]);

    if (macFeatures[mac]) {
        // Update existing feature
        macFeatures[mac].getGeometry().setCoordinates(coordinates);
    } else {
        // Create new feature
        const feature = new ol.Feature({
            geometry: new ol.geom.Point(coordinates),
            mac: mac
        });

        // Store reference to feature
        macFeatures[mac] = feature;

        // Add to source
        vectorSource.addFeature(feature);
    }
}

// Function to generate a color from MAC address
function getColorFromMac(mac) {
    // Simple hash function to generate color from MAC
    let hash = 0;
    for (let i = 0; i < mac.length; i++) {
        hash = mac.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Convert to RGB
    const r = (hash & 0xFF) % 200 + 55; // Avoid too dark colors
    const g = ((hash >> 8) & 0xFF) % 200 + 55;
    const b = ((hash >> 16) & 0xFF) % 200 + 55;

    return `rgb(${r}, ${g}, ${b})`;
}


// Update status given milliseconds
setInterval(updateStatus, 500);

// Get coordinates from map after click
map.on("click", function (e) {
    console.log(e.coordinate);
})

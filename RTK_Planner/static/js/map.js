/*
Define Map Layers
*/

const OSMLayer = new ol.layer.Tile({
    source: new ol.source.OSM(),
    visible: false
});

const satelliteLayer = new ol.layer.Tile({
    source: new ol.source.XYZ({
        url: 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
    }),
    visible: true
});

const hybridLabelsLayer = new ol.layer.Tile({
    source: new ol.source.XYZ({
        url: 'https://mt1.google.com/vt/lyrs=h&x={x}&y={y}&z={z}'
    }),
    visible: true
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
                radius: 7,
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
                font: 15 + 'px sans-serif',
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
    layers: [OSMLayer, satelliteLayer, hybridLabelsLayer, vectorDrawLayer, vectorLayer],
    view: new ol.View({
        center: ol.proj.fromLonLat([0, 0]),
        zoom: 3,
        minZoom: 2,
        maxZoom: 25
    }),
    controls: ol.control.defaults.defaults({
        attributionOptions: {
            collapsible: false
        }
    }).extend([
        new ol.control.ScaleLine(),
        new ol.control.FullScreen()
    ])
});

/*
Functionalities
*/
// Map layers methods.

// Add radio button event listeners
document.querySelectorAll('input[name="mapLayer"]').forEach(radio => {
    radio.addEventListener('change', function () {
        switchLayer(this.value);
    });
});

// Layer switching function
function switchLayer(layerType) {
    switch (layerType) {
        case 'street':
            OSMLayer.setVisible(true);
            satelliteLayer.setVisible(false);
            hybridLabelsLayer.setVisible(false);
            break;
        case 'ortofoto':
            OSMLayer.setVisible(false);
            satelliteLayer.setVisible(true);
            hybridLabelsLayer.setVisible(true);
            break;
    }
}

// Draw Methods
const drawTypeSelect = document.getElementById('draw-type');

let draw; // global so we can remove it later
function addInteraction() {
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
const trailName = document.getElementById("trail-name");
const trailSaveButton = document.getElementById("trail-save-button");
const trailDeleteButton = document.getElementById("trail-delete-button");
const trailConsole = document.getElementById("trail-console");
const trailAllDropdown = document.getElementById("all-trails-dropdown");

function loadTrailsForDropdown() {
    fetch("/api/trails")
        .then(response => response.json())
        .then(data => {
            // Clear existing options except the first one
            while (trailAllDropdown.options.length > 1) {
                trailAllDropdown.remove(1);
            }

            if (data.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No trails associated';
                trailAllDropdown.innerHTML = '';
                trailAllDropdown.appendChild(option);
                return;
            }

            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a trail';
            trailAllDropdown.innerHTML = '';
            trailAllDropdown.appendChild(defaultOption);

            data.forEach(trail => {
                const option = document.createElement('option');
                option.value = trail.id;
                option.textContent = trail.name;
                trailAllDropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading associated trails for dropdown:', error);
            trailAllDropdown.innerHTML = '<option value="">Error loading trails</option>';
        });
}

drawTypeSelect.onchange = function (e) {
    map.removeInteraction(draw);
    addInteraction();
};

document.getElementById('undo-button').addEventListener('click', function () {
    draw.removeLastPoint();
});

document.getElementById("clear-all-button").addEventListener("click", function () {
    sourceDrawVector.getFeatures().forEach(function (feature) {
        sourceDrawVector.removeFeature(feature);
    });
    trailConsole.innerHTML = "";
    trailName.value = "";
});

trailName.addEventListener("input", function () {
    if (trailName.value != "") {
        trailSaveButton.disabled = false;
    } else {
        trailSaveButton.disabled = true;
    }
});

trailSaveButton.addEventListener("click", function () {
    let points = [];
    sourceDrawVector.getFeatures().forEach(function (feature) {
        let coord = feature.getGeometry().getCoordinates();

        // Convert coordinates to DD (Decimal Degrees).
        if (typeof coord === "object" && coord.length > 0 && typeof coord[0] === "number") {
            points.push(ol.proj.transform(coord, 'EPSG:3857', 'EPSG:4326').map((number) => number.toString()));
        } else {
            coord.map(item => {
                points.push(ol.proj.transform(item, 'EPSG:3857', 'EPSG:4326').map((number) => number.toString()));
            });
        }

        // Remove feature to avoid adding coordinates second time in another trail.
        sourceDrawVector.removeFeature(feature);
    });
    if (points.length > 0) {
        fetch('/api/trails', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                trail_points: points,
                name: trailName.value
            })
        })
            .then(response => {
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                loadTrailsForDropdown();
                trailConsole.style.color = '#00AA00';
                trailConsole.innerHTML = "Trail " + data.name + " created.\nPoints: " + data.trail_points
            })
            .catch(error => {
                console.error('Error:', error);
                trailConsole.style.color = '#FF0000';
            });
        trailName.value = "";
        trailSaveButton.disabled = true;
    } else {
        trailConsole.style.color = '#FF0000';
        trailConsole.innerHTML = "Add at least one point or path to the trail."
    }
});

trailDeleteButton.addEventListener("click", function () {
    const selectedTrailName = trailAllDropdown.options[trailAllDropdown.selectedIndex].text;
    if (selectedTrailName != trailAllDropdown.options[0].text) {
        fetch(`/api/trails/${selectedTrailName}`, {
            method: 'DELETE'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to delete trail');
                }
                loadTrailsForDropdown();
                trailConsole.style.color = '#e88740';
                trailConsole.innerHTML = "Trail " + selectedTrailName + " has been deleted."
                return response.json();
            })
            .catch(error => {
                console.error('Error deleting trail:', error);
                alert('Failed to delete trail. Please try again.');
            });
    }
});

loadTrailsForDropdown();

/*
Handle GNSS Markers
*/
// Initialize a map to store features by MAC address
const macFeatures = {};

function formatUtcTime(timeStr) {
    if (!timeStr) return '-';
    return `${timeStr.slice(0, 2)}:${timeStr.slice(2, 4)}:${timeStr.slice(4, 6)} UTC`;
}

// Handle incoming data
new EventSource('/rover/get_coords').onmessage = function (event) {
    let data = JSON.parse(event.data);
    if (data) {
        // Update rover page
        document.getElementById(data.mac + '-fix-status').textContent = data.fix_status;
        document.getElementById(data.mac + '-fix-status').className =
            data.fix_status != 'Unknown' ? 'status-valid' : 'status-invalid';

        document.getElementById(data.mac + '-raw-coords').textContent =
            data.lat_raw && data.lon_raw ? `${data.lat_raw} / ${data.lon_raw}` : '-';

        document.getElementById(data.mac + '-dec-coords').textContent =
            data.latitude && data.longitude ?
                `${data.latitude}, ${data.longitude}` : '-';

        document.getElementById(data.mac + '-speed').textContent =
            data.speed !== null ? `${data.speed} knots` : '-';

        document.getElementById(data.mac + '-course').textContent =
            data.course !== null ? `${data.course}` : '-';

        document.getElementById(data.mac + '-gps-time').textContent =
            data.time_utc ? formatUtcTime(data.time_utc) : '-';

        document.getElementById(data.mac + '-last-update').textContent =
            data.last_update || '-';

        let satUsedHTML = "";
        let totalSat = 0;

        for (const [gnssSystem, satListAll] of Object.entries(data.su)) {
            let satUsedList = satListAll.filter(sat => /\w+/.test(sat));
            if (satUsedList.length > 0) {
                satUsedHTML += `<span class="gnss-${gnssSystem.toLowerCase()}">${gnssSystem}[${satUsedList}]</span> `;
                totalSat += satUsedList.length;
            }
        }

        const element = document.getElementById(data.mac + '-su');
        if (totalSat > 0) {
            element.innerHTML = `${totalSat} in total. ` + satUsedHTML;
        } else {
            element.textContent = 'Unknown';
        }


        // Update map marker
        if (data.latitude && data.longitude && data.mac) {
            updateMarker(data.mac, data.longitude, data.latitude);
        }
    }
};

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

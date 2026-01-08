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
    style: function(feature) {
        const geometry = feature.getGeometry();
        if (geometry.getType() === 'LineString') {
            return createLineStyleWithLabels(geometry, '#3399CC');
        } else {
            // Point style
            return new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 6,
                    fill: new ol.style.Fill({
                        color: '#3399CC'
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#fff',
                        width: 2
                    })
                })
            });
        }
    }
});

// Function to calculate distance between two coordinates in centimeters
function calculateDistance(coord1, coord2) {
    // Convert from map projection to lon/lat
    const lonLat1 = ol.proj.toLonLat(coord1);
    const lonLat2 = ol.proj.toLonLat(coord2);

    // Calculate distance using Haversine formula
    const R = 6378137; // Earth's radius in meters
    const lat1 = lonLat1[1] * Math.PI / 180;
    const lat2 = lonLat2[1] * Math.PI / 180;
    const deltaLat = (lonLat2[1] - lonLat1[1]) * Math.PI / 180;
    const deltaLon = (lonLat2[0] - lonLat1[0]) * Math.PI / 180;

    const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(deltaLon / 2) * Math.sin(deltaLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    const distanceMeters = R * c;
    // Convert to centimeters
    return distanceMeters * 100;
}

// Function to create style with distance labels for line segments
function createLineStyleWithLabels(geometry, color = '#FF6B00') {
    const styles = [
        new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: color,
                width: 3
            })
        })
    ];

    if (geometry.getType() === 'LineString') {
        const coordinates = geometry.getCoordinates();

        // Add distance label for each segment
        for (let i = 0; i < coordinates.length - 1; i++) {
            const start = coordinates[i];
            const end = coordinates[i + 1];
            const midpoint = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2];
            const distance = calculateDistance(start, end);

            styles.push(new ol.style.Style({
                geometry: new ol.geom.Point(midpoint),
                text: new ol.style.Text({
                    text: distance.toFixed(2) + ' cm',
                    font: '12px sans-serif',
                    fill: new ol.style.Fill({
                        color: '#000'
                    }),
                    backgroundFill: new ol.style.Fill({
                        color: 'rgba(255, 255, 255, 0.8)'
                    }),
                    padding: [2, 4, 2, 4],
                    stroke: new ol.style.Stroke({
                        color: '#fff',
                        width: 2
                    })
                })
            }));
        }
    }

    return styles;
}

// Create a separate source and layer for displaying loaded trails
const sourceLoadedTrail = new ol.source.Vector({ wrapX: false });
const vectorLoadedTrailLayer = new ol.layer.Vector({
    source: sourceLoadedTrail,
    style: function(feature) {
        const geometry = feature.getGeometry();
        if (geometry.getType() === 'LineString') {
            return createLineStyleWithLabels(geometry, '#FF6B00');
        } else {
            // Point style
            return new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 6,
                    fill: new ol.style.Fill({
                        color: '#FF6B00'
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#fff',
                        width: 2
                    })
                })
            });
        }
    }
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
    layers: [OSMLayer, satelliteLayer, hybridLabelsLayer, vectorDrawLayer, vectorLoadedTrailLayer, vectorLayer],
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

// Create overlay for cursor distance label
const cursorDistanceElement = document.createElement('div');
cursorDistanceElement.className = 'cursor-distance-label';
cursorDistanceElement.style.cssText = `
    position: absolute;
    background: rgba(255, 255, 255, 0.9);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    pointer-events: none;
    display: none;
    z-index: 1000;
    border: 1px solid #333;
`;
document.body.appendChild(cursorDistanceElement);

let lastDrawPoint = null;
let isDrawing = false;

let draw; // global so we can remove it later
function addInteraction() {
    const value = drawTypeSelect.value;
    if (value !== 'None') {
        draw = new ol.interaction.Draw({
            source: sourceDrawVector,
            type: drawTypeSelect.value,
        });

        // Track when drawing starts
        draw.on('drawstart', function(evt) {
            isDrawing = true;
            lastDrawPoint = null;
            cursorDistanceElement.style.display = 'block';
            cursorDistanceElement.textContent = '0.00 cm';
        });

        // Track when drawing ends
        draw.on('drawend', function(evt) {
            isDrawing = false;
            lastDrawPoint = null;
            cursorDistanceElement.style.display = 'none';
        });

        map.addInteraction(draw);
    } else {
        // Hide label when draw mode is None
        cursorDistanceElement.style.display = 'none';
        isDrawing = false;
        lastDrawPoint = null;
    }
}

// Handle mouse move on map to update cursor distance
map.on('pointermove', function(evt) {
    if (!isDrawing) {
        return;
    }

    const drawType = drawTypeSelect.value;
    if (drawType !== 'Point' && drawType !== 'LineString') {
        return;
    }

    // Update label position to follow cursor
    cursorDistanceElement.style.left = (evt.pixel[0] + 15) + 'px';
    cursorDistanceElement.style.top = (evt.pixel[1] - 15) + 'px';

    // Get the sketch feature being drawn
    const features = sourceDrawVector.getFeatures();
    if (features.length > 0) {
        const sketch = features[features.length - 1];
        const geometry = sketch.getGeometry();

        if (geometry.getType() === 'LineString') {
            const coordinates = geometry.getCoordinates();
            if (coordinates.length > 0) {
                lastDrawPoint = coordinates[coordinates.length - 1];
            }
        } else if (geometry.getType() === 'Point') {
            // For point drawing, there's no previous point until first click
            lastDrawPoint = null;
        }
    }

    // Calculate distance from last point to current cursor position
    let distance = 0;
    if (lastDrawPoint) {
        distance = calculateDistance(lastDrawPoint, evt.coordinate);
    }

    cursorDistanceElement.textContent = distance.toFixed(2) + ' cm';
});

// Handle click to update last point
map.on('click', function(evt) {
    if (isDrawing) {
        const drawType = drawTypeSelect.value;
        if (drawType === 'Point' || drawType === 'LineString') {
            lastDrawPoint = evt.coordinate;
        }
    }
});

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

// Function to load and display a trail on the map
function loadTrailOnMap(trailId) {
    // Clear the loaded trail layer
    sourceLoadedTrail.clear();

    if (!trailId) {
        // If no trail selected, just clear and return
        return;
    }

    // Fetch the trail data
    fetch(`/api/trails`)
        .then(response => response.json())
        .then(trails => {
            const trail = trails.find(t => t.id == trailId);
            if (!trail || !trail.trail_points) {
                console.error('Trail not found or has no points');
                return;
            }

            // Parse the trail points
            let points;
            try {
                // Replace single quotes with double quotes to make it valid JSON
                const validJson = trail.trail_points.replace(/'/g, '"');
                points = JSON.parse(validJson);
            } catch (e) {
                console.error('Error parsing trail points:', e);
                console.error('Trail points value:', trail.trail_points);
                return;
            }

            if (!Array.isArray(points) || points.length === 0) {
                console.error('Invalid trail points format');
                return;
            }

            // Convert points to map coordinates
            const coordinates = points.map(point => {
                // Points are stored as [longitude, latitude] in decimal degrees
                const lon = parseFloat(point[0]);
                const lat = parseFloat(point[1]);
                return ol.proj.fromLonLat([lon, lat]);
            });

            // Create feature based on number of points
            let feature;
            if (coordinates.length === 1) {
                // Single point
                feature = new ol.Feature({
                    geometry: new ol.geom.Point(coordinates[0])
                });
            } else {
                // Multiple points - create a LineString
                feature = new ol.Feature({
                    geometry: new ol.geom.LineString(coordinates)
                });
            }

            // Add feature to the loaded trail layer
            sourceLoadedTrail.addFeature(feature);
        })
        .catch(error => {
            console.error('Error loading trail:', error);
        });
}

// Add event listener for trail dropdown selection
trailAllDropdown.addEventListener('change', function() {
    const selectedTrailId = this.value;
    loadTrailOnMap(selectedTrailId);
});

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
                // Clear the map when trail is deleted
                sourceLoadedTrail.clear();
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

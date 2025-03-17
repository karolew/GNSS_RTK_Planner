var map = new ol.Map({
    target: 'map',
    layers: [
        new ol.layer.Tile({
            source: new ol.source.OSM()
        })
    ],
    view: new ol.View({
        center: ol.proj.fromLonLat([0, 0]),
        zoom: 2
    })
});

var marker = new ol.Feature({
    geometry: new ol.geom.Point(ol.proj.fromLonLat([0, 0]))
});

var vectorSource = new ol.source.Vector({
    features: [marker]
});

var vectorLayer = new ol.layer.Vector({
    source: vectorSource
});

map.addLayer(vectorLayer);

function formatUtcTime(timeStr) {
    if (!timeStr) return '-';
    return `${timeStr.slice(0, 2)}:${timeStr.slice(2, 4)}:${timeStr.slice(4, 6)} UTC`;
}

export function updateStatus() {
    fetch('/rover/get_coords')
        .then(response => response.json())
        .then(data => {
            // Update status panel
            document.getElementById('fix-status').textContent = data.fix_status;
            document.getElementById('fix-status').className =
                data.fix_status === 'Valid' ? 'status-valid' : 'status-invalid';

            document.getElementById('raw-coords').textContent =
                data.lat_raw && data.lon_raw ? `${data.lat_raw} / ${data.lon_raw}` : '-';

            document.getElementById('dec-coords').textContent =
                data.latitude && data.longitude ?
                    `${data.latitude.toFixed(6)}°, ${data.longitude.toFixed(6)}°` : '-';

            document.getElementById('speed').textContent =
                data.speed !== null ? `${data.speed} knots` : '-';

            document.getElementById('course').textContent =
                data.course !== null ? `${data.course}°` : '-';

            document.getElementById('gps-time').textContent =
                data.time_utc ? formatUtcTime(data.time_utc) : '-';

            document.getElementById('last-update').textContent =
                data.last_update || '-';

            // Update map marker
            if (data.latitude && data.longitude) {
                var coords = ol.proj.fromLonLat([data.longitude, data.latitude]);
                marker.getGeometry().setCoordinates(coords);
                map.getView().setCenter(coords);
            }
        });
}

// Update status given milliseconds
setInterval(updateStatus, 2000);
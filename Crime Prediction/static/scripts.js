document.querySelector('form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const location = document.getElementById('location').value;
    const time = document.getElementById('time').value;
    // Send AJAX POST to /predict
    const formData = new FormData();
    formData.append('location', location);
    formData.append('time', time);
    const response = await fetch('/predict', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();
    // Render heatmap
    renderHeatmap(data.heatmap);
    // Show summary
    document.getElementById('alerts').innerText = data.summary;
});

let heatmapLayer;
function renderHeatmap(points) {
    // Remove previous map if exists
    if (window.heatmapMap) {
        window.heatmapMap.remove();
    }
    // Create a new map in the heatmap div
    const mapDiv = document.getElementById('heatmap');
    mapDiv.innerHTML = '';
    mapDiv.style.height = '500px';
    const map = new maplibregl.Map({
        container: 'heatmap',
        style: 'https://tiles.openfreemap.org/styles/liberty',
        center: points.length ? [points[0].longitude, points[0].latitude] : [77, 20],
        zoom: points.length ? 8 : 4
    });
    window.heatmapMap = map;
    map.on('load', function() {
        if (points.length === 0) return;
        // Convert points to GeoJSON
        const features = points.map(p => ({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [p.longitude, p.latitude] },
            properties: { count: p.count, district: p.district }
        }));
        const geojson = { type: 'FeatureCollection', features };
        map.addSource('crimes', {
            type: 'geojson',
            data: geojson
        });
        map.addLayer({
            id: 'crime-heat',
            type: 'heatmap',
            source: 'crimes',
            maxzoom: 12,
            paint: {
                // Increase the heatmap weight based on frequency and crime count
                'heatmap-weight': [
                    'interpolate',
                    ['linear'],
                    ['get', 'count'],
                    0, 0,
                    50, 1
                ],
                'heatmap-intensity': 1.2,
                'heatmap-radius': 30,
                'heatmap-opacity': 0.7
            }
        });
    });
}
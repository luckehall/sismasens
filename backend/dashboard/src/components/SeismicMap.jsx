import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'

// Colore marker in base alla magnitudine
function magnitudeColor(mag) {
  if (mag >= 5.5) return '#ef4444'   // rosso — forte
  if (mag >= 4.0) return '#f97316'   // arancio — moderato
  if (mag >= 2.5) return '#eab308'   // giallo — leggero
  if (mag >= 1.0) return '#22c55e'   // verde — minore
  return '#94a3b8'                    // grigio — minimo
}

function magnitudeRadius(mag) {
  return Math.max(6, Math.min(30, mag * 5))
}

export default function SeismicMap({ events, sensors }) {
  return (
    <MapContainer
      center={[42.5, 12.5]}
      zoom={6}
      style={{ height: '100%', width: '100%', background: '#1e293b' }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />

      {/* Marker sensori attivi (senza eventi recenti) */}
      {sensors.map(s => (
        <CircleMarker
          key={s.sensor_id}
          center={[s.lat, s.lon]}
          radius={5}
          pathOptions={{ color: '#64748b', fillColor: '#334155', fillOpacity: 0.8, weight: 1 }}
        >
          <Popup>
            <strong>{s.name}</strong><br />
            {s.location}<br />
            <small>{s.sensor_id}</small>
          </Popup>
        </CircleMarker>
      ))}

      {/* Marker eventi sismici */}
      {events.filter(e => e.lat && e.lon).map((e, i) => (
        <CircleMarker
          key={`${e.sensor_id}-${e.time}-${i}`}
          center={[e.lat, e.lon]}
          radius={magnitudeRadius(e.magnitude)}
          pathOptions={{
            color: magnitudeColor(e.magnitude),
            fillColor: magnitudeColor(e.magnitude),
            fillOpacity: 0.5,
            weight: 2,
          }}
        >
          <Popup>
            <strong>M {e.magnitude?.toFixed(2)}</strong><br />
            {e.location}<br />
            SI: {e.si?.toFixed(2)} cm/s<br />
            PGA: {e.pga?.toFixed(4)} g<br />
            <small>{(() => { const d = new Date(e.time ?? e.timestamp); return isNaN(d) ? '—' : d.toLocaleString('it-IT') })()}</small><br />
            <small style={{ color: '#94a3b8' }}>{e.sensor_id}</small>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}

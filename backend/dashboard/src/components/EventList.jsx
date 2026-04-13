function magnitude_label(mag) {
  if (mag >= 5.5) return { label: 'FORTE', color: '#ef4444' }
  if (mag >= 4.0) return { label: 'MODERATO', color: '#f97316' }
  if (mag >= 2.5) return { label: 'LEGGERO', color: '#eab308' }
  if (mag >= 1.0) return { label: 'MINORE', color: '#22c55e' }
  return { label: 'MINIMO', color: '#64748b' }
}

export default function EventList({ events, connected }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid #1e293b',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span style={{
          width: 8, height: 8, borderRadius: '50%',
          background: connected ? '#22c55e' : '#ef4444',
          display: 'inline-block',
        }} />
        <span style={{ fontSize: 13, color: '#94a3b8' }}>
          {connected ? 'Live' : 'Disconnesso'}
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 13, color: '#64748b' }}>
          {events.length} eventi
        </span>
      </div>

      <div style={{ overflowY: 'auto', flex: 1 }}>
        {events.length === 0 && (
          <div style={{ padding: 24, color: '#64748b', textAlign: 'center', fontSize: 14 }}>
            Nessun evento registrato
          </div>
        )}
        {events.map((e, i) => {
          const { label, color } = magnitude_label(e.magnitude)
          const ts = new Date(e.time ?? e.timestamp)
          const isToday = ts.toDateString() === new Date().toDateString()
          const timeStr = isNaN(ts)
            ? '—'
            : isToday
              ? ts.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
              : ts.toLocaleString('it-IT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
          return (
            <div key={i} style={{
              padding: '10px 16px',
              borderBottom: '1px solid #1e293b',
              fontSize: 13,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                <span style={{ fontWeight: 600, color }}>M {e.magnitude?.toFixed(2)} — {label}</span>
                <span style={{ color: '#64748b', fontSize: 11 }}>
                  {timeStr}
                </span>
              </div>
              <div style={{ color: '#94a3b8' }}>{e.location}</div>
              <div style={{ color: '#64748b', fontSize: 11, marginTop: 2 }}>
                SI {e.si?.toFixed(2)} cm/s · PGA {e.pga?.toFixed(4)} g · {e.sensor_id}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

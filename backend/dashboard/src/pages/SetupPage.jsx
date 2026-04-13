import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, useMapEvents } from 'react-leaflet'
import { getToken, clearToken, isAuthenticated } from '../hooks/useAuth'

const API = import.meta.env.VITE_API_BASE || 'https://sismasens.iotzator.com/api'

const S = {
  page: {
    minHeight: '100vh',
    background: '#0f172a',
    color: '#e2e8f0',
    fontFamily: 'system-ui, sans-serif',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    padding: '12px 24px',
    background: '#1e293b',
    borderBottom: '1px solid #334155',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  body: {
    flex: 1,
    display: 'flex',
    gap: 32,
    padding: '32px 24px',
    maxWidth: 1100,
    margin: '0 auto',
    width: '100%',
    boxSizing: 'border-box',
  },
  card: {
    background: '#1e293b',
    borderRadius: 8,
    padding: 28,
    flex: '0 0 420px',
  },
  label: {
    display: 'block',
    fontSize: 13,
    color: '#94a3b8',
    marginBottom: 6,
    marginTop: 18,
  },
  input: {
    width: '100%',
    padding: '8px 12px',
    background: '#0f172a',
    border: '1px solid #334155',
    borderRadius: 6,
    color: '#e2e8f0',
    fontSize: 14,
    boxSizing: 'border-box',
  },
  btn: {
    marginTop: 24,
    width: '100%',
    padding: '10px 0',
    background: '#0ea5e9',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
  },
  error: {
    marginTop: 14,
    padding: '10px 14px',
    background: '#450a0a',
    border: '1px solid #ef4444',
    borderRadius: 6,
    color: '#fca5a5',
    fontSize: 13,
  },
  tokenBox: {
    marginTop: 14,
    padding: '12px 14px',
    background: '#0f172a',
    border: '1px solid #22c55e',
    borderRadius: 6,
    fontFamily: 'monospace',
    fontSize: 12,
    wordBreak: 'break-all',
    color: '#4ade80',
  },
  copyBtn: {
    marginTop: 10,
    padding: '6px 16px',
    background: '#166534',
    color: '#4ade80',
    border: '1px solid #22c55e',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: 13,
  },
  sensorRow: {
    background: '#0f172a',
    border: '1px solid #334155',
    borderRadius: 6,
    padding: '12px 14px',
    marginBottom: 8,
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  badge: (active) => ({
    fontSize: 11,
    padding: '2px 8px',
    borderRadius: 99,
    background: active ? '#14532d' : '#1e1e2e',
    color: active ? '#4ade80' : '#64748b',
    border: `1px solid ${active ? '#22c55e' : '#334155'}`,
    whiteSpace: 'nowrap',
  }),
  iconBtn: (color) => ({
    background: 'none',
    border: `1px solid ${color}`,
    color,
    borderRadius: 4,
    padding: '3px 9px',
    cursor: 'pointer',
    fontSize: 12,
    whiteSpace: 'nowrap',
  }),
}

function MapPicker({ lat, lon, onChange }) {
  function ClickHandler() {
    useMapEvents({
      click(e) {
        onChange(e.latlng.lat, e.latlng.lng)
      },
    })
    return null
  }

  return (
    <MapContainer
      center={[42.5, 12.5]}
      zoom={5}
      style={{ height: '100%', width: '100%', borderRadius: 8 }}
    >
      <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" />
      <ClickHandler />
      {lat !== null && (
        <CircleMarker
          center={[lat, lon]}
          radius={8}
          pathOptions={{ color: '#0ea5e9', fillColor: '#0ea5e9', fillOpacity: 0.8 }}
        />
      )}
    </MapContainer>
  )
}

export default function SetupPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ sensor_id: '', name: '', location: '' })
  const [lat, setLat] = useState(null)
  const [lon, setLon] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [token, setMqttToken] = useState(null)
  const [copied, setCopied] = useState(false)
  const [sensors, setSensors] = useState([])
  const [actionLoading, setActionLoading] = useState(null) // sensor_id in elaborazione

  // Redirect se non autenticato
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login')
    }
  }, [navigate])

  const loadSensors = useCallback(async () => {
    const res = await fetch(`${API}/sensors/`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (res.ok) setSensors(await res.json())
  }, [])

  useEffect(() => { loadSensors() }, [loadSensors])

  async function handleToggleActive(sensorId) {
    setActionLoading(sensorId + '_toggle')
    const res = await fetch(`${API}/sensors/${sensorId}/active`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (res.ok) await loadSensors()
    setActionLoading(null)
  }

  async function handleDelete(sensorId) {
    if (!window.confirm(`Eliminare definitivamente il sensore "${sensorId}"? L'operazione non è reversibile.`)) return
    setActionLoading(sensorId + '_delete')
    const res = await fetch(`${API}/sensors/${sensorId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (res.ok) await loadSensors()
    setActionLoading(null)
  }

  async function handleRegenToken(sensorId) {
    setActionLoading(sensorId + '_token')
    const res = await fetch(`${API}/sensors/${sensorId}/token`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (res.ok) {
      const data = await res.json()
      setMqttToken(data.mqtt_token)
      await loadSensors()
    }
    setActionLoading(null)
  }

  function set(field) {
    return e => setForm(f => ({ ...f, [field]: e.target.value }))
  }

  function logout() {
    clearToken()
    navigate('/login')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (lat === null) { setError('Clicca sulla mappa per impostare la posizione del sensore.'); return }
    setError(null)
    setLoading(true)

    const accessToken = getToken()

    try {
      // 1. Registra sensore
      const sensorRes = await fetch(`${API}/sensors/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          sensor_id: form.sensor_id,
          name: form.name,
          location: form.location,
          lat,
          lon,
        }),
      })
      if (!sensorRes.ok) {
        const d = await sensorRes.json()
        if (sensorRes.status === 401) { clearToken(); navigate('/login'); return }
        throw new Error(d.detail || 'Errore registrazione sensore')
      }

      // 2. Genera token MQTT
      const tokenRes = await fetch(`${API}/sensors/${form.sensor_id}/token`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
      })
      const tokenData = await tokenRes.json()
      if (!tokenRes.ok) throw new Error(tokenData.detail || 'Errore generazione token')

      setMqttToken(tokenData.mqtt_token)
      await loadSensors()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function copyToken() {
    navigator.clipboard.writeText(token)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={S.page}>
      <header style={S.header}>
        <span style={{ fontSize: 20 }}>🌍</span>
        <span style={{ fontWeight: 700, fontSize: 16, letterSpacing: 1 }}>SISMASENS</span>
        <span style={{ color: '#64748b', fontSize: 13 }}>Registra sensore</span>
        <Link to="/" style={{ marginLeft: 'auto', color: '#64748b', fontSize: 13, textDecoration: 'none' }}>
          ← Mappa
        </Link>
        <button onClick={logout}
          style={{ background: 'none', border: '1px solid #334155', color: '#64748b',
                   borderRadius: 4, padding: '3px 10px', cursor: 'pointer', fontSize: 12 }}>
          Esci
        </button>
      </header>

      <div style={S.body}>
        {/* Form */}
        <div style={S.card}>
          {/* Lista sensori esistenti */}
          {sensors.length > 0 && (
            <div style={{ marginBottom: 28 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
                I tuoi sensori
              </h3>
              {sensors.map(s => (
                <div key={s.sensor_id} style={S.sensorRow}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {s.name}
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                      {s.sensor_id} · {s.location}
                    </div>
                  </div>
                  <span style={S.badge(s.active)}>{s.active ? 'attivo' : 'revocato'}</span>
                  <button
                    style={S.iconBtn(s.active ? '#f97316' : '#22c55e')}
                    disabled={actionLoading === s.sensor_id + '_toggle'}
                    onClick={() => handleToggleActive(s.sensor_id)}
                    title={s.active ? 'Revoca' : 'Riattiva'}
                  >
                    {actionLoading === s.sensor_id + '_toggle' ? '...' : s.active ? 'Revoca' : 'Riattiva'}
                  </button>
                  <button
                    style={S.iconBtn('#38bdf8')}
                    disabled={actionLoading === s.sensor_id + '_token'}
                    onClick={() => handleRegenToken(s.sensor_id)}
                    title="Rigenera token MQTT"
                  >
                    {actionLoading === s.sensor_id + '_token' ? '...' : 'Token'}
                  </button>
                  <button
                    style={S.iconBtn('#ef4444')}
                    disabled={actionLoading === s.sensor_id + '_delete'}
                    onClick={() => handleDelete(s.sensor_id)}
                    title="Elimina sensore"
                  >
                    {actionLoading === s.sensor_id + '_delete' ? '...' : 'Elimina'}
                  </button>
                </div>
              ))}
              <div style={{ height: 1, background: '#334155', margin: '20px 0' }} />
            </div>
          )}

          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Nuovo sensore</h2>
          <p style={{ fontSize: 13, color: '#64748b' }}>
            Registra il sensore e ottieni il token MQTT da incollare in Home Assistant.
          </p>

          {!token ? (
            <form onSubmit={handleSubmit}>
              <label style={S.label}>Sensor ID <span style={{ color: '#64748b' }}>(es. mi-001)</span></label>
              <input style={S.input} type="text" required placeholder="mi-001"
                value={form.sensor_id} onChange={set('sensor_id')} />

              <label style={S.label}>Nome sensore</label>
              <input style={S.input} type="text" required value={form.name} onChange={set('name')} />

              <label style={S.label}>Posizione <span style={{ color: '#64748b' }}>(es. Milano, IT)</span></label>
              <input style={S.input} type="text" required value={form.location} onChange={set('location')} />

              <label style={S.label}>
                Coordinate&nbsp;
                {lat !== null
                  ? <span style={{ color: '#22c55e' }}>{lat.toFixed(5)}, {lon.toFixed(5)}</span>
                  : <span style={{ color: '#f97316' }}>clicca sulla mappa →</span>}
              </label>

              {error && <div style={S.error}>{error}</div>}

              <button
                type="submit"
                style={{ ...S.btn, ...(loading ? { background: '#334155', cursor: 'not-allowed' } : {}) }}
                disabled={loading}
              >
                {loading ? 'Registrazione in corso...' : 'Registra e ottieni token MQTT'}
              </button>
            </form>
          ) : (
            <div>
              <div style={{ marginTop: 24, color: '#22c55e', fontWeight: 600 }}>
                ✓ Sensore registrato con successo!
              </div>
              <label style={{ ...S.label, marginTop: 20 }}>Token MQTT — incolla in Home Assistant</label>
              <div style={S.tokenBox}>{token}</div>
              <button style={S.copyBtn} onClick={copyToken}>
                {copied ? '✓ Copiato!' : 'Copia token'}
              </button>
              <div style={{ marginTop: 20, fontSize: 13, color: '#64748b', lineHeight: 1.7 }}>
                <strong style={{ color: '#94a3b8' }}>Come usarlo in HA:</strong><br />
                1. Impostazioni → Dispositivi e servizi<br />
                2. SISMASENS → Configura<br />
                3. Abilita "Cloud publishing"<br />
                4. Incolla il token nel campo <em>Token MQTT</em>
              </div>
              <button style={{ ...S.btn, marginTop: 20 }} onClick={() => {
                setMqttToken(null); setForm({ sensor_id: '', name: '', location: '' })
                setLat(null); setLon(null); loadSensors()
              }}>
                Registra un altro sensore
              </button>
            </div>
          )}
        </div>

        {/* Mappa */}
        <div style={{ flex: 1, minHeight: 480, borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '8px 0 12px', fontSize: 13, color: '#64748b' }}>
            Clicca sulla mappa per impostare la posizione del sensore
          </div>
          <div style={{ height: 'calc(100% - 36px)' }}>
            <MapPicker lat={lat} lon={lon} onChange={(la, lo) => { setLat(la); setLon(lo) }} />
          </div>
        </div>
      </div>
    </div>
  )
}

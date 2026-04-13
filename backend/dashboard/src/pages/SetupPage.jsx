import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, useMapEvents } from 'react-leaflet'

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
  btnDisabled: {
    background: '#334155',
    cursor: 'not-allowed',
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
      <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
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
  const [form, setForm] = useState({
    email: '', password: '', sensor_id: '', name: '', location: '',
  })
  const [lat, setLat] = useState(null)
  const [lon, setLon] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [token, setToken] = useState(null)
  const [copied, setCopied] = useState(false)

  function set(field) {
    return e => setForm(f => ({ ...f, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (lat === null) { setError('Clicca sulla mappa per impostare la posizione del sensore.'); return }
    setError(null)
    setLoading(true)

    try {
      // 1. Registrazione account
      const regRes = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email, password: form.password }),
      })
      if (!regRes.ok) {
        const d = await regRes.json()
        throw new Error(d.detail || 'Errore registrazione account')
      }

      // 2. Login
      const loginRes = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email, password: form.password }),
      })
      const loginData = await loginRes.json()
      if (!loginRes.ok) throw new Error(loginData.detail || 'Errore login')
      const accessToken = loginData.access_token

      // 3. Registra sensore
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
        throw new Error(d.detail || 'Errore registrazione sensore')
      }

      // 4. Genera token MQTT
      const tokenRes = await fetch(`${API}/sensors/${form.sensor_id}/token`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
      })
      const tokenData = await tokenRes.json()
      if (!tokenRes.ok) throw new Error(tokenData.detail || 'Errore generazione token')

      setToken(tokenData.mqtt_token)
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
        <span style={{ color: '#64748b', fontSize: 13 }}>Registra il tuo sensore</span>
        <Link to="/" style={{ marginLeft: 'auto', color: '#64748b', fontSize: 13, textDecoration: 'none' }}>
          ← Torna alla mappa
        </Link>
      </header>

      <div style={S.body}>
        {/* Form */}
        <div style={S.card}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Nuovo sensore</h2>
          <p style={{ fontSize: 13, color: '#64748b' }}>
            Crea un account, registra il sensore e ottieni il token MQTT da incollare in Home Assistant.
          </p>

          {!token ? (
            <form onSubmit={handleSubmit}>
              <label style={S.label}>Email</label>
              <input style={S.input} type="email" required value={form.email} onChange={set('email')} />

              <label style={S.label}>Password</label>
              <input style={S.input} type="password" required minLength={8} value={form.password} onChange={set('password')} />

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
                style={{ ...S.btn, ...(loading ? S.btnDisabled : {}) }}
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
                {copied ? '✓ Copiato!' : '📋 Copia token'}
              </button>
              <div style={{ marginTop: 20, fontSize: 13, color: '#64748b', lineHeight: 1.7 }}>
                <strong style={{ color: '#94a3b8' }}>Come usarlo in HA:</strong><br />
                1. Impostazioni → Dispositivi e servizi<br />
                2. SISMASENS → Configura<br />
                3. Abilita "Cloud publishing"<br />
                4. Incolla il token nel campo <em>Token MQTT</em>
              </div>
              <Link to="/" style={{ display: 'block', marginTop: 20, color: '#38bdf8', fontSize: 13 }}>
                ← Vai alla mappa
              </Link>
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

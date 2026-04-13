import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { setToken } from '../hooks/useAuth'

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
  center: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    background: '#1e293b',
    borderRadius: 10,
    padding: 36,
    width: '100%',
    maxWidth: 400,
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
    padding: '9px 12px',
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
  totpBox: {
    marginTop: 20,
    padding: 20,
    background: '#0f172a',
    borderRadius: 8,
    border: '1px solid #334155',
    textAlign: 'center',
  },
}

export default function LoginPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [step, setStep] = useState('credentials') // 'credentials' | '2fa'
  const [tempToken, setTempToken] = useState(null)
  const [totpCode, setTotpCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function set(field) {
    return e => setForm(f => ({ ...f, [field]: e.target.value }))
  }

  async function handleCredentials(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Errore login')

      if (data.requires_2fa) {
        setTempToken(data.temp_token)
        setStep('2fa')
      } else {
        setToken(data.access_token)
        navigate('/setup')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleTotp(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/2fa/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp_token: tempToken, code: totpCode }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Codice non valido')
      setToken(data.access_token)
      navigate('/setup')
    } catch (err) {
      setError(err.message)
      setTotpCode('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={S.page}>
      <header style={S.header}>
        <span style={{ fontSize: 20 }}>🌍</span>
        <span style={{ fontWeight: 700, fontSize: 16, letterSpacing: 1 }}>SISMASENS</span>
        <Link to="/" style={{ marginLeft: 'auto', color: '#64748b', fontSize: 13, textDecoration: 'none' }}>
          ← Mappa
        </Link>
      </header>

      <div style={S.center}>
        <div style={S.card}>
          {step === 'credentials' ? (
            <>
              <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Accedi</h2>
              <p style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>
                Inserisci le tue credenziali per gestire i tuoi sensori.
              </p>

              <form onSubmit={handleCredentials}>
                <label style={S.label}>Email</label>
                <input style={S.input} type="email" required autoFocus
                  value={form.email} onChange={set('email')} />

                <label style={S.label}>Password</label>
                <input style={S.input} type="password" required
                  value={form.password} onChange={set('password')} />

                {error && <div style={S.error}>{error}</div>}

                <button type="submit" style={{ ...S.btn, ...(loading ? { background: '#334155', cursor: 'not-allowed' } : {}) }} disabled={loading}>
                  {loading ? 'Accesso in corso...' : 'Accedi'}
                </button>
              </form>

              <p style={{ marginTop: 20, fontSize: 13, color: '#64748b', textAlign: 'center' }}>
                Non hai un account?{' '}
                <Link to="/register" style={{ color: '#38bdf8', textDecoration: 'none' }}>Registrati</Link>
              </p>
            </>
          ) : (
            <div style={S.totpBox}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🔐</div>
              <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Verifica in due passaggi</h2>
              <p style={{ fontSize: 13, color: '#64748b', marginBottom: 20 }}>
                Inserisci il codice a 6 cifre dalla tua app authenticator.
              </p>
              <form onSubmit={handleTotp}>
                <input
                  style={{ ...S.input, textAlign: 'center', fontSize: 24, letterSpacing: 8, fontFamily: 'monospace' }}
                  type="text" inputMode="numeric" pattern="[0-9]{6}" maxLength={6}
                  placeholder="000000" autoFocus required
                  value={totpCode} onChange={e => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                />
                {error && <div style={S.error}>{error}</div>}
                <button type="submit" style={{ ...S.btn, ...(loading ? { background: '#334155', cursor: 'not-allowed' } : {}) }} disabled={loading}>
                  {loading ? 'Verifica...' : 'Verifica'}
                </button>
              </form>
              <button onClick={() => { setStep('credentials'); setError(null) }}
                style={{ marginTop: 12, background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 13 }}>
                ← Torna al login
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

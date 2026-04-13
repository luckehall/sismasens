import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import QRCode from 'react-qr-code'
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
    maxWidth: 440,
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
  btnSecondary: {
    marginTop: 10,
    width: '100%',
    padding: '9px 0',
    background: 'transparent',
    color: '#64748b',
    border: '1px solid #334155',
    borderRadius: 6,
    fontSize: 14,
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
  qrWrap: {
    background: '#fff',
    borderRadius: 8,
    padding: 16,
    display: 'inline-block',
    margin: '16px auto',
  },
  secret: {
    fontFamily: 'monospace',
    fontSize: 13,
    background: '#0f172a',
    border: '1px solid #334155',
    borderRadius: 6,
    padding: '8px 12px',
    wordBreak: 'break-all',
    color: '#94a3b8',
    marginTop: 10,
  },
  stepBar: {
    display: 'flex',
    gap: 8,
    marginBottom: 24,
  },
  stepDot: (active) => ({
    height: 4,
    flex: 1,
    borderRadius: 2,
    background: active ? '#0ea5e9' : '#334155',
    transition: 'background 0.3s',
  }),
}

// step: 'register' | '2fa_setup' | 'done'
export default function RegisterPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState('register')
  const [form, setForm] = useState({ email: '', password: '', confirm: '' })
  const [accessToken, setAccessToken] = useState(null)
  const [totpData, setTotpData] = useState(null) // {secret, uri}
  const [totpCode, setTotpCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function set(field) {
    return e => setForm(f => ({ ...f, [field]: e.target.value }))
  }

  // ── Step 1: registrazione account ─────────────────────────────────────────

  async function handleRegister(e) {
    e.preventDefault()
    setError(null)
    if (form.password !== form.confirm) {
      setError('Le password non coincidono')
      return
    }
    setLoading(true)
    try {
      // 1. Registra account
      const regRes = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email, password: form.password }),
      })
      if (!regRes.ok) {
        const d = await regRes.json()
        throw new Error(d.detail || 'Errore registrazione')
      }

      // 2. Login per ottenere token
      const loginRes = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.email, password: form.password }),
      })
      const loginData = await loginRes.json()
      if (!loginRes.ok) throw new Error(loginData.detail || 'Errore login')
      const token = loginData.access_token
      setAccessToken(token)

      // 3. Avvia setup 2FA
      const setupRes = await fetch(`${API}/auth/2fa/setup`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const setupData = await setupRes.json()
      if (!setupRes.ok) throw new Error(setupData.detail || 'Errore setup 2FA')

      setTotpData(setupData)
      setStep('2fa_setup')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Step 2: verifica e attiva 2FA ─────────────────────────────────────────

  async function handleEnable2FA(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/2fa/enable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ code: totpCode }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Codice non valido')

      setToken(accessToken)
      setStep('done')
    } catch (err) {
      setError(err.message)
      setTotpCode('')
    } finally {
      setLoading(false)
    }
  }

  // ── Step 3: salta 2FA ─────────────────────────────────────────────────────

  function skip2FA() {
    setToken(accessToken)
    navigate('/setup')
  }

  // ── Render ────────────────────────────────────────────────────────────────

  const stepIndex = { register: 0, '2fa_setup': 1, done: 2 }[step]

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
          {/* barra progresso */}
          <div style={S.stepBar}>
            {[0, 1, 2].map(i => (
              <div key={i} style={S.stepDot(i <= stepIndex)} />
            ))}
          </div>

          {/* ── Step 1: form registrazione ── */}
          {step === 'register' && (
            <>
              <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Crea account</h2>
              <p style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>
                Registrati per iniziare a gestire i tuoi sensori sismici.
              </p>
              <form onSubmit={handleRegister}>
                <label style={S.label}>Email</label>
                <input style={S.input} type="email" required autoFocus
                  value={form.email} onChange={set('email')} />

                <label style={S.label}>Password <span style={{ color: '#475569' }}>(min 8 caratteri)</span></label>
                <input style={S.input} type="password" required minLength={8}
                  value={form.password} onChange={set('password')} />

                <label style={S.label}>Conferma password</label>
                <input style={S.input} type="password" required minLength={8}
                  value={form.confirm} onChange={set('confirm')} />

                {error && <div style={S.error}>{error}</div>}

                <button type="submit"
                  style={{ ...S.btn, ...(loading ? { background: '#334155', cursor: 'not-allowed' } : {}) }}
                  disabled={loading}>
                  {loading ? 'Registrazione...' : 'Crea account e configura 2FA →'}
                </button>
              </form>

              <p style={{ marginTop: 20, fontSize: 13, color: '#64748b', textAlign: 'center' }}>
                Hai già un account?{' '}
                <Link to="/login" style={{ color: '#38bdf8', textDecoration: 'none' }}>Accedi</Link>
              </p>
            </>
          )}

          {/* ── Step 2: setup 2FA ── */}
          {step === '2fa_setup' && totpData && (
            <>
              <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Verifica in due passaggi</h2>
              <p style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>
                Scansiona il QR code con Google Authenticator, Authy o qualsiasi app TOTP.
              </p>

              <div style={{ textAlign: 'center' }}>
                <div style={S.qrWrap}>
                  <QRCode value={totpData.uri} size={180} />
                </div>
              </div>

              <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                Non riesci a scansionare? Inserisci questo codice manualmente nella tua app:
              </p>
              <div style={S.secret}>{totpData.secret}</div>

              <form onSubmit={handleEnable2FA} style={{ marginTop: 20 }}>
                <label style={{ ...S.label, marginTop: 0 }}>
                  Codice a 6 cifre per confermare l'attivazione
                </label>
                <input
                  style={{ ...S.input, textAlign: 'center', fontSize: 22, letterSpacing: 6, fontFamily: 'monospace' }}
                  type="text" inputMode="numeric" pattern="[0-9]{6}" maxLength={6}
                  placeholder="000000" autoFocus required
                  value={totpCode} onChange={e => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                />

                {error && <div style={S.error}>{error}</div>}

                <button type="submit"
                  style={{ ...S.btn, ...(loading ? { background: '#334155', cursor: 'not-allowed' } : {}) }}
                  disabled={loading}>
                  {loading ? 'Verifica...' : 'Attiva 2FA e continua'}
                </button>
              </form>

              <button style={S.btnSecondary} onClick={skip2FA}>
                Salta per ora (non consigliato)
              </button>
            </>
          )}

          {/* ── Step 3: fatto ── */}
          {step === 'done' && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>✓</div>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#22c55e', marginBottom: 8 }}>
                Account configurato!
              </h2>
              <p style={{ fontSize: 14, color: '#94a3b8', marginBottom: 28, lineHeight: 1.6 }}>
                Il tuo account è protetto con la verifica in due passaggi.<br />
                Ora puoi registrare il tuo primo sensore.
              </p>
              <button style={S.btn} onClick={() => navigate('/setup')}>
                Registra il tuo primo sensore →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

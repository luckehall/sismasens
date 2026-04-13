import { Routes, Route, Link } from 'react-router-dom'
import SeismicMap from './components/SeismicMap'
import EventList from './components/EventList'
import SetupPage from './pages/SetupPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import { useEvents } from './hooks/useEvents'

function MapPage() {
  const { events, sensors, connected } = useEvents()

  return (
    <div style={{
      display: 'grid',
      gridTemplateRows: 'auto 1fr',
      gridTemplateColumns: '1fr 340px',
      height: '100vh',
      background: '#0f172a',
    }}>
      <header style={{
        gridColumn: '1 / -1',
        padding: '10px 20px',
        background: '#1e293b',
        borderBottom: '1px solid #334155',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <span style={{ fontSize: 20 }}>🌍</span>
        <span style={{ fontWeight: 700, fontSize: 16, letterSpacing: 1 }}>SISMASENS</span>
        <span style={{ color: '#64748b', fontSize: 13 }}>Monitoraggio Sismico Distribuito</span>
        <Link to="/setup" style={{
          marginLeft: 'auto',
          fontSize: 12,
          color: '#38bdf8',
          textDecoration: 'none',
          padding: '4px 10px',
          border: '1px solid #38bdf8',
          borderRadius: 4,
        }}>
          + Gestisci sensori
        </Link>
        <span style={{ color: '#64748b', fontSize: 12 }}>
          {sensors.length} attivi
        </span>
      </header>

      <main style={{ position: 'relative', overflow: 'hidden' }}>
        <SeismicMap events={events} sensors={sensors} />
      </main>

      <aside style={{
        background: '#1e293b',
        borderLeft: '1px solid #334155',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #334155' }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, textTransform: 'uppercase',
                       letterSpacing: 1, color: '#94a3b8' }}>
            Ultimi eventi
          </h2>
        </div>
        <EventList events={events} connected={connected} />
      </aside>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MapPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/setup" element={<SetupPage />} />
    </Routes>
  )
}

import { useState, useEffect, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'https://sismasens.iotzator.com'
const WS_BASE  = import.meta.env.VITE_WS_BASE  || 'wss://sismasens.iotzator.com'

export function useEvents() {
  const [events, setEvents]   = useState([])
  const [sensors, setSensors] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  // Carica eventi recenti e sensori al mount
  useEffect(() => {
    fetch(`${API_BASE}/events/recent?limit=50`)
      .then(r => r.json())
      .then(setEvents)
      .catch(console.error)

    fetch(`${API_BASE}/sensors/public`)
      .then(r => r.json())
      .then(setSensors)
      .catch(console.error)
  }, [])

  // WebSocket per eventi in real-time
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${WS_BASE}/events/ws`)
      wsRef.current = ws

      ws.onopen = () => setConnected(true)
      ws.onclose = () => {
        setConnected(false)
        // Riconnessione automatica dopo 5s
        setTimeout(connect, 5000)
      }
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        if (data.type === 'ping') return
        setEvents(prev => [data, ...prev].slice(0, 100))
      }
    }
    connect()
    return () => wsRef.current?.close()
  }, [])

  return { events, sensors, connected }
}

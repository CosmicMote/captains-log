import { useState, useEffect, useCallback } from 'react'
import CalendarSidebar from './components/CalendarSidebar.jsx'
import EntryEditor from './components/EntryEditor.jsx'
import LoginScreen from './components/LoginScreen.jsx'
import { formatDate } from './utils.js'
import './App.css'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const today = formatDate(new Date())
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [selectedDate, setSelectedDate] = useState(today)
  const [entry, setEntry] = useState(null)
  const [entryDates, setEntryDates] = useState([])
  const [loading, setLoading] = useState(false)
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem('darkMode') === 'true'
  )

  const toggleDarkMode = () => {
    setDarkMode(prev => {
      localStorage.setItem('darkMode', !prev)
      return !prev
    })
  }

  const handleLogin = (newToken) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
  }, [])

  // Authenticated fetch — clears token on 401
  const authFetch = useCallback(async (path, options = {}) => {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    })
    if (res.status === 401) {
      handleLogout()
    }
    return res
  }, [token, handleLogout])

  const loadEntryDates = useCallback(async () => {
    try {
      const res = await authFetch('/entries/dates')
      if (res.ok) {
        setEntryDates(await res.json())
      }
    } catch (err) {
      console.error('Failed to load entry dates:', err)
    }
  }, [authFetch])

  const loadEntry = useCallback(async (date) => {
    setLoading(true)
    try {
      const res = await authFetch(`/entries/${date}`)
      if (res.ok) {
        setEntry(await res.json())
      } else if (res.status !== 401) {
        setEntry({ date, content: '', prev_date: null, next_date: null })
      }
    } catch (err) {
      console.error('Failed to load entry:', err)
      setEntry({ date, content: '', prev_date: null, next_date: null })
    } finally {
      setLoading(false)
    }
  }, [authFetch])

  useEffect(() => {
    if (!token) return
    loadEntryDates()
  }, [token, loadEntryDates])

  useEffect(() => {
    if (!token) return
    loadEntry(selectedDate)
  }, [token, selectedDate, loadEntry])

  const handleSave = useCallback(async (date, content) => {
    const res = await authFetch(`/entries/${date}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    })
    if (res.ok) {
      const updated = await res.json()
      setEntry(updated)
      setEntryDates(prev => {
        if (prev.includes(date)) return prev
        return [...prev, date].sort()
      })
    }
  }, [authFetch])

  const handleNavigate = useCallback((date) => {
    setSelectedDate(date)
  }, [])

  if (!token) {
    return (
      <div className={darkMode ? 'app dark' : 'app'}>
        <LoginScreen onLogin={handleLogin} />
      </div>
    )
  }

  return (
    <div className={darkMode ? 'app dark' : 'app'}>
      <header className="app-header">
        <h1>Journal</h1>
        <div className="header-actions">
          <button className="dark-toggle" onClick={toggleDarkMode}>
            {darkMode ? '☀ Light' : '☾ Dark'}
          </button>
          <button className="dark-toggle" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>
      <div className="app-body">
        <CalendarSidebar
          selectedDate={selectedDate}
          entryDates={entryDates}
          maxDate={today}
          onDateChange={setSelectedDate}
        />
        <EntryEditor
          entry={entry}
          loading={loading}
          onSave={handleSave}
          onNavigate={handleNavigate}
        />
      </div>
    </div>
  )
}

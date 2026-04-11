import { useState, useEffect, useCallback, useRef } from 'react'
import CalendarSidebar from './components/CalendarSidebar.jsx'
import EntryEditor from './components/EntryEditor.jsx'
import { formatDate } from './utils.js'
import './App.css'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const today = formatDate(new Date())
  const [selectedDate, setSelectedDate] = useState(today)
  const [entry, setEntry] = useState(null)       // null = not yet loaded
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

  const loadEntryDates = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/entries/dates`)
      if (res.ok) {
        setEntryDates(await res.json())
      }
    } catch (err) {
      console.error('Failed to load entry dates:', err)
    }
  }, [])

  const loadEntry = useCallback(async (date) => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/entries/${date}`)
      if (res.ok) {
        setEntry(await res.json())
      } else {
        setEntry({ date, content: '', prev_date: null, next_date: null })
      }
    } catch (err) {
      console.error('Failed to load entry:', err)
      setEntry({ date, content: '', prev_date: null, next_date: null })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadEntryDates()
  }, [loadEntryDates])

  useEffect(() => {
    loadEntry(selectedDate)
  }, [selectedDate, loadEntry])

  const handleSave = useCallback(async (date, content) => {
    const res = await fetch(`${API_BASE}/entries/${date}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
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
  }, [])

  const handleNavigate = useCallback((date) => {
    setSelectedDate(date)
  }, [])

  return (
    <div className={darkMode ? 'app dark' : 'app'}>
      <header className="app-header">
        <h1>Journal</h1>
        <button className="dark-toggle" onClick={toggleDarkMode}>
          {darkMode ? '☀ Light' : '☾ Dark'}
        </button>
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

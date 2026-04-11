import { useState, useEffect, useRef } from 'react'
import { toStardate } from '../utils.js'

function displayDate(dateStr) {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export default function EntryEditor({ entry, loading, onSave, onNavigate }) {
  const [content, setContent] = useState('')
  const [savedContent, setSavedContent] = useState('')
  const [saving, setSaving] = useState(false)
  const saveRef = useRef(null)

  useEffect(() => {
    if (entry !== null) {
      setContent(entry.content ?? '')
      setSavedContent(entry.content ?? '')
    }
  }, [entry])

  const hasUnsaved = content !== savedContent

  const handleSave = async () => {
    if (!hasUnsaved || saving || !entry) return
    setSaving(true)
    try {
      await onSave(entry.date, content)
      setSavedContent(content)
    } finally {
      setSaving(false)
    }
  }

  saveRef.current = handleSave

  useEffect(() => {
    const onKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault()
        saveRef.current?.()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const handleNavigate = (date) => {
    if (hasUnsaved && !window.confirm('You have unsaved changes. Leave without saving?')) return
    onNavigate(date)
  }

  if (loading || entry === null) {
    return (
      <main className="main-content">
        <div className="loading">Loading…</div>
      </main>
    )
  }

  return (
    <main className="main-content">
      <div className="entry-header">
        <button
          className="nav-btn"
          onClick={() => handleNavigate(entry.prev_date)}
          disabled={!entry.prev_date}
          title="Previous entry"
        >
          ←
        </button>
        <div className="entry-heading">
          <h2 className="entry-date">{displayDate(entry.date)}</h2>
          <p className="entry-stardate">Stardate {toStardate(entry.date)}</p>
        </div>
        <button
          className="nav-btn"
          onClick={() => handleNavigate(entry.next_date)}
          disabled={!entry.next_date}
          title="Next entry"
        >
          →
        </button>
      </div>

      <textarea
        className="entry-content"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Captain's log, supplemental…"
      />

      <div className="entry-footer">
        <span className={`status ${hasUnsaved ? 'unsaved' : 'saved'}`}>
          {hasUnsaved ? 'Unsaved changes' : 'All changes saved'}
        </span>
        <button
          className="save-btn"
          onClick={handleSave}
          disabled={!hasUnsaved || saving}
        >
          {saving ? 'Saving…' : 'Save Entry'}
        </button>
      </div>
    </main>
  )
}

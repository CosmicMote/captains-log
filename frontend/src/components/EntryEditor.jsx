import { useState, useEffect, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Placeholder from '@tiptap/extension-placeholder'
import { toStardate } from '../utils.js'

const AUTO_SAVE_INTERVAL_MS = 60_000 // 1 minute
const TICK_INTERVAL_MS      = 30_000 // refresh relative time every 30 s

function displayDate(dateStr) {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function getStatusLabel(hasUnsaved, autoSavedAt, _tick) {
  if (hasUnsaved) return { cls: 'unsaved', text: 'Unsaved changes' }
  if (autoSavedAt) {
    const mins = Math.floor((Date.now() - autoSavedAt) / 60_000)
    const text = mins < 1
      ? 'Auto-saved just now'
      : `Auto-saved ${mins} minute${mins === 1 ? '' : 's'} ago`
    return { cls: 'saved', text }
  }
  return { cls: 'saved', text: 'All changes saved' }
}

function ToolbarBtn({ onClick, isActive, title, children }) {
  return (
    <button
      type="button"
      className={`toolbar-btn${isActive ? ' is-active' : ''}`}
      onClick={onClick}
      title={title}
    >
      {children}
    </button>
  )
}

export default function EntryEditor({ entry, loading, prevEntryDate, nextEntryDate, onSave, onNavigate }) {
  const [content, setContent]       = useState('')
  const [savedContent, setSavedContent] = useState('')
  const [saving, setSaving]         = useState(false)
  const [autoSavedAt, setAutoSavedAt] = useState(null) // Date of last auto-save, null if manually saved
  const [tick, setTick]             = useState(0)      // increments to refresh relative time

  const saveRef        = useRef(null)
  const autoSaveRef    = useRef(null)
  const prevEntryDateRef = useRef(null)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Placeholder.configure({ placeholder: "Captain's log, supplemental…" }),
    ],
    content: '',
    onUpdate: ({ editor }) => {
      setContent(editor.getHTML())
    },
  })

  // When entry changes, load content into editor and reset save state.
  // Only clear autoSavedAt when navigating to a different date — not when
  // the same entry object is refreshed after a save (which also triggers
  // this effect but should preserve the auto-save timestamp).
  useEffect(() => {
    if (editor && entry !== null) {
      editor.commands.setContent(entry.content ?? '', false)
      const html = editor.getHTML()
      setContent(html)
      setSavedContent(html)
      if (entry.date !== prevEntryDateRef.current) {
        setAutoSavedAt(null)
        prevEntryDateRef.current = entry.date
      }
    }
  }, [entry, editor])

  const hasUnsaved = content !== savedContent

  // Manual save — clears the auto-save timestamp so status returns to "All changes saved"
  const handleSave = async () => {
    if (!hasUnsaved || saving || !entry || !editor) return
    setSaving(true)
    try {
      const html = editor.getHTML()
      await onSave(entry.date, html)
      setSavedContent(html)
      setAutoSavedAt(null)
    } finally {
      setSaving(false)
    }
  }

  // Keep ref current so the Ctrl+S listener never has a stale closure
  saveRef.current = handleSave

  // Auto-save function — sets the auto-save timestamp instead of clearing it
  autoSaveRef.current = async () => {
    if (!hasUnsaved || saving || !entry || !editor) return
    setSaving(true)
    try {
      const html = editor.getHTML()
      await onSave(entry.date, html)
      setSavedContent(html)
      setAutoSavedAt(new Date())
    } finally {
      setSaving(false)
    }
  }

  // Ctrl+S keyboard shortcut
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

  // Auto-save every minute
  useEffect(() => {
    const id = setInterval(() => autoSaveRef.current?.(), AUTO_SAVE_INTERVAL_MS)
    return () => clearInterval(id)
  }, [])

  // Tick every 30 s while an auto-save timestamp is active, to refresh "X minutes ago"
  useEffect(() => {
    if (!autoSavedAt) return
    const id = setInterval(() => setTick(t => t + 1), TICK_INTERVAL_MS)
    return () => clearInterval(id)
  }, [autoSavedAt])

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

  const status = getStatusLabel(hasUnsaved, autoSavedAt, tick)

  return (
    <main className="main-content">
      <div className="entry-header">
        <button
          className="nav-btn"
          onClick={() => handleNavigate(prevEntryDate)}
          disabled={!prevEntryDate}
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
          onClick={() => handleNavigate(nextEntryDate)}
          disabled={!nextEntryDate}
          title="Next entry"
        >
          →
        </button>
      </div>

      <div className="editor-wrapper">
        <div className="editor-toolbar">
          <ToolbarBtn
            onClick={() => editor.chain().focus().toggleBold().run()}
            isActive={editor?.isActive('bold')}
            title="Bold (Ctrl+B)"
          >
            <strong>B</strong>
          </ToolbarBtn>
          <ToolbarBtn
            onClick={() => editor.chain().focus().toggleItalic().run()}
            isActive={editor?.isActive('italic')}
            title="Italic (Ctrl+I)"
          >
            <em>I</em>
          </ToolbarBtn>
          <ToolbarBtn
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            isActive={editor?.isActive('underline')}
            title="Underline (Ctrl+U)"
          >
            <span style={{ textDecoration: 'underline' }}>U</span>
          </ToolbarBtn>
          <ToolbarBtn
            onClick={() => editor.chain().focus().toggleStrike().run()}
            isActive={editor?.isActive('strike')}
            title="Strikethrough"
          >
            <s>S</s>
          </ToolbarBtn>
        </div>
        <EditorContent editor={editor} className="entry-editor" />
      </div>

      <div className="entry-footer">
        <span className={`status ${status.cls}`}>
          {status.text}
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

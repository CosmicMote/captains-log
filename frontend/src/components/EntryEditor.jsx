import { useState, useEffect, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Placeholder from '@tiptap/extension-placeholder'
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
  const [content, setContent] = useState('')
  const [savedContent, setSavedContent] = useState('')
  const [saving, setSaving] = useState(false)
  const saveRef = useRef(null)

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

  // When entry changes, load content into editor and reset saved baseline
  useEffect(() => {
    if (editor && entry !== null) {
      // setContent with emitUpdate=false so onUpdate doesn't fire
      editor.commands.setContent(entry.content ?? '', false)
      const html = editor.getHTML()
      setContent(html)
      setSavedContent(html)
    }
  }, [entry, editor])

  const hasUnsaved = content !== savedContent

  const handleSave = async () => {
    if (!hasUnsaved || saving || !entry || !editor) return
    setSaving(true)
    try {
      const html = editor.getHTML()
      await onSave(entry.date, html)
      setSavedContent(html)
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

import { useState, useRef } from 'react'

const API_BASE = '/api'

export default function BackupModal({ mode, token, onClose, onImportSuccess }) {
  const [password, setPassword]     = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmed, setConfirmed]   = useState(false)
  const [selectedFile, setFile]     = useState(null)
  const [busy, setBusy]             = useState(false)
  const [error, setError]           = useState(null)
  const fileRef                     = useRef(null)

  const isExport = mode === 'export'

  const passwordsMatch = password === confirmPassword
  const canSubmit = isExport
    ? password.length > 0 && passwordsMatch
    : password.length > 0 && selectedFile !== null && confirmed

  async function handleExport() {
    setBusy(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/backup/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ password }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setError(body.detail || 'Export failed')
        return
      }
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      const date = new Date().toISOString().slice(0, 10)
      a.href     = url
      a.download = `captains-log-${date}.clog`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      onClose()
    } catch (e) {
      setError('Network error — is the backend running?')
    } finally {
      setBusy(false)
    }
  }

  async function handleImport() {
    setBusy(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', selectedFile)
      form.append('password', password)

      const res = await fetch(`${API_BASE}/backup/import`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setError(body.detail || 'Import failed')
        return
      }
      onImportSuccess()
      onClose()
    } catch (e) {
      setError('Network error — is the backend running?')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2 className="modal-title">
          {isExport ? 'Export Backup' : 'Import Backup'}
        </h2>

        {isExport ? (
          <p className="modal-desc">
            The database will be encrypted with your chosen password and downloaded
            as a <code>.clog</code> file. Keep the password safe — without it the
            backup cannot be decrypted.
          </p>
        ) : (
          <div className="modal-warning">
            <strong>⚠ Warning</strong>
            <p>
              Importing a backup will permanently replace <em>all</em> current
              journal entries with the contents of the backup file. This cannot
              be undone.
            </p>
          </div>
        )}

        {!isExport && (
          <div className="modal-field">
            <label className="modal-label">Backup file</label>
            <button
              type="button"
              className="file-btn"
              onClick={() => fileRef.current.click()}
            >
              {selectedFile ? selectedFile.name : 'Choose .clog file…'}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".clog"
              style={{ display: 'none' }}
              onChange={(e) => setFile(e.target.files[0] ?? null)}
            />
          </div>
        )}

        <div className="modal-field">
          <label className="modal-label">
            {isExport ? 'Encryption password' : 'Decryption password'}
          </label>
          <input
            type="password"
            className="modal-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && canSubmit && (isExport ? handleExport() : handleImport())}
            placeholder="Enter password…"
            autoFocus
          />
        </div>

        {isExport && (
          <div className="modal-field">
            <label className="modal-label">Confirm password</label>
            <input
              type="password"
              className={`modal-input${confirmPassword.length > 0 && !passwordsMatch ? ' input-error' : ''}`}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && canSubmit && handleExport()}
              placeholder="Re-enter password…"
            />
            {confirmPassword.length > 0 && !passwordsMatch && (
              <span className="modal-input-hint">Passwords do not match</span>
            )}
          </div>
        )}

        {!isExport && (
          <label className="modal-confirm-row">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            <span>I understand this will replace all current journal data</span>
          </label>
        )}

        {error && <p className="modal-error">{error}</p>}

        <div className="modal-actions">
          <button className="modal-btn secondary" onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button
            className={`modal-btn ${isExport ? 'primary' : 'danger'}`}
            onClick={isExport ? handleExport : handleImport}
            disabled={!canSubmit || busy}
          >
            {busy
              ? (isExport ? 'Exporting…' : 'Importing…')
              : (isExport ? 'Download Backup' : 'Restore Backup')}
          </button>
        </div>
      </div>
    </div>
  )
}

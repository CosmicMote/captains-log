import { useState, useEffect } from 'react'

const API_BASE = '/api'

const INTERVAL_OPTIONS = [
  { value: 6,   label: 'Every 6 hours' },
  { value: 12,  label: 'Every 12 hours' },
  { value: 24,  label: 'Every 24 hours' },
  { value: 48,  label: 'Every 48 hours' },
  { value: 168, label: 'Weekly' },
]

function formatLastBackup(isoString) {
  if (!isoString) return 'Never'
  const d = new Date(isoString)
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  })
}

export default function DropboxSettingsModal({ token, onClose }) {
  const [status, setStatus]         = useState(null)   // server config status
  const [loadError, setLoadError]   = useState(null)

  // Form fields
  const [appKey, setAppKey]         = useState('')
  const [appSecret, setAppSecret]   = useState('')
  const [refreshToken, setRefreshToken] = useState('')
  const [password, setPassword]     = useState('')
  const [dropboxPath, setDropboxPath] = useState("/Captain's Log Backups")
  const [intervalHours, setIntervalHours] = useState(24)

  const [saving, setSaving]         = useState(false)
  const [backingUp, setBackingUp]   = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)
  const [saveError, setSaveError]   = useState(null)
  const [saveOk, setSaveOk]         = useState(false)
  const [backupResult, setBackupResult] = useState(null) // { ok, message }

  // Load current config on mount
  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_BASE}/settings/dropbox`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) { setLoadError('Failed to load settings'); return }
        const data = await res.json()
        setStatus(data)
        if (data.configured) {
          setAppKey(data.app_key || '')
          setDropboxPath(data.dropbox_path || "/Captain's Log Backups")
          setIntervalHours(data.interval_hours || 24)
        }
      } catch {
        setLoadError('Network error loading settings')
      }
    }
    load()
  }, [token])

  const isConfigured = status?.configured === true
  const credentialsRequired = !isConfigured

  // When already configured, blank secret fields mean "keep existing"
  const canSave = appKey.trim() &&
    (isConfigured || (appSecret.trim() && refreshToken.trim() && password.trim()))

  // Returns true on success, false on failure
  async function handleSave() {
    setSaving(true)
    setSaveError(null)
    setSaveOk(false)
    try {
      const res = await fetch(`${API_BASE}/settings/dropbox`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          app_key:         appKey.trim(),
          app_secret:      appSecret.trim(),
          refresh_token:   refreshToken.trim(),
          backup_password: password.trim(),
          dropbox_path:    dropboxPath.trim() || "/Captain's Log Backups",
          interval_hours:  Number(intervalHours),
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setSaveError(body.detail || 'Save failed')
        return false
      }
      setSaveOk(true)
      const updated = await fetch(`${API_BASE}/settings/dropbox`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (updated.ok) setStatus(await updated.json())
      return true
    } catch {
      setSaveError('Network error — is the backend running?')
      return false
    } finally {
      setSaving(false)
    }
  }

  async function handleBackupNow() {
    setBackingUp(true)
    setBackupResult(null)
    try {
      const res = await fetch(`${API_BASE}/settings/dropbox/backup-now`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      const body = await res.json().catch(() => ({}))
      if (res.ok) {
        setBackupResult({ ok: true, message: `Uploaded: ${body.filename}` })
        // Refresh last-backup timestamp
        const updated = await fetch(`${API_BASE}/settings/dropbox`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (updated.ok) setStatus(await updated.json())
      } else {
        setBackupResult({ ok: false, message: body.detail || 'Backup failed' })
      }
    } catch {
      setBackupResult({ ok: false, message: 'Network error' })
    } finally {
      setBackingUp(false)
    }
  }

  async function handleDisconnect() {
    if (!window.confirm('Remove Dropbox configuration? Automatic backups will stop.')) return
    setDisconnecting(true)
    try {
      await fetch(`${API_BASE}/settings/dropbox`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      setStatus({ configured: false })
      setAppKey(''); setAppSecret(''); setRefreshToken('')
      setPassword(''); setDropboxPath("/Captain's Log Backups")
      setIntervalHours(24)
    } catch {
      // ignore
    } finally {
      setDisconnecting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-wide">
        <h2 className="modal-title">Dropbox Auto-Backup</h2>

        {loadError && <p className="modal-error">{loadError}</p>}

        {/* ── Status strip when configured ── */}
        {isConfigured && (
          <div className="dropbox-status">
            <div className="dropbox-status-row">
              <span className="dropbox-badge">✓ Connected</span>
              <span className="dropbox-last-backup">
                Last backup: {formatLastBackup(status.last_backup_at)}
                {status.last_backup_file && (
                  <span className="dropbox-filename"> ({status.last_backup_file})</span>
                )}
              </span>
            </div>
            <div className="dropbox-status-actions">
              <button
                className="modal-btn primary"
                onClick={handleBackupNow}
                disabled={backingUp}
              >
                {backingUp ? 'Uploading…' : 'Backup Now'}
              </button>
              <button
                className="modal-btn danger"
                onClick={handleDisconnect}
                disabled={disconnecting}
              >
                Disconnect
              </button>
            </div>
            {backupResult && (
              <p className={backupResult.ok ? 'modal-success' : 'modal-error'}>
                {backupResult.message}
              </p>
            )}
          </div>
        )}

        {/* ── Credentials ── */}
        <p className="modal-desc">
          {isConfigured
            ? 'Leave credential fields blank to keep existing values.'
            : 'Create a Dropbox app at developer.dropbox.com with files.content.write permission, then run setup_dropbox.py to get a refresh token.'}
        </p>

        <div className="modal-field">
          <label className="modal-label">App Key</label>
          <input className="modal-input" value={appKey}
            onChange={e => setAppKey(e.target.value)}
            placeholder="Dropbox app key" />
        </div>
        <div className="modal-field">
          <label className="modal-label">
            App Secret{isConfigured && ' (leave blank to keep existing)'}
          </label>
          <input className="modal-input" type="password" value={appSecret}
            onChange={e => setAppSecret(e.target.value)}
            placeholder={isConfigured ? '••••••••' : 'Dropbox app secret'} />
        </div>
        <div className="modal-field">
          <label className="modal-label">
            Refresh Token{isConfigured && ' (leave blank to keep existing)'}
          </label>
          <input className="modal-input" type="password" value={refreshToken}
            onChange={e => setRefreshToken(e.target.value)}
            placeholder={isConfigured ? '••••••••' : 'From setup_dropbox.py'} />
        </div>
        <div className="modal-field">
          <label className="modal-label">
            Backup Password{isConfigured && !status.has_password ? ' ⚠ not set' : ''}
            {isConfigured && status.has_password && ' (leave blank to keep existing)'}
          </label>
          <input className="modal-input" type="password" value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder={isConfigured && status.has_password ? '••••••••' : 'Encrypts each backup file'} />
        </div>

        {/* ── Schedule ── */}
        <div className="dropbox-schedule-row">
          <div className="modal-field" style={{ flex: 1 }}>
            <label className="modal-label">Dropbox Folder</label>
            <input className="modal-input" value={dropboxPath}
              onChange={e => setDropboxPath(e.target.value)}
              placeholder="/Captain's Log Backups" />
          </div>
          <div className="modal-field">
            <label className="modal-label">Frequency</label>
            <select className="modal-input modal-select"
              value={intervalHours}
              onChange={e => setIntervalHours(Number(e.target.value))}>
              {INTERVAL_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        </div>

        {saveError && <p className="modal-error">{saveError}</p>}
        {saveOk    && <p className="modal-success">Settings saved.</p>}

        <div className="modal-actions">
          <button className="modal-btn secondary" onClick={onClose}>Cancel</button>
          <button className="modal-btn secondary" onClick={handleSave}
            disabled={!canSave || saving}>
            {saving ? 'Saving…' : 'Apply'}
          </button>
          <button className="modal-btn primary" onClick={async () => { if (await handleSave()) onClose() }}
            disabled={!canSave || saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import './LoginScreen.css'

const API_BASE = '/api'

export default function LoginScreen({ onLogin }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (res.ok) {
        const { access_token } = await res.json()
        onLogin(access_token)
      } else if (res.status === 503) {
        setError('Server not configured. Run setup_password.py first.')
      } else {
        setError('Incorrect password.')
        setPassword('')
      }
    } catch {
      setError('Could not connect to server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      <div className="login-box">
        <h1>Captain's Log</h1>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            autoFocus
            disabled={loading}
          />
          {error && <p className="login-error">{error}</p>}
          <button type="submit" disabled={loading || !password}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

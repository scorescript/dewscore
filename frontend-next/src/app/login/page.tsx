'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (isRegister) {
      const { error } = await supabase.auth.signUp({ email, password })
      if (error) setError(error.message || JSON.stringify(error))
      else router.push('/dashboard')
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) setError(error.message || JSON.stringify(error))
      else router.push('/dashboard')
    }
    setLoading(false)
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a1628',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'var(--font-space-grotesk)',
    }}>
      <div style={{
        background: '#0f2040',
        border: '1px solid #1e4976',
        borderRadius: '10px',
        padding: '40px',
        width: '100%',
        maxWidth: '400px',
      }}>
        <div style={{
          fontFamily: 'var(--font-space-mono)',
          fontWeight: 700,
          fontSize: '1.4rem',
          color: '#00d4ff',
          marginBottom: '8px',
        }}>
          Dew<span style={{ color: '#e0f0ff' }}>Score</span>
        </div>
        <div style={{ fontSize: '0.8rem', color: '#7aafc8', marginBottom: '32px' }}>
          {isRegister ? 'Crea tu cuenta' : 'Inicia sesión en tu cuenta'}
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.7rem', color: '#4a7a9b', fontFamily: 'var(--font-space-mono)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px' }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                background: '#0a1628',
                border: '1px solid #1e4976',
                borderRadius: '4px',
                color: '#e0f0ff',
                fontSize: '0.85rem',
                outline: 'none',
                fontFamily: 'var(--font-space-grotesk)',
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '0.7rem', color: '#4a7a9b', fontFamily: 'var(--font-space-mono)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '6px' }}>
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                background: '#0a1628',
                border: '1px solid #1e4976',
                borderRadius: '4px',
                color: '#e0f0ff',
                fontSize: '0.85rem',
                outline: 'none',
                fontFamily: 'var(--font-space-grotesk)',
              }}
            />
          </div>

          {error && (
            <div style={{ color: '#ff6b6b', fontSize: '0.75rem', marginBottom: '16px', fontFamily: 'var(--font-space-mono)' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '11px',
              background: '#00d4ff',
              border: 'none',
              borderRadius: '4px',
              color: '#0a1628',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-space-mono)',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Cargando...' : isRegister ? 'Crear cuenta' : 'Iniciar sesión'}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '0.75rem', color: '#4a7a9b' }}>
          {isRegister ? '¿Ya tienes cuenta?' : '¿No tienes cuenta?'}{' '}
          <span
            onClick={() => { setIsRegister(!isRegister); setError('') }}
            style={{ color: '#00d4ff', cursor: 'pointer' }}
          >
            {isRegister ? 'Inicia sesión' : 'Regístrate'}
          </span>
        </div>

        <div style={{ marginTop: '32px', paddingTop: '20px', borderTop: '1px solid #1e4976', textAlign: 'center' }}>
          <a href="/" style={{ fontSize: '0.7rem', color: '#4a7a9b', textDecoration: 'none', fontFamily: 'var(--font-space-mono)' }}>
            ← Volver al mapa
          </a>
        </div>
      </div>
    </div>
  )
}
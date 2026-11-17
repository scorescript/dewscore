'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase'
import { useRouter } from 'next/navigation'

type Perfil = {
  plan: string
  created_at: string
}

export default function DashboardPage() {
  const [email, setEmail] = useState('')
  const [perfil, setPerfil] = useState<Perfil | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    async function load() {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) { router.push('/login'); return }
      setEmail(user.email || '')
      const { data } = await supabase
        .from('perfiles')
        .select('plan, created_at')
        .eq('id', user.id)
        .single()
      setPerfil(data)
      setLoading(false)
    }
    load()
  }, [])

  async function handleLogout() {
    await supabase.auth.signOut()
    router.push('/')
  }

  const planColor: Record<string, string> = {
    free: '#4a7a9b',
    pro: '#00d4ff',
    enterprise: '#f59e0b',
  }

  if (loading) return (
    <div style={{ minHeight: '100vh', background: '#0a1628', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ color: '#4a7a9b', fontFamily: 'var(--font-space-mono)', fontSize: '0.8rem' }}>Cargando...</div>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: '#0a1628', fontFamily: 'var(--font-space-grotesk)', padding: '40px 20px' }}>
      <div style={{ maxWidth: '700px', margin: '0 auto' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
          <div style={{ fontFamily: 'var(--font-space-mono)', fontWeight: 700, fontSize: '1.1rem', color: '#00d4ff' }}>
            Dew<span style={{ color: '#e0f0ff' }}>Score</span>
          </div>
          <button
            onClick={handleLogout}
            style={{ background: 'none', border: '1px solid #1e4976', borderRadius: '4px', color: '#4a7a9b', padding: '6px 14px', cursor: 'pointer', fontSize: '0.72rem', fontFamily: 'var(--font-space-mono)' }}
          >
            Cerrar sesión
          </button>
        </div>

        {/* Plan actual */}
        <div style={{ background: '#0f2040', border: '1px solid #1e4976', borderRadius: '8px', padding: '24px', marginBottom: '20px' }}>
          <div style={{ fontSize: '0.6rem', fontFamily: 'var(--font-space-mono)', color: '#4a7a9b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>
            Tu cuenta
          </div>
          <div style={{ fontSize: '0.9rem', color: '#e0f0ff', marginBottom: '16px' }}>{email}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ fontFamily: 'var(--font-space-mono)', fontWeight: 700, fontSize: '0.75rem', color: planColor[perfil?.plan || 'free'], background: `${planColor[perfil?.plan || 'free']}22`, padding: '4px 10px', borderRadius: '4px', textTransform: 'uppercase' }}>
              {perfil?.plan || 'free'}
            </div>
            {perfil?.plan === 'free' && (
              <span style={{ fontSize: '0.72rem', color: '#4a7a9b' }}>
                → <a href="/pricing" style={{ color: '#00d4ff', textDecoration: 'none' }}>Actualizar a Pro</a>
              </span>
            )}
          </div>
        </div>

        {/* Accesos rápidos */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
          <a href="/" style={{ textDecoration: 'none' }}>
            <div style={{ background: '#0f2040', border: '1px solid #1e4976', borderRadius: '8px', padding: '20px', cursor: 'pointer', transition: 'border-color 0.15s' }}>
              <div style={{ fontSize: '1.4rem', marginBottom: '8px' }}>🗺️</div>
              <div style={{ fontFamily: 'var(--font-space-mono)', fontSize: '0.75rem', color: '#00d4ff', fontWeight: 700, marginBottom: '4px' }}>DewScore</div>
              <div style={{ fontSize: '0.7rem', color: '#4a7a9b' }}>Condensación atmosférica</div>
            </div>
          </a>
          <a href="/?module=solar" style={{ textDecoration: 'none' }}>
            <div style={{ background: '#0f2040', border: '1px solid #1e4976', borderRadius: '8px', padding: '20px', cursor: 'pointer' }}>
              <div style={{ fontSize: '1.4rem', marginBottom: '8px' }}>☀️</div>
              <div style={{ fontFamily: 'var(--font-space-mono)', fontSize: '0.75rem', color: '#f59e0b', fontWeight: 700, marginBottom: '4px' }}>SolarScore</div>
              <div style={{ fontSize: '0.7rem', color: '#4a7a9b' }}>Radiación solar</div>
            </div>
          </a>
        </div>

        {/* Informes */}
        <div style={{ background: '#0f2040', border: '1px solid #1e4976', borderRadius: '8px', padding: '24px' }}>
          <div style={{ fontSize: '0.6rem', fontFamily: 'var(--font-space-mono)', color: '#4a7a9b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '16px' }}>
            Informes de feasibility
          </div>
          {perfil?.plan !== 'enterprise' ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: '0.8rem', color: '#4a7a9b', marginBottom: '12px' }}>
                Los informes PDF están disponibles en el plan Enterprise
              </div>
              <a href="/pricing" style={{ color: '#f59e0b', fontSize: '0.75rem', fontFamily: 'var(--font-space-mono)', textDecoration: 'none' }}>
                Ver planes →
              </a>
            </div>
          ) : (
            <a href="/report" style={{ textDecoration: 'none' }}>
              <button style={{ background: '#f59e0b', border: 'none', borderRadius: '4px', color: '#1a1008', fontWeight: 700, fontSize: '0.8rem', padding: '10px 20px', cursor: 'pointer', fontFamily: 'var(--font-space-mono)' }}>
                Generar nuevo informe
              </button>
            </a>
          )}
        </div>

        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <a href="/" style={{ fontSize: '0.7rem', color: '#4a7a9b', textDecoration: 'none', fontFamily: 'var(--font-space-mono)' }}>
            ← Volver al mapa
          </a>
        </div>
      </div>
    </div>
  )
}
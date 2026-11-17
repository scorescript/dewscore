'use client'

import { useRouter } from 'next/navigation'

const plans = [
  {
    name: 'Free',
    price: '0€',
    period: 'siempre gratis',
    color: '#4a7a9b',
    accent: '#7aafc8',
    features: [
      'Mapa interactivo de Canarias',
      'Temperatura y humedad (2025)',
      'Sin registro necesario',
    ],
    cta: 'Usar gratis',
    action: 'free',
  },
  {
    name: 'Pro',
    price: '199€',
    period: '/mes',
    color: '#00d4ff',
    accent: '#00d4ff',
    highlight: true,
    features: [
      'DewScore completo (CFI, DF, HHF, AWVC)',
      'SolarScore (radiación, viento)',
      'Serie histórica 2008–2025',
      'Evolución temporal por municipio',
      'Todas las islas de Canarias',
    ],
    cta: 'Empezar Pro',
    action: 'pro',
  },
  {
    name: 'Informe',
    price: '999€',
    period: 'por informe',
    color: '#f59e0b',
    accent: '#f59e0b',
    features: [
      'Todo lo de Pro',
      'Informe PDF de feasibility (50 pág.)',
      'Análisis detallado por emplazamiento',
      'Mapas, cálculos y recomendaciones',
      'Entrega en 24-48h',
    ],
    cta: 'Solicitar informe',
    action: 'report',
  },
]

export default function PricingPage() {
  const router = useRouter()

  function handleCTA(action: string) {
    if (action === 'free') router.push('/')
    else router.push('/login')
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a1628',
      fontFamily: 'var(--font-space-grotesk)',
      padding: '60px 20px',
    }}>
      <div style={{ maxWidth: '960px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '60px' }}>
          <div style={{ fontFamily: 'var(--font-space-mono)', fontWeight: 700, fontSize: '1.6rem', color: '#00d4ff', marginBottom: '12px' }}>
            Dew<span style={{ color: '#e0f0ff' }}>Score</span>
          </div>
          <div style={{ fontSize: '1rem', color: '#7aafc8', maxWidth: '500px', margin: '0 auto', lineHeight: 1.6 }}>
            Elige el plan que mejor se adapta a tu proyecto
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
          {plans.map(plan => (
            <div key={plan.name} style={{
              background: plan.highlight ? 'rgba(0,212,255,0.05)' : '#0f2040',
              border: `1px solid ${plan.highlight ? '#00d4ff' : '#1e4976'}`,
              borderRadius: '10px',
              padding: '32px 24px',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
            }}>
              {plan.highlight && (
                <div style={{
                  position: 'absolute',
                  top: '-12px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: '#00d4ff',
                  color: '#0a1628',
                  fontFamily: 'var(--font-space-mono)',
                  fontSize: '0.6rem',
                  fontWeight: 700,
                  padding: '3px 12px',
                  borderRadius: '20px',
                  letterSpacing: '0.1em',
                }}>
                  MÁS POPULAR
                </div>
              )}

              <div style={{ fontFamily: 'var(--font-space-mono)', fontWeight: 700, fontSize: '0.9rem', color: plan.accent, marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                {plan.name}
              </div>

              <div style={{ marginBottom: '24px' }}>
                <span style={{ fontSize: '2rem', fontWeight: 700, color: '#e0f0ff' }}>{plan.price}</span>
                <span style={{ fontSize: '0.8rem', color: '#4a7a9b', marginLeft: '4px' }}>{plan.period}</span>
              </div>

              <div style={{ flex: 1, marginBottom: '28px' }}>
                {plan.features.map(f => (
                  <div key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '10px', fontSize: '0.8rem', color: '#7aafc8', lineHeight: 1.5 }}>
                    <span style={{ color: plan.accent, flexShrink: 0, marginTop: '2px' }}>✓</span>
                    {f}
                  </div>
                ))}
              </div>

              <button
                onClick={() => handleCTA(plan.action)}
                style={{
                  width: '100%',
                  padding: '11px',
                  background: plan.highlight ? '#00d4ff' : 'transparent',
                  border: `1px solid ${plan.accent}`,
                  borderRadius: '4px',
                  color: plan.highlight ? '#0a1628' : plan.accent,
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-space-mono)',
                }}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>

        <div style={{ textAlign: 'center', marginTop: '40px' }}>
          <a href="/" style={{ fontSize: '0.7rem', color: '#4a7a9b', textDecoration: 'none', fontFamily: 'var(--font-space-mono)' }}>
            ← Volver al mapa
          </a>
        </div>
      </div>
    </div>
  )
}
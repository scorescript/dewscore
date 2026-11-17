'use client'

import dynamic from 'next/dynamic'

const MapApp = dynamic(() => import('@/components/MapApp'), {
  ssr: false,
  loading: () => (
    <div style={{
      height: '100vh',
      background: '#0a1628',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'monospace',
      color: '#4a7a9b',
      fontSize: '0.8rem'
    }}>
      Cargando...
    </div>
  )
})

export default function Home() {
  return <MapApp />
}
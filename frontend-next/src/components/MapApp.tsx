'use client'

import { useEffect } from 'react'
import '../app/map.css'
import { createClient } from '@/lib/supabase'

export default function MapApp() {
  useEffect(() => {
    async function loadMap() {
      if (document.getElementById('map-app-script')) return

      let plan = 'free'
      try {
        const supabase = createClient()
        const { data: { user } } = await supabase.auth.getUser()
        if (user) {
          const { data: perfil } = await supabase
            .from('perfiles')
            .select('plan')
            .eq('id', user.id)
            .single()
          if (perfil?.plan) plan = perfil.plan
        }
      } catch (e) {
        console.error('Error leyendo plan:', e)
      }

      ;(window as any).DEWSCORE_PLAN = plan

      const link1 = document.createElement('link')
      link1.rel = 'stylesheet'
      link1.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap'
      document.head.appendChild(link1)

      const link2 = document.createElement('link')
      link2.rel = 'stylesheet'
      link2.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      document.head.appendChild(link2)

      function loadScript(src: string): Promise<void> {
        return new Promise((resolve, reject) => {
          const s = document.createElement('script')
          s.src = src
          s.onload = () => resolve()
          s.onerror = reject
          document.head.appendChild(s)
        })
      }

      await loadScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js')
      await loadScript('https://unpkg.com/leaflet.vectorgrid@1.3.0/dist/Leaflet.VectorGrid.bundled.js')
      await loadScript('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js')

      const script = document.createElement('script')
      script.src = '/map-app.js'
      script.id = 'map-app-script'
      document.body.appendChild(script)
    }

    loadMap()
  }, [])

  return (
    <>
      <header>
       <div className="module-selector" id="moduleSelector">
          <button className="module-btn" onClick={() => (window as any).toggleModuleDropdown?.()}>
            <div className="dot"></div>
            <div className="mname" id="moduleLabel">Dew<span>Score</span></div>
            <span style={{color:'var(--muted)',fontSize:'0.7rem'}}>▾</span>
          </button>
          <div className="module-dropdown" id="moduleDropdown">
            <div className="module-option" onClick={() => (window as any).setModule?.('dew')}>
              <div className="opt-dot" style={{background:'#00d4ff'}}></div>
              <div><div className="opt-name" style={{color:'#00d4ff'}}>DewScore</div><div className="opt-sub" id="module-dew-sub">Atmospheric condensation</div></div>
            </div>
          </div>
        </div>

        <div className="layer-tabs" id="layerTabs"></div>

        <div className="header-right">
          <div className="region-selector">
            <select className="region-select" id="selectCA" onChange={() => (window as any).onCAChange?.()}>
              <option value="Canarias">Canarias</option>
            </select>
            <select className="region-select" id="selectIsla" onChange={() => (window as any).onIslaChange?.()}>
              <option value="todas">All islands</option>
              <option value="Gran Canaria">Gran Canaria</option>
              <option value="Tenerife">Tenerife</option>
              <option value="Lanzarote">Lanzarote</option>
              <option value="Fuerteventura">Fuerteventura</option>
              <option value="La Palma">La Palma</option>
              <option value="La Gomera">La Gomera</option>
              <option value="El Hierro">El Hierro</option>
            </select>
          </div>
          <div className="year-selector">
            <button className="year-btn" id="yearBtn" onClick={() => (window as any).toggleYearDropdown?.()}>
              <span id="yearLabel">2025</span> ▾
            </button>
            <div className="year-dropdown" id="yearDropdown"></div>
          </div>
          <button className="info-btn" onClick={() => (window as any).openAbout?.()}>ℹ Info</button>
          <select
            className="region-select"
            id="lang-selector"
            defaultValue="en"
            onChange={(e) => {
              if (typeof (window as any).setLanguage === 'function') {
                (window as any).setLanguage(e.target.value)
              }
            }}
            style={{fontFamily:'Space Mono, monospace',fontSize:'0.63rem'}}
          >
            <option value="en">EN</option>
            <option value="es">ES</option>
            <option value="fr">FR</option>
            <option value="de">DE</option>
            <option value="it">IT</option>
          </select>
        </div>
      </header>

      <div className="main">
        <div id="map">
          <div className="loading" id="mapLoading"><div className="spinner"></div><span id="loading-label">Loading...</span></div>
        </div>

        <div className="detail-col">
          <div className="detail-col-header" id="detailHeader">
            <div className="detail-col-name" id="detailName">—</div>
            <div className="detail-col-sub">AEMET · <span id="detailYear">2025</span></div>
          </div>
          <div className="detail-col-empty" id="detailEmpty">
            <div className="detail-col-empty-icon">💧</div>
            <span id="selectPromptText">Select a municipality to view its data</span>
          </div>
          <div className="detail-body" id="detailBody"></div>
          <button className="evolucion-btn" id="evolucionBtn" onClick={() => (window as any).openChart?.()}>📈 Temporal evolution</button>
        </div>

        <div className="sidebar">
          <div className="sidebar-header">
            <div className="sidebar-label" id="sidebar-ordered-label">Ordered by</div>
            <div className="sidebar-title" id="sidebarTitle">CFI</div>
          </div>
          <div className="municipio-list" id="municipioList">
            <div className="loading" style={{height:'160px'}}><div className="spinner"></div></div>
          </div>
          <div className="legend">
            <div className="legend-label" id="legendLabel">Condensation Feasibility Index</div>
            <div className="legend-gradient" id="legendGradient" style={{background:'linear-gradient(to right,#0a1628,#00d4ff)'}}></div>
            <div className="legend-labels"><span id="legendMin">0.00</span><span id="legendMax">0.25+</span></div>
          </div>
        </div>
      </div>

      <div className="chart-overlay" id="chartOverlay" onClick={(e) => (window as any).closeChart?.(e)}>
        <div className="chart-panel">
          <div className="chart-header">
            <div>
              <div className="chart-title" id="chartTitle">Temporal evolution</div>
              <div className="chart-subtitle" id="chart-subtitle-label">Historical AEMET data</div>
            </div>
            <button className="chart-close" onClick={() => (window as any).closeChart?.()}>✕</button>
          </div>
          <div className="chart-var-select" id="chartVarSelect"></div>
          <div className="chart-container"><canvas id="temporalChart"></canvas></div>
          <div className="chart-note" id="chart-note-label">● Real AEMET data · Availability varies by station</div>
        </div>
      </div>

      <div className="about-overlay" id="aboutOverlay" onClick={(e) => (window as any).closeAbout?.(e)}>
        <div className="about-panel">
          <button className="about-close" onClick={() => (window as any).closeAbout?.()}>✕</button>
          <div className="about-logo">DewScore</div>
          <div className="about-tagline" id="about-tagline">DewScore is a geospatial analysis platform for the territorial assessment of atmospheric condensation potential. It integrates observational meteorological time series with derived indices to identify locations with real viability for atmospheric water harvesting, both passive and active.</div>
          <div className="about-tagline" id="about-tagline2" style={{marginTop:'12px',fontSize:'0.8rem',color:'var(--muted2)',lineHeight:'1.65'}}>Applications include planning of atmospheric water harvesting systems, hydrological resilience studies in arid zones, applied climate research, and territorial decision-making support.</div>
          <div className="about-section">
            <div className="about-section-title" id="about-indices-title">Implemented Indices</div>
            <div className="index-block">
              <div className="index-block-title">Dew Point Temperature — T<sub>d</sub></div>
              <div className="index-block-desc" id="about-td-desc">Temperature at which an air mass reaches thermodynamic saturation. The fundamental psychrometric variable and basis for all derived indices. Computed via the August–Roche–Magnus approximation (a = 17.27, b = 237.7°C).</div>
            </div>
            <div className="index-block">
              <div className="index-block-title">CFI — Condensation Feasibility Index <span style={{color:'var(--muted2)',fontSize:'0.7rem'}}>[0–1]</span></div>
              <div className="index-block-desc" id="about-cfi-desc">Annual fraction of days in which daily minimum temperature reaches or exceeds the dew point threshold, incorporating an operational thermal margin ε = 1°C. A CFI value of 0.20 means that on 20% of days per year, conditions are suitable for active condensation.</div>
              <div className="index-use" id="about-cfi-use">Feasibility assessment of thermoelectric atmospheric water harvesting systems.</div>
            </div>
            <div className="index-block">
              <div className="index-block-title">Dew Frequency — DF <span style={{color:'var(--muted2)',fontSize:'0.7rem'}}>[0–1]</span></div>
              <div className="index-block-desc" id="about-df-desc">Fraction of days with spontaneous natural dew, defined as those in which minimum temperature equals or falls below the calculated dew point. Standard index in agrometeorology and water balance studies in arid zones.</div>
              <div className="index-use" id="about-df-use">Estimation of natural dew frequency and water balance in arid ecosystems.</div>
            </div>
            <div className="index-block">
              <div className="index-block-title">HHF — High-Humidity Frequency <span style={{color:'var(--muted2)',fontSize:'0.7rem'}}>[0–1]</span></div>
              <div className="index-block-desc" id="about-hhf-desc">Fraction of days per year in which maximum relative humidity exceeds 95%, indicative of fog or near-saturation conditions. HHF values above 0.5 are associated with high fog-harvesting frequency.</div>
              <div className="index-use" id="about-hhf-use">Site selection for fog nets and passive fog collectors.</div>
            </div>
            <div className="index-block">
              <div className="index-block-title">AWVC — Atmospheric Water Vapour Content <span style={{color:'var(--muted2)',fontSize:'0.7rem'}}>[g/m³]</span></div>
              <div className="index-block-desc" id="about-awvc-desc">Absolute density of exploitable water vapour in the air, derived from saturation vapour pressure and observed relative humidity. Expresses the condensable water mass per cubic metre of processed air.</div>
              <div className="index-use" id="about-awvc-use">Input parameter for sizing active and passive harvesting systems.</div>
            </div>
            <div className="index-block">
              <div className="index-block-title">Δ Temp–T<sub>d</sub> <span style={{color:'var(--muted2)',fontSize:'0.7rem'}}>[°C]</span></div>
              <div className="index-block-desc" id="about-delta-desc">Difference between mean annual temperature and mean annual dew point: thermal margin to saturation. The smaller it is, the closer the air is to condensing.</div>
              <div className="index-use" id="about-delta-use">First-order screening of the thermal margin a condensation system must overcome.</div>
            </div>
            <div className="index-block">
              <div className="index-block-title">Mean Temperature <span style={{color:'var(--muted2)',fontSize:'0.7rem'}}>[°C]</span></div>
              <div className="index-block-desc" id="about-temp-desc">Annual mean of the daily mean temperature recorded at the AEMET station assigned to the municipality.</div>
              <div className="index-use" id="about-temp-use">Climatic context and thermal sizing.</div>
            </div>
            <div className="index-block">
              <div className="index-block-title">Mean Relative Humidity <span style={{color:'var(--muted2)',fontSize:'0.7rem'}}>[%]</span></div>
              <div className="index-block-desc" id="about-hum-desc">Annual mean of the daily mean relative humidity at the AEMET station assigned to the municipality.</div>
              <div className="index-use" id="about-hum-use">Hygrometric context; it conditions the available water vapour.</div>
            </div>
          </div>
          <div className="about-section">
            <div className="about-section-title" id="about-sources-title">Data Sources</div>
            <div className="about-sources" id="about-sources-list">
              <div className="about-source-item"><div className="about-source-dot"></div><span><strong>AEMET OpenData</strong> — Daily climatological series (2008–2025).</span></div>
              <div className="about-source-item"><div className="about-source-dot"></div><span><strong>IGN — Instituto Geográfico Nacional</strong> — Official municipal boundaries and reference geometries.</span></div>
              <div className="about-source-item"><div className="about-source-dot"></div><span><strong>PVGIS — European Commission (JRC)</strong> — Annual solar irradiation (SARAH-2).</span></div>
              <div className="about-source-item"><div className="about-source-dot"></div><span><strong>Copernicus DEM GLO-90</strong> — Digital elevation model used to assign stations by altitude.</span></div>
              <div className="about-source-item"><div className="about-source-dot"></div><span><strong>Copernicus CDS</strong> — Climate projections (integration in progress).</span></div>
            </div>
          </div>
          <div className="about-section">
            <div className="about-section-title" id="about-who-title">About</div>
            <div className="about-who" id="about-who">DewScore is a research project developed at the Universidad de Las Palmas de Gran Canaria (SIANI — Instituto Universitario de Sistemas Inteligentes y Aplicaciones Numéricas en Ingeniería), by doctoral researcher Miguel Ferrer P.</div>
          </div>
        </div>
      </div>

      <div className="footer-bar">
        <span id="footer-copyright">© 2026 · dewscore.eu</span>
        <div className="footer-loading" id="footerLoading"><div className="footer-spinner"></div><span>Loading...</span></div>
        <a href="mailto:contacto@dewscore.eu" id="footer-contact">Contact</a>
      </div>
    </>
  )
}

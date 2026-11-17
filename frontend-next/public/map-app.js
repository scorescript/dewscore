if (!window.__dewscoreLoaded) {
window.__dewscoreLoaded = true;

const PLAN = window.DEWSCORE_PLAN || 'free';
const IS_FREE = PLAN === 'free';
const IS_PRO = PLAN === 'pro' || PLAN === 'enterprise';
const IS_ENTERPRISE = PLAN === 'enterprise';

// Free plan: only temp and humedad layers
const FREE_LAYERS_DEW = ['temp', 'humedad'];
const PRO_LAYERS_DEW = ['cfi','df','hhf','awvc','delta','temp','humedad'];
const FREE_YEARS = [2025];

function isPlanAllowed(layer) {
  if (IS_PRO) return true;
  return FREE_LAYERS_DEW.includes(layer);
}

function showUpgradeBanner(layer) {
  return IS_FREE && !FREE_LAYERS_DEW.includes(layer);
}

const API = (window.location.hostname==='localhost'||window.location.hostname==='127.0.0.1')
  ? 'http://localhost:8000/api'
  : 'https://dewscore-backend.onrender.com/api';

const lang = navigator.language.slice(0,2);

// Módulos — DewScore sin solar, SolarScore solo solar
const MODULES = {
  dew:   { layers:['cfi','df','hhf','awvc','delta','temp','humedad'], defaultLayer:'cfi' },
  solar: { layers:['solar'], defaultLayer:'solar' }
};

function getRowDefs() { return {
  cfi:    {icon:'⭐',label:'CFI',key:t.rowKeys?.cfi||'Condensation Feasibility Index [0–1]',color:'var(--accent3)',bar:'var(--accent3)',field:'cfi',fmt:v=>v.toFixed(3),desc:v=>t.descCFI(v),max:0.25},
  df:     {icon:'🌫',label:t.rowLabels?.df||'Dew Frequency',key:t.rowKeys?.df||'Dew Frequency [0–1]',color:'var(--accent)',bar:'var(--accent)',field:'dew_frequency',fmt:v=>v.toFixed(3),desc:v=>t.descDF(v),max:0.15},
  hhf:    {icon:'🌁',label:'HHF',key:t.rowKeys?.hhf||'High-Humidity Frequency [0–1]',color:'#a78bfa',bar:'#a78bfa',field:'hhf',fmt:v=>v.toFixed(3),desc:v=>t.descHHF(v),max:1},
  awvc:   {icon:'💦',label:'AWVC',key:t.rowKeys?.awvc||'Atm. Water Vapour Content (g/m³)',color:'#34d399',bar:'#34d399',field:'awvc',fmt:v=>v.toFixed(2)+' g/m³',desc:v=>t.descAWVC(v),max:15,min:5},
  delta:  {icon:'📏',label:'Δ Temp–T<sub>d</sub>',key:t.rowKeys?.delta||'Distance to saturation (°C)',color:'var(--text)',bar:null,field:'diferencia_temp_rocio',fmt:v=>v.toFixed(1)+'°C',desc:v=>t.descDelta(v)},
  temp:   {icon:'🌡',label:t.rowLabels?.temp||'Mean Temp.',key:t.rowKeys?.temp||'Annual mean temperature (°C)',color:'var(--text)',bar:null,field:'temp_media_c',fmt:v=>v.toFixed(1)+'°C',desc:v=>t.descTemp(v)},
  humedad:{icon:'💧',label:t.rowLabels?.humedad||'Rel. Humidity',key:t.rowKeys?.humedad||'Mean relative humidity (%)',color:'var(--text)',bar:null,field:'humedad_relativa_pct',fmt:v=>v.toFixed(0)+'%',desc:v=>t.descHum(v)},
  solar:  {icon:'☀️',label:t.rowLabels?.solar||'Solar Radiation',key:t.rowKeys?.solar||'Cumulative irradiation (kWh/m²/yr)',color:'#fbbf24',bar:'#fbbf24',field:'__solar',fmt:v=>v.toFixed(0)+' kWh/m²',desc:v=>t.descSolar(v),max:2200,min:1700},
};}
function getRocioRow(){return {icon:'❄️',label:t.rocioLabel||'Dew Point',key:'T<sub>d</sub> (°C)',color:'var(--accent)',bar:null,field:'punto_rocio_c',fmt:v=>v.toFixed(1)+'°C'};}

const ISLA_VIEW = {
  'todas':         {center:[28.3,-15.8],zoom:8},
  'Gran Canaria':  {center:[28.0,-15.55],zoom:10},
  'Tenerife':      {center:[28.27,-16.57],zoom:10},
  'Lanzarote':     {center:[29.03,-13.63],zoom:11},
  'Fuerteventura': {center:[28.35,-14.03],zoom:10},
  'La Palma':      {center:[28.68,-17.86],zoom:11},
  'La Gomera':     {center:[28.10,-17.23],zoom:11},
  'El Hierro':     {center:[27.74,-18.03],zoom:11},
};
const REGIONS = {
  'Canarias':{view:{center:[28.3,-15.8],zoom:8},subs:['Gran Canaria','Tenerife','Lanzarote','Fuerteventura','La Palma','La Gomera','El Hierro'],kind:'islands'},
};
function viewFor(rows){
  const la=rows.map(r=>r.lat).filter(Number.isFinite), lo=rows.map(r=>r.lng).filter(Number.isFinite);
  if(!la.length) return {center:[40.2,-3.7],zoom:6};
  const a=Math.min(...la),b=Math.max(...la),c=Math.min(...lo),d=Math.max(...lo);
  const span=Math.max((b-a)*1.3,(d-c),0.05);
  return {center:[(a+b)/2,(c+d)/2],zoom:Math.max(5,Math.min(11,Math.floor(Math.log2(900/span))))};
}
function buildRegions(data){
  const byCA={};
  for(const d of data){const m=d.municipios; if(!m||!m.comunidad||!m.isla) continue;
    ((byCA[m.comunidad]=byCA[m.comunidad]||{})[m.isla]=byCA[m.comunidad][m.isla]||[]).push(m);}
  const out={'Canarias':REGIONS['Canarias']};  // el orden alfabetico lo aplica buildCASelector
  Object.keys(byCA).filter(c=>c!=='Canarias').sort((x,y)=>x.localeCompare(y,'es')).forEach(c=>{
    const subs=Object.keys(byCA[c]).sort((x,y)=>x.localeCompare(y,'es'));
    subs.forEach(p=>{ISLA_VIEW[p]=viewFor(byCA[c][p]);});
    out[c]={view:viewFor([].concat(...subs.map(p=>byCA[c][p]))),subs,kind:'provinces'};
  });
  Object.keys(REGIONS).forEach(k=>delete REGIONS[k]); Object.assign(REGIONS,out);
}
const ALL_PROV={es:'Todas las provincias',en:'All provinces',fr:'Toutes les provinces',de:'Alle Provinzen',it:'Tutte le province'};

const T = {
  es:{
    selectPrompt:'Selecciona un municipio<br>para ver sus datos',
    descTemp:v=>v<16?`Zona fresca (${v}°C). Asociada a menor estrés calórico.`:v<20?`Temperatura templada (${v}°C).`:`Zona cálida (${v}°C).`,
    descHum:v=>v>=70?`Humedad alta (${v}%). Favorable para captación.`:v>=50?`Humedad moderada (${v}%).`:`Humedad baja (${v}%).`,
    descRocio:(v,temp)=>`T<sub>d</sub>=${v}°C. Margen hasta saturación: ${(temp-v).toFixed(1)}°C.`,
    descDelta:v=>v<=2?`${v}°C — potencial muy alto.`:v<=5?`${v}°C de margen.`:v<=10?`${v}°C. Condensación esporádica.`:`${v}°C. Baja viabilidad pasiva.`,
    descCFI:v=>{const d=Math.round(v*365);return d===0?'CFI=0. Sin días de condensación.':`CFI=${v.toFixed(3)}. ${d}/365 días T_min alcanzó saturación.`;},
    descDF:v=>{const d=Math.round(v*365);return d===0?'DF=0.':`DF=${v.toFixed(3)}. Rocío en ${d}/365 días.`;},
    descHHF:v=>{const d=Math.round(v*365);return d===0?'HHF=0.':`HHF=${v.toFixed(3)}. HRmax >95 % en ${d}/365 días.`;},
    descAWVC:v=>`AWVC=${v.toFixed(2)} g/m³.`,
    descSolar:v=>`${v.toFixed(0)} kWh/m²/año. ${v>2000?'Radiación alta.':v>1800?'Radiación moderada-alta.':'Radiación moderada.'}`,
    layerTitles:{cfi:'CFI',df:'Frecuencia de Rocío',hhf:'HHF',awvc:'AWVC',solar:'Radiación Solar',delta:'Δ Temp–T<sub>d</sub>',temp:'Temp. Media Anual',humedad:'Humedad Relativa'},
    levelHigh:'ALTO',levelMid:'MEDIO',levelLow:'BAJO',
    allIslands:'Todas las islas',moduleCondensation:'Condensación atmosférica',moduleSolar:'Radiación solar',orderedBy:'Ordenado por',historicalData:'Datos históricos AEMET',footerContact:'Contacto',evolutionTitle:'Evolución temporal',evolucionBtn:'Evolución temporal',loadingLabel:'Cargando...',chartLabelTemp:'Temp (°C)',chartLabelHum:'Humedad (%)',rocioLabel:'Punto de Rocío',rocioKey:'T<sub>d</sub> (°C)',chartNote:'● Datos reales AEMET · Disponibilidad variable según estación',deltaDesc:'Diferencia entre la temperatura media anual y el punto de rocío medio anual: margen térmico hasta la saturación. Cuanto menor es, más cerca está el aire de condensar.',deltaUse:'Cribado de primer orden del margen térmico que debe vencer un sistema de condensación.',tempDesc:'Media anual de la temperatura media diaria registrada en la estación AEMET asignada al municipio.',tempUse:'Contexto climático y dimensionado térmico.',humDesc:'Media anual de la humedad relativa media diaria en la estación AEMET asignada al municipio.',humUse:'Contexto higrométrico; condiciona la cantidad de vapor disponible.',tdDesc:'Temperatura a la que una masa de aire alcanza la saturación termodinámica. Variable psicométrica fundamental y base de cálculo para todos los índices derivados. Se calcula mediante la aproximación de August–Roche–Magnus (a = 17.67, b = 243.5°C).',cfiDesc:'Fracción temporal anual en que la temperatura mínima diaria alcanza o supera el umbral de saturación, incorporando un margen operativo ε = 1°C. Un valor de CFI = 0.20 indica que en el 20% de los días del año las condiciones son propicias para la condensación activa.',cfiUse:'Evaluación de viabilidad de sistemas termoeléctricos de captación de agua atmosférica.',dfDesc:'Fracción de días con rocío natural espontáneo, definida como aquellos en que la temperatura mínima es igual o inferior al punto de rocío calculado. Índice estándar en agrometeorología y estudios de balance hídrico en zonas áridas.',dfUse:'Estimación de frecuencia de rocío natural y balance hídrico en ecosistemas áridos.',hhfDesc:'Fracción de días al año en que la humedad relativa máxima supera el 95 %, condición compatible con niebla o casi saturación. No mide el agua captada.',hhfUse:'Indicador de cribado para ubicar captadores de niebla; requiere medición in situ.',awvcDesc:'Densidad absoluta de vapor de agua aprovechable en el aire, calculada a partir de la presión de vapor de saturación y la humedad relativa observada. Expresa la masa de agua condensable por metro cúbico de aire procesado.',awvcUse:'Parámetro de entrada para dimensionamiento de sistemas de captación activa y pasiva.',solarStatic:'Valor fijo (PVGIS) — sin variación interanual',
    rowLabels:{df:'Dew Frequency',temp:'Temp. Media',humedad:'Hum. Relativa',solar:'Solar'},
    rowKeys:{cfi:'Condensation Feasibility Index [0–1]',df:'Fracción días con rocío natural [0–1]',hhf:'High-Humidity Frequency [0–1]',awvc:'Contenido de vapor de agua (g/m³)',delta:'Distancia a saturación (°C)',temp:'Temperatura media anual (°C)',humedad:'Humedad relativa media (%)',solar:'Irradiación acumulada (kWh/m²/año)'},
    footerText:'© 2026 · dewscore.eu',
    footerContact:'Contacto',
    aboutTagline:'DewScore es una plataforma de análisis geoespacial para la evaluación territorial del potencial de condensación atmosférica. Integra series temporales de datos meteorológicos observacionales con índices derivados para identificar zonas con viabilidad real de captación de agua atmosférica, tanto pasiva como activa.',
    aboutTagline2:'Sus aplicaciones incluyen la planificación de sistemas de captación de agua atmosférica, estudios de resiliencia hídrica en zonas áridas y semiáridas, investigación climática aplicada, y apoyo a decisiones de ordenación territorial.',
    aboutIndicesTitle:'Índices implementados',aboutSourcesTitle:'Fuentes de datos',aboutWhoTitle:'Quiénes somos',
    aboutWho:'DewScore es un proyecto de investigación desarrollado en el Instituto Universitario de Sistemas Inteligentes y Aplicaciones Numéricas en Ingeniería (SIANI) de la Universidad de Las Palmas de Gran Canaria, por el doctorando Miguel Ferrer P.',
    aboutSources:['AEMET OpenData — Series climatológicas diarias (2008–2025).','IGN — Límites municipales oficiales y geometrías de referencia.','PVGIS — Comisión Europea (JRC) — Irradiación solar acumulada anual (SARAH-2).','Copernicus DEM GLO-90 — Modelo digital de elevaciones usado para asignar estaciones por altitud.','Copernicus CDS — Proyecciones climáticas (integración en curso).']
  },
  en:{
    selectPrompt:'Select a municipality<br>to view its data',
    descTemp:v=>v<16?`Cool zone (${v}°C).`:v<20?`Mild (${v}°C).`:`Warm zone (${v}°C).`,
    descHum:v=>v>=70?`High humidity (${v}%).`:v>=50?`Moderate (${v}%).`:`Low humidity (${v}%).`,
    descRocio:(v,temp)=>`T<sub>d</sub>=${v}°C. Margin: ${(temp-v).toFixed(1)}°C.`,
    descDelta:v=>v<=2?`${v}°C — very high potential.`:v<=5?`${v}°C margin.`:v<=10?`${v}°C. Sporadic condensation.`:`${v}°C. Low passive viability.`,
    descCFI:v=>{const d=Math.round(v*365);return d===0?'CFI=0.':`CFI=${v.toFixed(3)}. ${d}/365 days.`;},
    descDF:v=>{const d=Math.round(v*365);return d===0?'DF=0.':`DF=${v.toFixed(3)}. Dew ${d}/365 days.`;},
    descHHF:v=>{const d=Math.round(v*365);return d===0?'HHF=0.':`HHF=${v.toFixed(3)}. RHmax >95% on ${d}/365 days.`;},
    descAWVC:v=>`AWVC=${v.toFixed(2)} g/m³.`,
    descSolar:v=>`${v.toFixed(0)} kWh/m²/yr.`,
    layerTitles:{cfi:'CFI',df:'Dew Frequency',hhf:'HHF',awvc:'AWVC',solar:'Solar Irradiation',delta:'Δ Temp–T<sub>d</sub>',temp:'Mean Temperature',humedad:'Mean Humidity'},
    levelHigh:'HIGH',levelMid:'MED',levelLow:'LOW',
    allIslands:'All islands',moduleCondensation:'Atmospheric condensation',moduleSolar:'Solar radiation',orderedBy:'Ordered by',historicalData:'Historical AEMET data',footerContact:'Contact',evolutionTitle:'Temporal evolution',evolucionBtn:'Temporal evolution',loadingLabel:'Loading...',chartLabelTemp:'Temp (°C)',chartLabelHum:'Humidity (%)',rocioLabel:'Dew Point',rocioKey:'T<sub>d</sub> (°C)',chartNote:'● Real AEMET data · Availability varies by station',deltaDesc:'Difference between mean annual temperature and mean annual dew point: thermal margin to saturation. The smaller it is, the closer the air is to condensing.',deltaUse:'First-order screening of the thermal margin a condensation system must overcome.',tempDesc:'Annual mean of the daily mean temperature recorded at the AEMET station assigned to the municipality.',tempUse:'Climatic context and thermal sizing.',humDesc:'Annual mean of the daily mean relative humidity at the AEMET station assigned to the municipality.',humUse:'Hygrometric context; it conditions the available water vapour.',tdDesc:'Temperature at which an air mass reaches thermodynamic saturation. The fundamental psychrometric variable and basis for all derived indices. Computed via the August–Roche–Magnus approximation (a = 17.67, b = 243.5°C).',cfiDesc:'Annual fraction of days in which daily minimum temperature reaches or exceeds the dew point threshold, incorporating an operational thermal margin ε = 1°C. A CFI value of 0.20 means that on 20% of days per year, conditions are suitable for active condensation.',cfiUse:'Feasibility assessment of thermoelectric atmospheric water harvesting systems.',dfDesc:'Fraction of days with spontaneous natural dew, defined as those in which minimum temperature equals or falls below the calculated dew point. Standard index in agrometeorology and water balance studies in arid zones.',dfUse:'Estimation of natural dew frequency and water balance in arid ecosystems.',hhfDesc:'Fraction of days per year in which maximum relative humidity exceeds 95 %, a condition compatible with fog or near-saturation. It does not measure the water collected.',hhfUse:'Screening indicator for siting fog collectors; on-site measurement is required.',awvcDesc:'Absolute density of exploitable water vapour in the air, derived from saturation vapour pressure and observed relative humidity. Expresses the condensable water mass per cubic metre of processed air.',awvcUse:'Input parameter for sizing active and passive harvesting systems.',solarStatic:'Fixed value (PVGIS) — no interannual variation',
    rowLabels:{df:'Dew Frequency',temp:'Mean Temp.',humedad:'Rel. Humidity',solar:'Solar Radiation'},
    rowKeys:{cfi:'Condensation Feasibility Index [0–1]',df:'Fraction of days with natural dew [0–1]',hhf:'High-Humidity Frequency [0–1]',awvc:'Atm. Water Vapour Content (g/m³)',delta:'Distance to saturation (°C)',temp:'Annual mean temperature (°C)',humedad:'Mean relative humidity (%)',solar:'Cumulative irradiation (kWh/m²/yr)'},
    footerText:'© 2026 · dewscore.eu',
    footerContact:'Contact',
    aboutTagline:'DewScore is a geospatial analysis platform for the territorial assessment of atmospheric condensation potential. It integrates observational meteorological time series with derived indices to identify locations with real viability for atmospheric water harvesting, both passive and active.',
    aboutTagline2:'Applications include planning of atmospheric water harvesting systems, hydrological resilience studies in arid zones, applied climate research, and territorial decision-making support.',
    aboutIndicesTitle:'Implemented Indices',aboutSourcesTitle:'Data Sources',aboutWhoTitle:'About',
    aboutWho:'DewScore is a research project developed at the Universidad de Las Palmas de Gran Canaria (SIANI — Instituto Universitario de Sistemas Inteligentes y Aplicaciones Numéricas en Ingeniería), by doctoral researcher Miguel Ferrer P.',
    aboutSources:['AEMET OpenData — Daily climatological series (2008–2025).','IGN — Official municipal boundaries and reference geometries.','PVGIS — European Commission (JRC) — Annual solar irradiation (SARAH-2).','Copernicus DEM GLO-90 — Digital elevation model used to assign stations by altitude.','Copernicus CDS — Climate projections (integration in progress).']
  },
  fr:{
    selectPrompt:'Sélectionnez une commune<br>pour voir ses données',
    descTemp:v=>v<16?`Zone fraîche (${v}°C).`:v<20?`Température modérée (${v}°C).`:`Zone chaude (${v}°C).`,
    descHum:v=>v>=70?`Humidité élevée (${v}%). Favorable à la captation.`:v>=50?`Humidité modérée (${v}%).`:`Humidité faible (${v}%).`,
    descRocio:(v,temp)=>`T<sub>d</sub>=${v}°C. Marge jusqu'à saturation: ${(temp-v).toFixed(1)}°C.`,
    descDelta:v=>v<=2?`${v}°C — potentiel très élevé.`:v<=5?`${v}°C de marge.`:v<=10?`${v}°C. Condensation sporadique.`:`${v}°C. Faible viabilité passive.`,
    descCFI:v=>{const d=Math.round(v*365);return d===0?'CFI=0.':`CFI=${v.toFixed(3)}. ${d}/365 jours.`;},
    descDF:v=>{const d=Math.round(v*365);return d===0?'DF=0.':`DF=${v.toFixed(3)}. Rosée ${d}/365 jours.`;},
    descHHF:v=>{const d=Math.round(v*365);return d===0?'HHF=0.':`HHF=${v.toFixed(3)}. HRmax >95 % ${d}/365 jours.`;},
    descAWVC:v=>`AWVC=${v.toFixed(2)} g/m³.`,
    descSolar:v=>`${v.toFixed(0)} kWh/m²/an.`,
    layerTitles:{cfi:'CFI',df:'Fréquence de Rosée',hhf:'HHF',awvc:'AWVC',solar:'Rayonnement Solaire',delta:'Δ Temp–T<sub>d</sub>',temp:'Température Moyenne',humedad:'Humidité Relative'},
    levelHigh:'ÉLEVÉ',levelMid:'MOYEN',levelLow:'FAIBLE',
    allIslands:'Toutes les îles',moduleCondensation:'Condensation atmosphérique',moduleSolar:'Rayonnement solaire',orderedBy:'Classé par',historicalData:'Données historiques AEMET',footerContact:'Contact',evolutionTitle:'Évolution temporelle',evolucionBtn:'Évolution temporelle',loadingLabel:'Chargement...',chartLabelTemp:'Temp (°C)',chartLabelHum:'Humidité (%)',rocioLabel:'Point de Rosée',rocioKey:'T<sub>d</sub> (°C)',chartNote:'● Données AEMET réelles · Disponibilité variable selon la station',deltaDesc:'Différence entre la température moyenne annuelle et le point de rosée moyen annuel : marge thermique jusqu\'à la saturation. Plus elle est faible, plus l\'air est proche de la condensation.',deltaUse:'Tri de premier ordre de la marge thermique que doit franchir un système de condensation.',tempDesc:'Moyenne annuelle de la température moyenne journalière enregistrée à la station AEMET assignée à la commune.',tempUse:'Contexte climatique et dimensionnement thermique.',humDesc:'Moyenne annuelle de l\'humidité relative moyenne journalière à la station AEMET assignée à la commune.',humUse:'Contexte hygrométrique ; il conditionne la vapeur d\'eau disponible.',tdDesc:'Température à laquelle une masse d\'air atteint la saturation thermodynamique. Variable psychrométrique fondamentale et base de calcul pour tous les indices dérivés. Calculée via l\'approximation d\'August–Roche–Magnus (a = 17.67, b = 243.5°C).',cfiDesc:'Fraction annuelle de jours où la température minimale journalière atteint ou dépasse le seuil de saturation, avec une marge opérationnelle ε = 1°C. Une valeur de CFI = 0.20 signifie que 20% des jours de l\'année sont propices à la condensation active.',cfiUse:'Évaluation de viabilité des systèmes thermoélectriques de captation d\'eau atmosphérique.',dfDesc:'Fraction de jours avec rosée naturelle spontanée, définie comme ceux où la température minimale est inférieure ou égale au point de rosée calculé.',dfUse:'Estimation de la fréquence de rosée naturelle et du bilan hydrique en écosystèmes arides.',hhfDesc:'Fraction de jours par an où l\'humidité relative maximale dépasse 95 %, condition compatible avec du brouillard ou une quasi-saturation. Ne mesure pas l\'eau collectée.',hhfUse:'Indicateur de tri pour l\'implantation de collecteurs de brouillard ; une mesure sur site est nécessaire.',awvcDesc:'Densité absolue de vapeur d\'eau exploitable dans l\'air, calculée à partir de la pression de vapeur saturante et de l\'humidité relative observée.',awvcUse:'Paramètre d\'entrée pour le dimensionnement des systèmes de captation actifs et passifs.',solarStatic:'Valeur fixe (PVGIS) — pas de variation interannuelle',
    rowLabels:{df:'Fréquence de Rosée',temp:'Temp. Moyenne',humedad:'Humidité Rel.',solar:'Rayonnement Solaire'},
    rowKeys:{cfi:'Condensation Feasibility Index [0–1]',df:'Fraction de jours avec rosée naturelle [0–1]',hhf:'High-Humidity Frequency [0–1]',awvc:'Contenu en vapeur d\'eau (g/m³)',delta:'Distance à la saturation (°C)',temp:'Température moyenne annuelle (°C)',humedad:'Humidité relative moyenne (%)',solar:'Irradiation cumulée (kWh/m²/an)'},
    footerText:'© 2026 · dewscore.eu',
    footerContact:'Contact',
    aboutTagline:"DewScore est une plateforme d'analyse géospatiale pour l'évaluation territoriale du potentiel de condensation atmosphérique. Elle intègre des séries temporelles de données météorologiques avec des indices dérivés pour identifier les zones à viabilité réelle pour la collecte d\'eau atmosphérique.",
    aboutTagline2:"Les applications incluent la planification de systèmes de collecte d\'eau atmosphérique, les études de résilience hydrique en zones arides, la recherche climatique appliquée et le soutien à la décision territoriale.",
    aboutIndicesTitle:'Indices implémentés',aboutSourcesTitle:'Sources de données',aboutWhoTitle:'À propos',
    aboutWho:"DewScore est un projet de recherche développé à l'Université de Las Palmas de Gran Canaria (SIANI), par le doctorant Miguel Ferrer P.",
    aboutSources:["AEMET OpenData — Séries climatologiques journalières (2008–2025).","IGN — Limites municipaux officiels.","PVGIS — Commission Européenne (JRC) — Irradiation solaire annuelle (SARAH-2).","Copernicus DEM GLO-90 — Modèle numérique d'élévation utilisé pour affecter les stations selon l'altitude.","Copernicus CDS — Projections climatiques (intégration en cours)."]
  },
  de:{
    selectPrompt:'Gemeinde auswählen<br>um Daten anzuzeigen',
    descTemp:v=>v<16?`Kühle Zone (${v}°C).`:v<20?`Mäßige Temperatur (${v}°C).`:`Warme Zone (${v}°C).`,
    descHum:v=>v>=70?`Hohe Luftfeuchtigkeit (${v}%).`:v>=50?`Mäßige Luftfeuchtigkeit (${v}%).`:`Niedrige Luftfeuchtigkeit (${v}%).`,
    descRocio:(v,temp)=>`T<sub>d</sub>=${v}°C. Abstand zur Sättigung: ${(temp-v).toFixed(1)}°C.`,
    descDelta:v=>v<=2?`${v}°C — sehr hohes Potenzial.`:v<=5?`${v}°C Abstand.`:v<=10?`${v}°C. Sporadische Kondensation.`:`${v}°C. Geringe passive Viabilität.`,
    descCFI:v=>{const d=Math.round(v*365);return d===0?'CFI=0.':`CFI=${v.toFixed(3)}. ${d}/365 Tage.`;},
    descDF:v=>{const d=Math.round(v*365);return d===0?'DF=0.':`DF=${v.toFixed(3)}. Tau ${d}/365 Tage.`;},
    descHHF:v=>{const d=Math.round(v*365);return d===0?'HHF=0.':`HHF=${v.toFixed(3)}. RFmax >95 % an ${d}/365 Tagen.`;},
    descAWVC:v=>`AWVC=${v.toFixed(2)} g/m³.`,
    descSolar:v=>`${v.toFixed(0)} kWh/m²/Jahr.`,
    layerTitles:{cfi:'CFI',df:'Taufrequenz',hhf:'HHF',awvc:'AWVC',solar:'Solarstrahlung',delta:'Δ Temp–T<sub>d</sub>',temp:'Mittlere Temperatur',humedad:'Relative Feuchte'},
    levelHigh:'HOCH',levelMid:'MITTEL',levelLow:'NIEDRIG',
    allIslands:'Alle Inseln',moduleCondensation:'Atmosphärische Kondensation',moduleSolar:'Solarstrahlung',orderedBy:'Sortiert nach',historicalData:'Historische AEMET-Daten',footerContact:'Kontakt',evolutionTitle:'Zeitliche Entwicklung',evolucionBtn:'Zeitliche Entwicklung',loadingLabel:'Laden...',chartLabelTemp:'Temp (°C)',chartLabelHum:'Feuchte (%)',rocioLabel:'Taupunkt',rocioKey:'T<sub>d</sub> (°C)',chartNote:'● Echte AEMET-Daten · Verfügbarkeit je nach Station',deltaDesc:'Differenz zwischen mittlerer Jahrestemperatur und mittlerem Jahres-Taupunkt: thermische Reserve bis zur Sättigung. Je kleiner sie ist, desto näher ist die Luft an der Kondensation.',deltaUse:'Grobes Screening der thermischen Reserve, die ein Kondensationssystem überwinden muss.',tempDesc:'Jahresmittel der täglichen Mitteltemperatur an der der Gemeinde zugeordneten AEMET-Station.',tempUse:'Klimatischer Kontext und thermische Auslegung.',humDesc:'Jahresmittel der täglichen mittleren relativen Feuchte an der der Gemeinde zugeordneten AEMET-Station.',humUse:'Hygrometrischer Kontext; bestimmt den verfügbaren Wasserdampf.',tdDesc:'Temperatur, bei der eine Luftmasse die thermodynamische Sättigung erreicht. Grundlegende psychrometrische Variable und Berechnungsbasis für alle abgeleiteten Indizes. Berechnet über die August–Roche–Magnus-Näherung (a = 17.67, b = 243.5°C).',cfiDesc:'Jährlicher Anteil der Tage, an denen die tägliche Mindesttemperatur den Taupunktschwellenwert erreicht oder überschreitet, mit einer Betriebsmarge ε = 1°C.',cfiUse:'Machbarkeitsbewertung thermoelektrischer atmosphärischer Wassergewinnungssysteme.',dfDesc:'Anteil der Tage mit natürlichem Tau, definiert als jene, an denen die Mindesttemperatur dem berechneten Taupunkt entspricht oder darunter liegt.',dfUse:'Schätzung der natürlichen Tauhäufigkeit und des Wasserhaushalts in ariden Ökosystemen.',hhfDesc:'Anteil der Tage pro Jahr, an denen die maximale relative Feuchte 95 % übersteigt, eine mit Nebel oder Beinahe-Sättigung vereinbare Bedingung. Sie misst nicht die gesammelte Wassermenge.',hhfUse:'Screening-Indikator für die Standortwahl von Nebelsammlern; Messungen vor Ort sind erforderlich.',awvcDesc:'Absolute Dichte des nutzbaren Wasserdampfes in der Luft, abgeleitet aus dem Sättigungsdampfdruck und der beobachteten relativen Feuchte.',awvcUse:'Eingabeparameter für die Auslegung aktiver und passiver Gewinnungssysteme.',solarStatic:'Fester Wert (PVGIS) — keine interannuelle Variation',
    rowLabels:{df:'Taufrequenz',temp:'Mittl. Temp.',humedad:'Rel. Feuchte',solar:'Solarstrahlung'},
    rowKeys:{cfi:'Condensation Feasibility Index [0–1]',df:'Anteil Tautage [0–1]',hhf:'High-Humidity Frequency [0–1]',awvc:'Wasserdampfgehalt (g/m³)',delta:'Abstand zur Sättigung (°C)',temp:'Mittlere Jahrestemperatur (°C)',humedad:'Mittlere relative Feuchte (%)',solar:'Kumulierte Einstrahlung (kWh/m²/Jahr)'},
    footerText:'© 2026 · dewscore.eu',
    footerContact:'Kontakt',
    aboutTagline:'DewScore ist eine geospatiale Analyseplattform zur territorialen Bewertung des atmosphärischen Kondensationspotenzials. Sie integriert meteorologische Zeitreihendaten mit abgeleiteten Indizes, um Standorte mit realer Viabilität für die atmosphärische Wassergewinnung zu identifizieren.',
    aboutTagline2:'Anwendungen umfassen die Planung von Systemen zur atmosphärischen Wassergewinnung, hydrologische Resilienzstudien in ariden Zonen, angewandte Klimaforschung und territoriale Entscheidungsunterstützung.',
    aboutIndicesTitle:'Implementierte Indizes',aboutSourcesTitle:'Datenquellen',aboutWhoTitle:'Über uns',
    aboutWho:'DewScore ist ein Forschungsprojekt der Universität Las Palmas de Gran Canaria (SIANI), entwickelt vom Doktoranden Miguel Ferrer P.',
    aboutSources:['AEMET OpenData — Tägliche klimatologische Reihen (2008–2025).','IGN — Offizielle Gemeindegrenzen.','PVGIS — Europäische Kommission (JRC) — Jährliche Solarstrahlung (SARAH-2).','Copernicus DEM GLO-90 — Digitales Höhenmodell zur höhenbasierten Zuordnung der Stationen.','Copernicus CDS — Klimaprojektionen (Integration in Bearbeitung).']
  },
  it:{
    selectPrompt:'Seleziona un comune<br>per vedere i suoi dati',
    descTemp:v=>v<16?`Zona fresca (${v}°C).`:v<20?`Temperatura mite (${v}°C).`:`Zona calda (${v}°C).`,
    descHum:v=>v>=70?`Umidità alta (${v}%). Favorevole alla captazione.`:v>=50?`Umidità moderata (${v}%).`:`Umidità bassa (${v}%).`,
    descRocio:(v,temp)=>`T<sub>d</sub>=${v}°C. Margine fino alla saturazione: ${(temp-v).toFixed(1)}°C.`,
    descDelta:v=>v<=2?`${v}°C — potenziale molto elevato.`:v<=5?`${v}°C di margine.`:v<=10?`${v}°C. Condensazione sporadica.`:`${v}°C. Bassa viabilità passiva.`,
    descCFI:v=>{const d=Math.round(v*365);return d===0?'CFI=0.':`CFI=${v.toFixed(3)}. ${d}/365 giorni.`;},
    descDF:v=>{const d=Math.round(v*365);return d===0?'DF=0.':`DF=${v.toFixed(3)}. Rugiada ${d}/365 giorni.`;},
    descHHF:v=>{const d=Math.round(v*365);return d===0?'HHF=0.':`HHF=${v.toFixed(3)}. URmax >95 % in ${d}/365 giorni.`;},
    descAWVC:v=>`AWVC=${v.toFixed(2)} g/m³.`,
    descSolar:v=>`${v.toFixed(0)} kWh/m²/anno.`,
    layerTitles:{cfi:'CFI',df:'Frequenza di Rugiada',hhf:'HHF',awvc:'AWVC',solar:'Irradiazione Solare',delta:'Δ Temp–T<sub>d</sub>',temp:'Temperatura Media',humedad:'Umidità Relativa'},
    levelHigh:'ALTO',levelMid:'MEDIO',levelLow:'BASSO',
    allIslands:'Tutte le isole',moduleCondensation:'Condensazione atmosferica',moduleSolar:'Irradiazione solare',orderedBy:'Ordinato per',historicalData:'Dati storici AEMET',footerContact:'Contatto',evolutionTitle:'Evoluzione temporale',evolucionBtn:'Evoluzione temporale',loadingLabel:'Caricamento...',chartLabelTemp:'Temp (°C)',chartLabelHum:'Umidità (%)',rocioLabel:'Punto di Rugiada',rocioKey:'T<sub>d</sub> (°C)',chartNote:'● Dati AEMET reali · Disponibilità variabile per stazione',deltaDesc:'Differenza tra la temperatura media annuale e il punto di rugiada medio annuale: margine termico fino alla saturazione. Più è piccola, più l\'aria è vicina alla condensazione.',deltaUse:'Screening di primo ordine del margine termico che un sistema di condensazione deve superare.',tempDesc:'Media annuale della temperatura media giornaliera registrata nella stazione AEMET assegnata al comune.',tempUse:'Contesto climatico e dimensionamento termico.',humDesc:'Media annuale dell\'umidità relativa media giornaliera nella stazione AEMET assegnata al comune.',humUse:'Contesto igrometrico; condiziona il vapore acqueo disponibile.',tdDesc:'Temperatura alla quale una massa d\'aria raggiunge la saturazione termodinamica. Variabile psicrometrica fondamentale e base di calcolo per tutti gli indici derivati. Calcolata tramite l\'approssimazione di August–Roche–Magnus (a = 17.67, b = 243.5°C).',cfiDesc:'Frazione annuale di giorni in cui la temperatura minima giornaliera raggiunge o supera la soglia del punto di rugiada, con un margine operativo ε = 1°C.',cfiUse:'Valutazione di fattibilità dei sistemi termoelettrici di raccolta dell\'acqua atmosferica.',dfDesc:'Frazione di giorni con rugiada naturale spontanea, definita come quelli in cui la temperatura minima è uguale o inferiore al punto di rugiada calcolato.',dfUse:'Stima della frequenza della rugiada naturale e del bilancio idrico negli ecosistemi aridi.',hhfDesc:'Frazione di giorni all\'anno in cui l\'umidità relativa massima supera il 95 %, condizione compatibile con nebbia o quasi saturazione. Non misura l\'acqua raccolta.',hhfUse:'Indicatore di screening per la scelta dei siti dei collettori di nebbia; è necessaria una misura in loco.',awvcDesc:'Densità assoluta di vapore acqueo sfruttabile nell\'aria, derivata dalla pressione di vapore saturo e dall\'umidità relativa osservata.',awvcUse:'Parametro di ingresso per il dimensionamento di sistemi di raccolta attivi e passivi.',solarStatic:'Valore fisso (PVGIS) — nessuna variazione interannuale',
    rowLabels:{df:'Frequenza Rugiada',temp:'Temp. Media',humedad:'Umidità Rel.',solar:'Irradiazione Solare'},
    rowKeys:{cfi:'Condensation Feasibility Index [0–1]',df:'Frazione giorni con rugiada [0–1]',hhf:'High-Humidity Frequency [0–1]',awvc:'Contenuto di vapore acqueo (g/m³)',delta:'Distanza alla saturazione (°C)',temp:'Temperatura media annuale (°C)',humedad:'Umidità relativa media (%)',solar:'Irradiazione cumulata (kWh/m²/anno)'},
    footerText:'© 2026 · dewscore.eu',
    footerContact:'Contatto',
    aboutTagline:"DewScore è una piattaforma di analisi geospaziale per la valutazione territoriale del potenziale di condensazione atmosferica. Integra serie temporali di dati meteorologici osservazionali con indici derivati per identificare zone con reale viabilità per la raccolta di acqua atmosferica.",
    aboutTagline2:"Le applicazioni includono la pianificazione di sistemi di raccolta di acqua atmosferica, studi di resilienza idrica in zone aride, ricerca climatica applicata e supporto alle decisioni territoriali.",
    aboutIndicesTitle:'Indici implementati',aboutSourcesTitle:'Fonti dei dati',aboutWhoTitle:'Chi siamo',
    aboutWho:"DewScore è un progetto di ricerca sviluppato presso l'Università di Las Palmas de Gran Canaria (SIANI), dal dottorando Miguel Ferrer P.",
    aboutSources:["AEMET OpenData — Serie climatologiche giornaliere (2008–2025).","IGN — Confini comunali ufficiali.","PVGIS — Commissione Europea (JRC) — Irradiazione solare annuale (SARAH-2).","Copernicus DEM GLO-90 — Modello digitale di elevazione usato per assegnare le stazioni per quota.","Copernicus CDS — Proiezioni climatiche (integrazione in corso)."]
  }
};

let currentLang = (typeof localStorage !== 'undefined' && localStorage.getItem('dewscore_lang')) || 'en';
let t = T[currentLang] || T.en;

function setLanguage(l) {
  currentLang = l;
  if (typeof localStorage !== 'undefined') localStorage.setItem('dewscore_lang', l);
  t = T[l] || T.en;
  document.getElementById('selectPromptText').innerHTML = t.selectPrompt;
  buildLayerTabs();
  updateLayerUI();
  if (selectedNombre) { const d = getDatos(selectedNombre); if(d) buildDetailPanel(d, selectedNombre); }
  renderList();
  updateAbout();
  buildIslaSelector();
  buildModuleDropdown();
  updateAbout();
  document.querySelectorAll('.lang-btn').forEach(b => {
    b.style.color = b.dataset.lang === l ? 'var(--accent)' : 'var(--muted2)';
    b.style.borderColor = b.dataset.lang === l ? 'var(--accent)' : 'var(--border)';
  });
}

function updateAbout() {
  const el = id => document.getElementById(id);
  if (!el('about-tagline')) return;
  el('about-tagline').textContent = t.aboutTagline;
  el('about-tagline2').textContent = t.aboutTagline2;
  el('about-indices-title').textContent = t.aboutIndicesTitle;
  el('about-sources-title').textContent = t.aboutSourcesTitle;
  el('about-who-title').textContent = t.aboutWhoTitle;
  el('about-who').innerHTML = t.aboutWho;
  const srcEl = el('about-sources-list');
  if (srcEl) srcEl.innerHTML = t.aboutSources.map(s => '<div class="about-source-item"><div class="about-source-dot"></div><span>'+s+'</span></div>').join('');
  // Update index blocks
  const ids = {
    'about-td-desc': t.tdDesc,
    'about-cfi-desc': t.cfiDesc,
    'about-cfi-use': t.cfiUse,
    'about-df-desc': t.dfDesc,
    'about-df-use': t.dfUse,
    'about-hhf-desc': t.hhfDesc,
    'about-hhf-use': t.hhfUse,
    'about-awvc-desc': t.awvcDesc,
    'about-awvc-use': t.awvcUse,
    'about-delta-desc': t.deltaDesc,
    'about-delta-use': t.deltaUse,
    'about-temp-desc': t.tempDesc,
    'about-temp-use': t.tempUse,
    'about-hum-desc': t.humDesc,
    'about-hum-use': t.humUse,
  };
  Object.entries(ids).forEach(([id, txt]) => {
    try {
      const el2 = document.getElementById(id);
      if (el2 && txt) el2.textContent = txt;
    } catch(e) {}
  });
  // Update evolucion button
  const evBtn = document.getElementById('evolucionBtn');
  if (evBtn) evBtn.innerHTML = '📈 ' + (t.evolucionBtn || 'Temporal evolution');
  // Update loading label
  const loadLabel = document.getElementById('loading-label');
  if (loadLabel) loadLabel.textContent = t.loadingLabel || 'Loading...';
  // Update chart note
  const chartNote = document.getElementById('chart-note-label');
  if (chartNote) chartNote.textContent = t.chartNote || '● Real AEMET data · Availability varies by station';
  // Update footer
  const footer = el('footer-copyright');
  if (footer) footer.textContent = t.footerText || '© 2026 · dewscore.eu';
  const contact = el('footer-contact');
  if (contact) contact.textContent = t.footerContact || 'Contact';
}

document.getElementById('selectPromptText').innerHTML = t.selectPrompt;

const AVAILABLE_YEARS=[2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025];
let currentYear=2025,currentModule='dew',currentLayer='cfi',currentIsla='Gran Canaria',currentCA='Canarias';
let atmosferaData=[],tileLayer=null,selectedNombre=null,selectedMunicipioId=null,map=null;
let chartInstance=null,currentChartVar='cfi',serieData=[];

function getCHART_VARS_DEW(){return [
  {key:'temp_media_c',label:t.chartLabelTemp||'Temp (°C)',color:'#ff6b6b',yLabel:'°C'},
  {key:'punto_rocio_c',label:'T<sub>d</sub> (°C)',color:'#00d4ff',yLabel:'°C'},
  {key:'diferencia_temp_rocio',label:'Δ Temp–T<sub>d</sub>',color:'#fbbf24',yLabel:'°C'},
  {key:'humedad_relativa_pct',label:t.chartLabelHum||'Humidity (%)',color:'#60a5fa',yLabel:'%'},
  {key:'cfi',label:'CFI',color:'#69ff47',yLabel:'index'},
  {key:'dew_frequency',label:'DF',color:'#00d4ff',yLabel:'index'},
  {key:'hhf',label:'HHF',color:'#a78bfa',yLabel:'index'},
  {key:'awvc',label:'AWVC (g/m³)',color:'#34d399',yLabel:'g/m³'},
];}  

const CHART_VARS_SOLAR=[
  {key:'radiacion_solar_kwh',label:t.layerTitles?.solar||'Solar Irradiation (kWh/m²)',color:'#f59e0b',yLabel:'kWh/m²'},
];

function getChartVars(){return currentModule==='solar'?CHART_VARS_SOLAR:getCHART_VARS_DEW();}

const DEW_LAYERS={
  cfi:{getValue:d=>d.cfi??0,format:v=>v.toFixed(3),color:v=>interp('#0a1628','#00d4ff',Math.min(v/0.25,1)),minLabel:'0.00',maxLabel:'0.25+',gradient:'linear-gradient(to right,#0a1628,#00d4ff)',legendLabel:'Condensation Feasibility Index',rev:false,badge:(v,t)=>v>=0.15?{tx:t.levelHigh,bg:'rgba(105,255,71,0.15)',c:'#69ff47'}:v>=0.03?{tx:t.levelMid,bg:'rgba(0,212,255,0.15)',c:'#00d4ff'}:{tx:t.levelLow,bg:'rgba(255,107,107,0.15)',c:'#ff6b6b'}},
  df:{getValue:d=>d.dew_frequency??0,format:v=>v.toFixed(3),color:v=>interp('#0a1628','#00d4ff',Math.min(v/0.15,1)),minLabel:'0.00',maxLabel:'0.15+',gradient:'linear-gradient(to right,#0a1628,#00d4ff)',legendLabel:'Dew Frequency',rev:false,badge:(v,t)=>v>=0.10?{tx:t.levelHigh,bg:'rgba(105,255,71,0.15)',c:'#69ff47'}:v>=0.03?{tx:t.levelMid,bg:'rgba(0,212,255,0.15)',c:'#00d4ff'}:{tx:t.levelLow,bg:'rgba(255,107,107,0.15)',c:'#ff6b6b'}},
  hhf:{getValue:d=>d.hhf??0,format:v=>v.toFixed(3),color:v=>interp('#0a1628','#a78bfa',Math.min(v/0.9,1)),minLabel:'0.00',maxLabel:'1.00',gradient:'linear-gradient(to right,#0a1628,#a78bfa)',legendLabel:'High-Humidity Frequency',rev:false,badge:(v,t)=>v>=0.5?{tx:t.levelHigh,bg:'rgba(105,255,71,0.15)',c:'#69ff47'}:v>=0.1?{tx:t.levelMid,bg:'rgba(0,212,255,0.15)',c:'#00d4ff'}:{tx:t.levelLow,bg:'rgba(255,107,107,0.15)',c:'#ff6b6b'}},
  awvc:{getValue:d=>d.awvc??0,format:v=>v.toFixed(1)+' g/m³',color:v=>interp('#0a1628','#34d399',Math.min((v-5)/10,1)),minLabel:'5 g/m³',maxLabel:'15 g/m³',gradient:'linear-gradient(to right,#0a1628,#34d399)',legendLabel:'Atm. Water Vapour Content',rev:false,badge:(v,t)=>v>=12?{tx:t.levelHigh,bg:'rgba(105,255,71,0.15)',c:'#69ff47'}:v>=9?{tx:t.levelMid,bg:'rgba(0,212,255,0.15)',c:'#00d4ff'}:{tx:t.levelLow,bg:'rgba(255,107,107,0.15)',c:'#ff6b6b'}},
  delta:{getValue:d=>d.diferencia_temp_rocio??0,format:v=>v.toFixed(1)+'°C',color:v=>interp('#00d4ff','#ff6b6b',Math.min((v-2)/12,1)),minLabel:'2°C',maxLabel:'14°C+',gradient:'linear-gradient(to right,#00d4ff,#ff6b6b)',legendLabel:'Δ Temp–T<sub>d</sub>',rev:true,badge:(v,t)=>v<=4?{tx:t.levelHigh,bg:'rgba(105,255,71,0.15)',c:'#69ff47'}:v<=8?{tx:t.levelMid,bg:'rgba(0,212,255,0.15)',c:'#00d4ff'}:{tx:t.levelLow,bg:'rgba(255,107,107,0.15)',c:'#ff6b6b'}},
  temp:{getValue:d=>d.temp_media_c??0,format:v=>v.toFixed(1)+'°C',color:v=>interp('#00d4ff','#ff6b6b',Math.min((v-11)/11,1)),minLabel:'11°C',maxLabel:'22°C',gradient:'linear-gradient(to right,#00d4ff,#ff6b6b)',legendLabel:'Temperatura media anual',rev:true,badge:(v,t)=>v<=15?{tx:t.levelHigh,bg:'rgba(105,255,71,0.15)',c:'#69ff47'}:v<=19?{tx:t.levelMid,bg:'rgba(0,212,255,0.15)',c:'#00d4ff'}:{tx:t.levelLow,bg:'rgba(255,107,107,0.15)',c:'#ff6b6b'}},
  humedad:{getValue:d=>d.humedad_relativa_pct??0,format:v=>v.toFixed(0)+'%',color:v=>interp('#ff6b6b','#00d4ff',Math.min((v-40)/45,1)),minLabel:'40%',maxLabel:'85%',gradient:'linear-gradient(to right,#ff6b6b,#00d4ff)',legendLabel:t.rowLabels?.humedad||'Rel. Humidity',rev:false,badge:(v,t)=>v>=75?{tx:t.levelHigh,bg:'rgba(105,255,71,0.15)',c:'#69ff47'}:v>=60?{tx:t.levelMid,bg:'rgba(0,212,255,0.15)',c:'#00d4ff'}:{tx:t.levelLow,bg:'rgba(255,107,107,0.15)',c:'#ff6b6b'}},
};

const SOLAR_LAYERS={
  solar:{getValue:d=>d.municipios?.radiacion_solar_kwh??0,format:v=>v.toFixed(0)+' kWh/m²',color:v=>interp('#1a1008','#f59e0b',Math.min((v-1700)/500,1)),minLabel:'1700',maxLabel:'2200+',gradient:'linear-gradient(to right,#1a1008,#f59e0b)',legendLabel:'Radiación solar acumulada (kWh/m²/año)',rev:false,badge:(v,t)=>v>=2100?{tx:t.levelHigh,bg:'rgba(245,158,11,0.2)',c:'#f59e0b'}:v>=1900?{tx:t.levelMid,bg:'rgba(239,68,68,0.15)',c:'#ef4444'}:{tx:t.levelLow,bg:'rgba(120,53,15,0.3)',c:'#92400e'}},
};

function getLAYERS(){return currentModule==='solar'?SOLAR_LAYERS:DEW_LAYERS;}
function hexToRgb(h){return[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}
function interp(c1,c2,t){const[r1,g1,b1]=hexToRgb(c1);const[r2,g2,b2]=hexToRgb(c2);return`rgb(${Math.round(r1+(r2-r1)*t)},${Math.round(g1+(g2-g1)*t)},${Math.round(b1+(b2-b1)*t)})`;}

function getDatos(nombre){
  if(!nombre)return null;
  const n=nombre.toLowerCase().trim();
  let m=atmosferaData.find(d=>(d.municipios?.nombre||'').toLowerCase().trim()===n);
  if(m)return m;
  m=atmosferaData.find(d=>(d.municipios?.nombre||'').toLowerCase().trim().startsWith(n));
  if(m)return m;
  return atmosferaData.find(d=>{const x=(d.municipios?.nombre||'').toLowerCase().trim();return n.startsWith(x);})||null;
}

function getFilteredData(){
  if(currentIsla==='todas'){const subs=REGIONS[currentCA]?.subs||[];return atmosferaData.filter(d=>subs.includes(d.municipios?.isla));}
  return atmosferaData.filter(d=>d.municipios?.isla===currentIsla);
}

function toggleModuleDropdown(){document.getElementById('moduleDropdown').classList.toggle('visible');}

function setModule(mod){
  currentModule=mod;
  document.getElementById('moduleDropdown').classList.remove('visible');
  if(mod==='solar'){
    document.body.classList.add('solar');
    document.getElementById('moduleLabel').innerHTML='Solar<span style="color:var(--solar-accent)">Score</span>';
  } else {
    document.body.classList.remove('solar');
    document.getElementById('moduleLabel').innerHTML='Dew<span style="color:var(--accent)">Score</span>';
  }
  currentLayer=MODULES[mod].defaultLayer;
  buildLayerTabs();
  updateLayerUI();
  renderTiles();
  renderList();
  if(selectedNombre){
    const datos=getDatos(selectedNombre);
    if(datos)buildDetailPanel(datos,selectedNombre);
  }
}

function buildModuleDropdown(){
  const dewSub = document.getElementById('module-dew-sub');
  const solSub = document.getElementById('module-sol-sub');
  if(dewSub) dewSub.textContent = t.moduleCondensation||'Atmospheric condensation';
  if(solSub) solSub.textContent = t.moduleSolar||'Solar radiation';
  const sideLabel = document.getElementById('sidebar-ordered-label');
  if(sideLabel) sideLabel.textContent = t.orderedBy||'Ordered by';
  const chartSub = document.getElementById('chart-subtitle-label');
  if(chartSub) chartSub.textContent = t.historicalData||'Historical AEMET data';
}

function buildLayerTabs(){
  document.getElementById('layerTabs').innerHTML=MODULES[currentModule].layers.map(k=>
    `<button class="tab ${k===currentLayer?'active':''}" onclick="setLayer('${k}')">${(t.layerTitles&&t.layerTitles[k])||k.toUpperCase()}</button>`
  ).join('');
}

function buildYearDropdown(){
  document.getElementById('yearDropdown').innerHTML=AVAILABLE_YEARS.slice().reverse().map(y=>
    `<div class="year-option ${y===currentYear?'active':''}" onclick="selectYear(${y})">${y}</div>`
  ).join('');
}

function toggleYearDropdown(){document.getElementById('yearDropdown').classList.toggle('visible');}

async function selectYear(year){
  currentYear=year;
  document.getElementById('yearLabel').textContent=year;
  document.getElementById('detailYear').textContent=year;
  document.getElementById('yearDropdown').classList.remove('visible');
  buildYearDropdown();
  await loadAtmosfera();
}

const CA_LABEL={'Comunidad de Madrid':'Madrid','Comunidad Foral de Navarra':'Navarra','Principado de Asturias':'Asturias','Región de Murcia':'Murcia','Ciudad de Ceuta':'Ceuta','Ciudad de Melilla':'Melilla'};
function buildCASelector(){
  const sel=document.getElementById('selectCA'); if(!sel) return;
  const lab=c=>CA_LABEL[c]||c;
  sel.innerHTML=Object.keys(REGIONS).sort((a,b)=>lab(a).localeCompare(lab(b),'es')).map(c=>`<option value="${c}"${currentCA===c?' selected':''}>${lab(c)}</option>`).join('');
}

function buildIslaSelector(){
  buildCASelector();
  const sel = document.getElementById('selectIsla');
  if(!sel) return;
  const reg=REGIONS[currentCA]||REGIONS['Canarias'];
  const allLabel=reg.kind==='islands'?(t.allIslands||'All islands'):(ALL_PROV[currentLang]||ALL_PROV.en);
  sel.innerHTML = `<option value="todas">${allLabel}</option>` +
    reg.subs.map(i=>`<option value="${i}"${currentIsla===i?' selected':''}>${i}</option>`).join('');
}

function resetDetail(){
  selectedNombre=null;selectedMunicipioId=null;
  document.getElementById('detailEmpty').style.display='flex';
  document.getElementById('detailHeader').style.display='none';
  document.getElementById('detailBody').style.display='none';
  document.getElementById('evolucionBtn').style.display='none';
}

function onCAChange(){
  currentCA=document.getElementById('selectCA').value;
  currentIsla='todas';
  buildIslaSelector();
  const v=(REGIONS[currentCA]||REGIONS['Canarias']).view;
  map.flyTo(v.center,v.zoom,{duration:1.2});
  renderList(); resetDetail();
}

function onIslaChange(){
  const isla=document.getElementById('selectIsla').value;
  currentIsla=isla;
  const view=isla==='todas'?(REGIONS[currentCA]||REGIONS['Canarias']).view:(ISLA_VIEW[isla]||ISLA_VIEW['Gran Canaria']);
  map.flyTo(view.center,view.zoom,{duration:1.2});
  renderList(); resetDetail();
}

async function loadAtmosfera(){
  showFooterLoading(true);
  try{
    const atm=await fetch(`${API}/atmosfera/${currentYear}`).then(r=>r.json());
    atmosferaData=atm;buildRegions(atm);buildIslaSelector();renderTiles();renderList();
  }catch(e){console.error(e);}
  showFooterLoading(false);
}

function showFooterLoading(v){document.getElementById('footerLoading').classList.toggle('visible',v);}

async function init(){
  map=L.map('map',{center:ISLA_VIEW['Gran Canaria'].center,zoom:10,zoomControl:true,attributionControl:false,minZoom:4,maxZoom:18});
  L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,minZoom:4,subdomains:'abc'}).addTo(map);
  map.on('zoomend moveend',()=>{showFooterLoading(true);renderTiles();});

  if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(async pos=>{
      map.setView([pos.coords.latitude,pos.coords.longitude],10);
      try{
        const r=await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&format=json&accept-language=${lang}`);
        const d=await r.json();
        const isla=d.address?.island||null;
        if(isla&&ISLA_VIEW[isla]){document.getElementById('selectIsla').value=isla;currentIsla=isla;}
      }catch{}
    },()=>{});
  }

  buildLayerTabs();
  buildYearDropdown();
  buildIslaSelector();
  buildModuleDropdown();
  updateAbout();

  try{
    const atm=await fetch(`${API}/atmosfera/${currentYear}`).then(r=>r.json());
    atmosferaData=atm;buildRegions(atm);buildIslaSelector();
    document.getElementById('mapLoading').style.display='none';
    renderTiles();renderList();
  }catch(e){
    document.getElementById('mapLoading').innerHTML=`<div style="padding:20px;color:#ff6b6b;font-family:monospace;font-size:0.72rem;text-align:center">Error cargando datos.</div>`;
  }
}

function renderTiles(){
  const LAYERS=getLAYERS();
  const bgColor=currentModule==='solar'?'#1a1008':'#0a1628';
  const borderColor=currentModule==='solar'?'#5c3a1a':'#1e4976';

  const oldTileLayer = tileLayer;

  const newTileLayer=L.vectorGrid.protobuf(`${API}/tiles/{z}/{x}/{y}`,{
    vectorTileLayerStyles:{municipios:p=>{
      const d=getDatos(p.nombre);
      const L=LAYERS[currentLayer];
      if(!L)return{fill:true,fillColor:bgColor,fillOpacity:0.3,stroke:true,color:borderColor,weight:1,opacity:1};
      const v=d?L.getValue(d):0;
      const c=d?L.color(v):bgColor;
      const sel=selectedNombre===p.nombre;
      return{fill:true,fillColor:c,fillOpacity:sel?0.85:0.62,stroke:true,color:sel?'#fff':borderColor,weight:sel?2.5:1,opacity:1};
    }},
    interactive:true,
    getFeatureId:f=>f.properties.nombre
  });

  newTileLayer.on('click',e=>selectMunicipio(e.layer.properties.nombre,getDatos(e.layer.properties.nombre)));

  // Solo quitamos la capa vieja DESPUÉS de que la nueva haya terminado de cargar
  // — así nunca hay un momento sin colores visibles en el mapa
  let swapped = false;
  function swapLayers(){
    if(swapped) return;
    swapped = true;
    if(oldTileLayer && map.hasLayer(oldTileLayer)) map.removeLayer(oldTileLayer);
    showFooterLoading(false);
  }

  newTileLayer.on('load', swapLayers);
  // Salvaguarda: si el evento 'load' tarda demasiado o no llega, forzamos el swap
  // a los 4s para no dejar el footer "Cargando..." colgado indefinidamente
  setTimeout(swapLayers, 4000);

  newTileLayer.addTo(map);
  tileLayer = newTileLayer;
}

function renderList(){
  const LAYERS=getLAYERS();
  const L=LAYERS[currentLayer];
  if(!L){document.getElementById('municipioList').innerHTML='';return;}
  const filtered=getFilteredData();
  const sorted=[...filtered].sort((a,b)=>L.rev?L.getValue(a)-L.getValue(b):L.getValue(b)-L.getValue(a));
  document.getElementById('municipioList').innerHTML=sorted.map(d=>{
    const n=d.municipios?.nombre||'—';
    const v=L.getValue(d);
    const b=L.badge(v,t);
    return`<div class="municipio-card ${selectedNombre===n?'selected':''}" onclick="selectMunicipio('${n}',null)">
      <div class="municipio-card-left">
        <div class="municipio-name">${n}</div>
        <div class="municipio-sub">${L.format(v)} · T<sub>d</sub>:${(d.punto_rocio_c??0).toFixed(1)}°C</div>
      </div>
      <div class="level-badge" style="background:${b.bg};color:${b.c}">${b.tx}</div>
    </div>`;
  }).join('');
}

function buildDetailPanel(datos,nombre){
  const layers = MODULES[currentModule].layers;
  let html = '';

  if(currentModule === 'dew'){
    // Fila fija de temperatura/humedad/rocío siempre dentro de DewScore
    const temp=datos.temp_media_c??0, hum=datos.humedad_relativa_pct??0, rocio=datos.punto_rocio_c??0;
    html += `<div class="detail-row">
      <div class="detail-row-header"><span class="detail-row-label">🌡 ${t.rowLabels?.temp||'Mean Temp.'}</span><span class="detail-row-value">${temp.toFixed(1)}°C</span></div>
      <div class="detail-row-desc">${t.descTemp(temp)}</div>
    </div>`;
    html += `<div class="detail-row">
      <div class="detail-row-header"><span class="detail-row-label">💧 ${t.rowLabels?.humedad||'Rel. Humidity'}</span><span class="detail-row-value">${hum.toFixed(0)}%</span></div>
      <div class="detail-row-desc">${t.descHum(hum)}</div>
    </div>`;
    html += `<div class="detail-row">
      <div class="detail-row-header"><span class="detail-row-label">❄️ ${t.rocioLabel||'Dew Point'}</span><span class="detail-row-value" style="color:var(--accent)">${rocio.toFixed(1)}°C</span></div>
      <div class="detail-row-key">${t.rocioKey||'T<sub>d</sub> (°C)'}</div>
      <div class="detail-row-desc">${t.descRocio(rocio,temp)}</div>
    </div>`;

    ['delta','cfi','df','hhf','awvc'].forEach(key=>{
      const def = getRowDefs()[key];
      const raw = datos[def.field] ?? 0;
      const desc = def.desc(raw);
      const barHtml = def.bar
        ? `<div class="mini-bar-bg"><div class="mini-bar-fill" style="background:${def.bar};width:${Math.min(((raw-(def.min||0))/((def.max||1)-(def.min||0)))*100,100)}%"></div></div>`
        : '';
      html += `<div class="detail-row">
        <div class="detail-row-header"><span class="detail-row-label">${def.icon} ${def.label}</span><span class="detail-row-value" style="color:${def.color}">${def.fmt(raw)}</span></div>
        <div class="detail-row-key">${def.key}</div>
        <div class="detail-row-desc">${desc}</div>
        ${barHtml}
      </div>`;
    });
  }

  if(currentModule === 'solar'){
    const solar = datos.municipios?.radiacion_solar_kwh ?? 0;
    const def = getRowDefs().solar;
    const desc = solar>0 ? def.desc(solar) : '—';
    const barHtml = `<div class="mini-bar-bg"><div class="mini-bar-fill" style="background:${def.bar};width:${solar>0?Math.min(((solar-def.min)/(def.max-def.min))*100,100):0}%"></div></div>`;
    html += `<div class="detail-row">
      <div class="detail-row-header"><span class="detail-row-label">${def.icon} ${def.label}</span><span class="detail-row-value" style="color:${def.color}">${solar>0?def.fmt(solar):'—'}</span></div>
      <div class="detail-row-key">${def.key}</div>
      <div class="detail-row-desc">${desc}</div>
      ${barHtml}
    </div>`;
  }

  document.getElementById('detailBody').innerHTML = html;
}

function selectMunicipio(nombre,datos){
  if(selectedNombre&&selectedNombre!==nombre&&tileLayer)tileLayer.resetFeatureStyle(selectedNombre);
  selectedNombre=nombre;
  if(!datos)datos=getDatos(nombre);
  if(datos){
    selectedMunicipioId=datos.municipio_id;
    document.getElementById('detailName').textContent=datos.municipios?.nombre||nombre;
    buildDetailPanel(datos,nombre);
    document.getElementById('detailEmpty').style.display='none';
    document.getElementById('detailHeader').style.display='block';
    document.getElementById('detailBody').style.display='flex';
    document.getElementById('evolucionBtn').style.display='block';
    if(tileLayer){
      const sc=currentModule==='solar'?'#f59e0b':'#00d4ff';
      tileLayer.setFeatureStyle(nombre,{fill:true,fillColor:sc,fillOpacity:0.2,stroke:true,color:'#fff',weight:2.5,opacity:1});
    }
  }
  renderList();
}

function setLayer(layer){
  currentLayer=layer;
  buildLayerTabs();
  updateLayerUI();
  renderList();renderTiles();
}

function updateLayerUI(){
  const LAYERS=getLAYERS();
  const cfg=LAYERS[currentLayer];
  if(!cfg)return;
  document.getElementById('sidebarTitle').innerHTML=t.layerTitles[currentLayer]||currentLayer;
  document.getElementById('legendLabel').innerHTML=cfg.legendLabel;
  document.getElementById('legendGradient').style.background=cfg.gradient;
  document.getElementById('legendMin').textContent=cfg.minLabel;
  document.getElementById('legendMax').textContent=cfg.maxLabel;
}

function buildChartVarButtons(){
  const vars = getChartVars();
  document.getElementById('chartVarSelect').innerHTML = vars.map(v=>
    `<button class="chart-var-btn ${v.key===currentChartVar?'active':''}" onclick="setChartVar('${v.key}')">${v.label}</button>`
  ).join('');
}

async function openChart(){
  if(!selectedMunicipioId)return;
  document.getElementById('chartOverlay').classList.add('visible');
  document.getElementById('chartTitle').textContent=(t.evolutionTitle||'Temporal evolution')+' — '+selectedNombre;
  currentChartVar = getChartVars()[0].key;
  buildChartVarButtons();

  if(currentModule==='solar'){
    // La radiación solar es un valor fijo por municipio (PVGIS), no varía por año en los datos actuales
    const subtitleEl = document.getElementById('chart-subtitle-label');
    if(subtitleEl) subtitleEl.textContent = t.solarStatic||'Fixed value (PVGIS) — no interannual variation in available data';
    const datos = getDatos(selectedNombre);
    const solar = datos?.municipios?.radiacion_solar_kwh ?? 0;
    renderSolarStaticChart(solar);
    return;
  }

  const subEl = document.getElementById('chart-subtitle-label');
  if(subEl) subEl.textContent = t.historicalData||'Historical AEMET data';
  try{
    serieData=await fetch(`${API}/serie/${selectedMunicipioId}`).then(r=>r.json());
    renderChart();
  }catch(e){console.error(e);}
}

function closeChart(e){if(!e||e.target===document.getElementById('chartOverlay'))document.getElementById('chartOverlay').classList.remove('visible');}
function setChartVar(key){currentChartVar=key;buildChartVarButtons();if(currentModule!=='solar')renderChart();}

function renderSolarStaticChart(solar){
  const ctx=document.getElementById('temporalChart').getContext('2d');
  if(chartInstance)chartInstance.destroy();
  const grid='rgba(60,40,20,0.5)',tick='#8b6040';
  chartInstance=new Chart(ctx,{
    type:'bar',
    data:{labels:[selectedNombre],datasets:[{label:t.layerTitles?.solar||'Solar Irradiation (kWh/m²)',data:[solar],backgroundColor:'#f59e0b',borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:true,
      plugins:{legend:{display:false},tooltip:{backgroundColor:'#2a1a0a',borderColor:'#5c3a1a',borderWidth:1,titleColor:'#c4874a',bodyColor:'#fef3c7',titleFont:{family:'Space Mono',size:11},bodyFont:{family:'Space Mono',size:12}}},
      scales:{x:{grid:{color:grid},ticks:{color:tick,font:{family:'Space Mono',size:10}}},y:{grid:{color:grid},ticks:{color:tick,font:{family:'Space Mono',size:10}},title:{display:true,text:'kWh/m²/año',color:tick,font:{family:'Space Mono',size:10}}}}}
  });
}

function renderChart(){
  const ctx=document.getElementById('temporalChart').getContext('2d');
  if(chartInstance)chartInstance.destroy();
  const varCfg=getChartVars().find(v=>v.key===currentChartVar);
  if(!varCfg||!serieData.length)return;
  const grid='rgba(30,73,118,0.5)',tick='#4a7a9b';
  chartInstance=new Chart(ctx,{
    type:'line',
    data:{labels:serieData.map(d=>d.año),datasets:[{label:String(varCfg.label).replace(/<\/?sub>/g,''),data:serieData.map(d=>d[varCfg.key]),borderColor:varCfg.color,backgroundColor:varCfg.color.replace(')',',0.12)').replace('rgb','rgba'),borderWidth:2,pointRadius:4,pointHoverRadius:6,tension:0.3,fill:true}]},
    options:{responsive:true,maintainAspectRatio:true,interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:false},tooltip:{backgroundColor:'#0f2040',borderColor:'#1e4976',borderWidth:1,titleColor:'#7aafc8',bodyColor:'#e0f0ff',titleFont:{family:'Space Mono',size:11},bodyFont:{family:'Space Mono',size:12}}},
      scales:{x:{grid:{color:grid},ticks:{color:tick,font:{family:'Space Mono',size:10}},title:{display:true,text:'Año',color:tick,font:{family:'Space Mono',size:10}}},y:{grid:{color:grid},ticks:{color:tick,font:{family:'Space Mono',size:10}},title:{display:true,text:varCfg.yLabel,color:tick,font:{family:'Space Mono',size:10}}}}}
  });
}

function openAbout(){updateAbout();document.getElementById('aboutOverlay').classList.add('visible');if(window.MathJax)MathJax.typesetPromise();}
function closeAbout(e){if(!e||e.target===document.getElementById('aboutOverlay'))document.getElementById('aboutOverlay').classList.remove('visible');}

document.addEventListener('click',e=>{
  if(!e.target.closest('.year-selector'))document.getElementById('yearDropdown').classList.remove('visible');
  if(!e.target.closest('.module-selector'))document.getElementById('moduleDropdown').classList.remove('visible');
});

init();
// Add upgrade banner to detail panel for free users
const _origBuildDetail = buildDetailPanel;
buildDetailPanel = function(datos, nombre) {
  _origBuildDetail(datos, nombre);

};

// Expose functions globally
window.toggleModuleDropdown = toggleModuleDropdown;
window.setModule = setModule;
window.setLayer = setLayer;
window.selectYear = selectYear;
window.toggleYearDropdown = toggleYearDropdown;
window.onCAChange = onCAChange;
window.onIslaChange = onIslaChange;
window.openChart = openChart;
window.closeChart = closeChart;
window.setChartVar = setChartVar;
window.openAbout = openAbout;
window.closeAbout = closeAbout;
window.selectMunicipio = selectMunicipio;
}
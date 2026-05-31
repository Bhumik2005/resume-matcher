import { motion } from 'framer-motion'

const bars = [
  { key: 'tfidf', label: 'TF-IDF Keywords', color: '#6366f1', desc: 'Exact keyword overlap' },
  { key: 'sbert', label: 'SBERT Semantic', color: '#a855f7', desc: 'Meaning & context match' },
  { key: 'skill', label: 'Skill Match', color: '#06b6d4', desc: 'Technical skills gap' },
]

export default function ScoreBreakdown({ breakdown, sections }) {
  return (
    <div style={{
      background: 'var(--card)', borderRadius: '20px',
      border: '1px solid var(--border)', padding: '28px',
      height: '100%',
    }}>
      <div style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '24px' }}>
        Score Breakdown
      </div>

      {/* Layer scores */}
      <div style={{ marginBottom: '28px' }}>
        {bars.map(({ key, label, color, desc }, i) => {
          const val = breakdown[key]?.score ?? 0
          const pct = Math.round(val * 100)
          return (
            <div key={key} style={{ marginBottom: '18px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '6px' }}>
                <div>
                  <span style={{ fontSize: '13px', color: 'var(--text)', fontWeight: 500 }}>{label}</span>
                  <span style={{ fontSize: '11px', color: 'var(--muted)', marginLeft: '8px' }}>{desc}</span>
                </div>
                <span style={{ fontSize: '14px', fontWeight: 700, color, fontFamily: 'Syne, sans-serif' }}>{pct}%</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 1, delay: i * 0.1, ease: 'easeOut' }}
                  style={{
                    height: '100%', borderRadius: '3px',
                    background: `linear-gradient(90deg, ${color}, ${color}99)`,
                    boxShadow: `0 0 8px ${color}66`,
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>

      {/* Section scores */}
      {Object.keys(sections).length > 0 && (
        <>
          <div style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>
            By Section
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '10px' }}>
            {Object.entries(sections).map(([sec, val]) => {
              const pct = Math.round(val * 100)
              const c = pct >= 75 ? '#10b981' : pct >= 50 ? '#fbbf24' : '#f43f5e'
              return (
                <div key={sec} style={{
                  background: 'var(--card2)', borderRadius: '10px',
                  padding: '12px', textAlign: 'center',
                  border: '1px solid var(--border)',
                }}>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: c, fontFamily: 'Syne, sans-serif' }}>{pct}%</div>
                  <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px', textTransform: 'capitalize' }}>{sec}</div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
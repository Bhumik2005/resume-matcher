import { motion } from 'framer-motion'

const Badge = ({ label, type }) => {
  const styles = {
    matched: { bg: 'rgba(16,185,129,0.1)', color: '#10b981', border: 'rgba(16,185,129,0.25)' },
    missing: { bg: 'rgba(244,63,94,0.1)', color: '#f43f5e', border: 'rgba(244,63,94,0.25)' },
    extra:   { bg: 'rgba(99,102,241,0.1)', color: '#818cf8', border: 'rgba(99,102,241,0.25)' },
  }
  const s = styles[type]
  return (
    <span style={{
      display: 'inline-block', padding: '4px 12px', borderRadius: '20px',
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      fontSize: '12px', fontWeight: 500, margin: '3px',
    }}>{label}</span>
  )
}

const Panel = ({ title, icon, skills, type, delay }) => (
  <motion.div
    initial={{ opacity: 0, y: 16 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    style={{
      background: 'var(--card)', borderRadius: '16px',
      border: '1px solid var(--border)', padding: '22px',
    }}
  >
    <div style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '14px' }}>
      {icon} {title} <span style={{ color: 'var(--muted)', marginLeft: '4px' }}>({skills.length})</span>
    </div>
    <div>
      {skills.length > 0
        ? skills.map(s => <Badge key={s} label={s} type={type} />)
        : <span style={{ color: 'var(--muted)', fontSize: '13px' }}>None found</span>
      }
    </div>
  </motion.div>
)

export default function SkillsSection({ skillAnalysis }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
      <Panel title="Matched Skills" icon="✓" skills={skillAnalysis.matched_skills} type="matched" delay={0} />
      <Panel title="Missing Skills" icon="✗" skills={skillAnalysis.missing_skills} type="missing" delay={0.05} />
      <Panel title="Bonus Skills" icon="+" skills={skillAnalysis.extra_skills} type="extra" delay={0.1} />
    </div>
  )
}
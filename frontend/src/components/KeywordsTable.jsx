import { motion } from 'framer-motion'

export default function KeywordsTable({ keywords }) {
  const top = keywords.slice(0, 12)
  return (
    <div style={{
      background: 'var(--card)', borderRadius: '20px',
      border: '1px solid var(--border)', padding: '28px',
    }}>
      <div style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '20px' }}>
        Keyword Density — Top {top.length} from Job Description
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px' }}>
        {top.map((kw, i) => (
          <motion.div
            key={kw.term}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.03 }}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderRadius: '10px',
              background: kw.in_resume ? 'rgba(16,185,129,0.06)' : 'rgba(244,63,94,0.06)',
              border: `1px solid ${kw.in_resume ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)'}`,
            }}
          >
            <span style={{ fontSize: '13px', color: 'var(--text)', fontWeight: 500 }}>{kw.term}</span>
            <span style={{
              fontSize: '11px', fontWeight: 700,
              color: kw.in_resume ? '#10b981' : '#f43f5e',
            }}>
              {kw.in_resume ? '✓' : '✗'}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
import { motion } from 'framer-motion'

export default function Suggestions({ suggestions }) {
  return (
    <div style={{
      background: 'var(--card)', borderRadius: '20px',
      border: '1px solid var(--border)', padding: '28px',
      height: '100%',
    }}>
      <div style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '20px' }}>
        AI Suggestions
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {suggestions.map((s, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            style={{
              padding: '12px 14px',
              background: 'var(--yellow-dim)',
              borderLeft: '3px solid var(--yellow)',
              borderRadius: '0 10px 10px 0',
              fontSize: '13px', color: 'var(--muted2)',
              lineHeight: 1.6,
            }}
          >
            <span style={{ color: 'var(--yellow)', marginRight: '8px' }}>→</span>
            {s}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
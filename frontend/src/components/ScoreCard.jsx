import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

const getColor = (pct) => pct >= 75 ? '#10b981' : pct >= 50 ? '#fbbf24' : '#f43f5e'
const getGlow  = (pct) => pct >= 75 ? 'rgba(16,185,129,0.25)' : pct >= 50 ? 'rgba(251,191,36,0.25)' : 'rgba(244,63,94,0.25)'

export default function ScoreCard({ result }) {
  const [count, setCount] = useState(0)
  const target = result.match_percentage
  const color  = getColor(target)
  const glow   = getGlow(target)

  useEffect(() => {
    let n = 0
    const step = target / 70
    const t = setInterval(() => {
      n += step
      if (n >= target) { setCount(target); clearInterval(t) }
      else setCount(Math.floor(n))
    }, 14)
    return () => clearInterval(t)
  }, [target])

  const r = 54
  const circ = 2 * Math.PI * r
  const offset = circ - (count / 100) * circ

  return (
    <div style={{
      background: 'rgba(255,255,255,0.02)',
      borderRadius: '24px',
      border: '1px solid rgba(255,255,255,0.07)',
      padding: '36px 24px',
      textAlign: 'center',
      height: '100%',
      backdropFilter: 'blur(20px)',
      boxShadow: `0 0 60px ${glow}, inset 0 1px 0 rgba(255,255,255,0.05)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Background shimmer */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: '24px',
        background: `radial-gradient(circle at 50% 0%, ${glow} 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      <div style={{ fontSize: '10px', color: 'var(--muted)', letterSpacing: '2.5px', textTransform: 'uppercase', marginBottom: '28px', position: 'relative' }}>
        Overall Match
      </div>

      {/* SVG ring */}
      <div style={{ position: 'relative', width: '140px', height: '140px', marginBottom: '24px' }}>
        <svg width="140" height="140" style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="9" />
          <motion.circle
            cx="70" cy="70" r={r} fill="none"
            stroke={color} strokeWidth="9" strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.4, ease: [0.32, 0.72, 0, 1] }}
            style={{ filter: `drop-shadow(0 0 10px ${color}) drop-shadow(0 0 20px ${color}66)` }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{
            fontSize: '36px', fontWeight: 800, color,
            fontFamily: 'Syne, sans-serif', lineHeight: 1,
            textShadow: `0 0 30px ${color}`,
          }}>{count}</span>
          <span style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '2px' }}>%</span>
        </div>
      </div>

      <div style={{
        fontSize: '16px', fontWeight: 800, color,
        fontFamily: 'Syne, sans-serif',
        letterSpacing: '2px', textTransform: 'uppercase',
        textShadow: `0 0 20px ${color}`,
        marginBottom: '10px',
        position: 'relative',
      }}>
        {result.match_label}
      </div>
      <div style={{ fontSize: '12px', color: 'var(--muted)', lineHeight: 1.6, position: 'relative' }}>
        Keywords · Semantics · Skills
      </div>
    </div>
  )
}
import { motion } from 'framer-motion'
import ScoreCard from './ScoreCard'
import ScoreBreakdown from './ScoreBreakdown'
import SkillsSection from './SkillsSection'
import KeywordsTable from './KeywordsTable'
import Suggestions from './Suggestions'

export default function Results({ result, onReset }) {
  const fadeUp = (delay = 0) => ({
    initial: { opacity: 0, y: 24 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, delay },
  })

  return (
    <div style={{ paddingTop: '48px' }}>
      {/* Top row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr 1.3fr', gap: '20px', marginBottom: '20px' }}>
        <motion.div {...fadeUp(0)}><ScoreCard result={result} /></motion.div>
        <motion.div {...fadeUp(0.1)}><ScoreBreakdown breakdown={result.score_breakdown} sections={result.section_scores} /></motion.div>
        <motion.div {...fadeUp(0.15)}><Suggestions suggestions={result.suggestions} /></motion.div>
      </div>

      {/* Skills row */}
      <motion.div {...fadeUp(0.2)} style={{ marginBottom: '20px' }}>
        <SkillsSection skillAnalysis={result.skill_analysis} />
      </motion.div>

      {/* Keywords */}
      <motion.div {...fadeUp(0.25)} style={{ marginBottom: '40px' }}>
        <KeywordsTable keywords={result.keyword_analysis} />
      </motion.div>

      {/* Reset */}
      <motion.div {...fadeUp(0.3)} style={{ textAlign: 'center' }}>
        <button onClick={onReset} style={{
          padding: '12px 32px', borderRadius: '12px',
          background: 'transparent', border: '1px solid rgba(255,255,255,0.12)',
          color: 'var(--muted2)', fontSize: '14px', cursor: 'pointer',
          fontFamily: 'Inter, sans-serif', transition: 'all 0.2s',
        }}
          onMouseEnter={e => { e.target.style.borderColor = 'rgba(255,255,255,0.25)'; e.target.style.color = 'var(--text)' }}
          onMouseLeave={e => { e.target.style.borderColor = 'rgba(255,255,255,0.12)'; e.target.style.color = 'var(--muted2)' }}
        >
          ← Analyse Another Resume
        </button>
      </motion.div>
    </div>
  )
}
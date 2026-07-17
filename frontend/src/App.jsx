import { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import UploadSection from './components/UploadSection'
import Results from './components/Results'
import Header from './components/Header'
import Background from './components/Background'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [apiWarm, setApiWarm] = useState(false)

  // Wake up the API as soon as page loads
  useEffect(() => {
    const warmUp = async () => {
      try {
        await fetch(`${API}/health`)
        setApiWarm(true)
      } catch {
        setApiWarm(false)
      }
    }
    warmUp()
  }, [])

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <Background />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <Header />
        {!apiWarm && (
          <div style={{
            textAlign: 'center',
            padding: '8px',
            background: 'rgba(251,191,36,0.08)',
            borderBottom: '1px solid rgba(251,191,36,0.2)',
            color: '#fbbf24',
            fontSize: '13px',
          }}>
            ⏳ AI engine warming up — first analysis may take 60-90 seconds
          </div>
        )}
        <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '0 24px 80px' }}>
          <AnimatePresence mode="wait">
            {!result ? (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.4 }}
              >
                <UploadSection setResult={setResult} loading={loading} setLoading={setLoading} />
              </motion.div>
            ) : (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.4 }}
              >
                <Results result={result} onReset={() => setResult(null)} />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
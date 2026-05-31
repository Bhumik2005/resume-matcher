import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import UploadSection from './components/UploadSection'
import Results from './components/Results'
import Header from './components/Header'
import Background from './components/Background'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <Background />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <Header />
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
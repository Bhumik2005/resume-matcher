import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'

export default function UploadSection({ setResult, loading, setLoading }) {
  const [file, setFile] = useState(null)
  const [jd, setJd] = useState('')
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const handleFile = (f) => {
    if (f?.type === 'application/pdf') { setFile(f); setError('') }
    else setError('Please upload a PDF file.')
  }

  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleSubmit = async () => {
    if (!file) return setError('Please upload your resume PDF.')
    if (jd.trim().length < 50) return setError('Please paste a full job description (min 50 chars).')
    setError(''); setLoading(true)
    try {
      const form = new FormData()
      form.append('resume', file)
      form.append('job_description', jd)
      const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const { data } = await axios.post(`${API}/api/v1/match`, form)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Cannot connect to API. Is the backend running on port 8000?')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ paddingTop: '80px', paddingBottom: '40px' }}>

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        style={{ textAlign: 'center', marginBottom: '64px' }}
      >
        {/* Pill badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            padding: '6px 18px', borderRadius: '100px',
            background: 'rgba(99,102,241,0.08)',
            border: '1px solid rgba(99,102,241,0.2)',
            marginBottom: '28px',
          }}
        >
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#6366f1', boxShadow: '0 0 8px #6366f1', display: 'inline-block' }} />
          <span style={{ fontSize: '11px', color: '#818cf8', fontWeight: 600, letterSpacing: '1.5px', textTransform: 'uppercase' }}>
            TF-IDF · SBERT · spaCy NER
          </span>
        </motion.div>

        <h1 style={{
          fontFamily: 'Syne, sans-serif', fontWeight: 800,
          fontSize: 'clamp(42px, 7vw, 76px)',
          lineHeight: 1.05, letterSpacing: '-3px',
          marginBottom: '20px',
        }}>
          <span style={{
            background: 'linear-gradient(180deg, #ffffff 0%, rgba(255,255,255,0.7) 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>Know your match</span>
          <br />
          <span style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 40%, #06b6d4 100%)',
            backgroundSize: '200% auto',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            animation: 'shimmer 4s linear infinite',
          }}>before they decide.</span>
        </h1>

        <p style={{
          color: 'var(--muted2)', fontSize: '17px',
          maxWidth: '500px', margin: '0 auto', lineHeight: 1.7,
          fontWeight: 300,
        }}>
          Upload your resume and paste any job description.
          Our 3-layer AI pipeline scores your fit and shows exactly what's missing.
        </p>
      </motion.div>

      {/* Input cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>

        {/* PDF drop zone */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div
            onClick={() => fileRef.current.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            style={{
              minHeight: '200px', borderRadius: '20px', cursor: 'pointer',
              border: `1px solid ${dragging ? 'rgba(99,102,241,0.6)' : file ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.07)'}`,
              background: dragging
                ? 'rgba(99,102,241,0.08)'
                : file
                ? 'rgba(16,185,129,0.04)'
                : 'rgba(255,255,255,0.02)',
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              gap: '12px', transition: 'all 0.25s',
              boxShadow: dragging ? '0 0 40px rgba(99,102,241,0.15), inset 0 0 40px rgba(99,102,241,0.05)' :
                file ? '0 0 30px rgba(16,185,129,0.08)' : 'none',
              backdropFilter: 'blur(10px)',
              padding: '32px',
            }}
          >
            <input ref={fileRef} type="file" accept=".pdf"
              style={{ display: 'none' }}
              onChange={e => handleFile(e.target.files[0])} />

            {/* Icon */}
            <div style={{
              width: '56px', height: '56px', borderRadius: '16px',
              background: file ? 'rgba(16,185,129,0.1)' : 'rgba(99,102,241,0.1)',
              border: `1px solid ${file ? 'rgba(16,185,129,0.2)' : 'rgba(99,102,241,0.2)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '24px',
            }}>
              {file ? '✅' : '📄'}
            </div>

            {file ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#10b981', fontWeight: 600, fontSize: '14px' }}>{file.name}</div>
                <div style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '4px' }}>
                  {(file.size / 1024).toFixed(1)} KB · Click to change
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: 'var(--text)', fontWeight: 600, fontSize: '15px' }}>
                  Drop resume here
                </div>
                <div style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '4px' }}>
                  or click to browse · PDF only
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* JD textarea */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.25, duration: 0.5 }}
        >
          <textarea
            value={jd}
            onChange={e => setJd(e.target.value)}
            placeholder="Paste the full job description here..."
            style={{
              width: '100%', height: '100%', minHeight: '200px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.07)',
              borderRadius: '20px', padding: '22px',
              color: 'var(--text)', fontSize: '14px',
              lineHeight: 1.7, resize: 'none', outline: 'none',
              fontFamily: 'Inter, sans-serif',
              transition: 'all 0.25s', boxSizing: 'border-box',
              backdropFilter: 'blur(10px)',
            }}
            onFocus={e => {
              e.target.style.borderColor = 'rgba(99,102,241,0.4)'
              e.target.style.boxShadow = '0 0 30px rgba(99,102,241,0.08), inset 0 0 30px rgba(99,102,241,0.03)'
            }}
            onBlur={e => {
              e.target.style.borderColor = 'rgba(255,255,255,0.07)'
              e.target.style.boxShadow = 'none'
            }}
          />
        </motion.div>
      </div>

      {/* Character count */}
      <div style={{ textAlign: 'right', marginBottom: '16px', marginRight: '4px' }}>
        <span style={{ fontSize: '12px', color: jd.length >= 50 ? 'var(--green)' : 'var(--muted)' }}>
          {jd.length} chars {jd.length >= 50 ? '✓' : `· need ${50 - jd.length} more`}
        </span>
      </div>

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'var(--red-dim)', border: '1px solid rgba(244,63,94,0.25)',
            borderRadius: '12px', padding: '12px 18px',
            color: 'var(--red)', fontSize: '14px', marginBottom: '16px',
          }}
        >⚠️ {error}</motion.div>
      )}

      {/* Button */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        style={{ display: 'flex', justifyContent: 'center' }}
      >
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            padding: '16px 56px', borderRadius: '16px', border: 'none',
            background: loading
              ? 'rgba(99,102,241,0.2)'
              : 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            color: 'white', fontSize: '16px', fontWeight: 700,
            cursor: loading ? 'not-allowed' : 'pointer',
            fontFamily: 'Syne, sans-serif', letterSpacing: '0.5px',
            boxShadow: loading ? 'none' : '0 0 40px rgba(99,102,241,0.35), 0 0 80px rgba(99,102,241,0.15)',
            transition: 'all 0.3s', minWidth: '240px',
            transform: 'translateY(0)',
          }}
          onMouseEnter={e => {
            if (!loading) {
              e.target.style.transform = 'translateY(-2px)'
              e.target.style.boxShadow = '0 8px 50px rgba(99,102,241,0.45), 0 0 80px rgba(99,102,241,0.2)'
            }
          }}
          onMouseLeave={e => {
            e.target.style.transform = 'translateY(0)'
            e.target.style.boxShadow = loading ? 'none' : '0 0 40px rgba(99,102,241,0.35), 0 0 80px rgba(99,102,241,0.15)'
          }}
        >
          {loading ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center' }}>
              <span style={{
                width: '16px', height: '16px',
                border: '2px solid rgba(255,255,255,0.3)',
                borderTopColor: 'white', borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
                display: 'inline-block', flexShrink: 0,
              }} />
              Analysing your resume...
            </span>
          ) : '⚡ Analyse Match'}
        </button>
      </motion.div>
    </div>
  )
}
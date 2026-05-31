import { useEffect, useRef } from 'react'

export default function Background() {
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 0, overflow: 'hidden', pointerEvents: 'none' }}>

      {/* Deep base gradient */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,0.15) 0%, transparent 60%)',
      }} />

      {/* Left orb */}
      <div style={{
        position: 'absolute', top: '5%', left: '-5%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 65%)',
        filter: 'blur(60px)',
        animation: 'float 8s ease-in-out infinite',
      }} />

      {/* Right orb */}
      <div style={{
        position: 'absolute', top: '20%', right: '-8%',
        width: '600px', height: '600px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(168,85,247,0.14) 0%, transparent 65%)',
        filter: 'blur(80px)',
        animation: 'float 10s ease-in-out infinite reverse',
      }} />

      {/* Bottom orb */}
      <div style={{
        position: 'absolute', bottom: '-5%', left: '35%',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 65%)',
        filter: 'blur(60px)',
        animation: 'float 12s ease-in-out infinite',
      }} />

      {/* Subtle dot grid */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.07) 1px, transparent 1px)',
        backgroundSize: '32px 32px',
        maskImage: 'radial-gradient(ellipse 80% 80% at 50% 50%, black 40%, transparent 100%)',
      }} />

      {/* Top edge glow line */}
      <div style={{
        position: 'absolute', top: 0, left: '20%', right: '20%', height: '1px',
        background: 'linear-gradient(90deg, transparent, rgba(99,102,241,0.5), rgba(168,85,247,0.5), transparent)',
      }} />
    </div>
  )
}
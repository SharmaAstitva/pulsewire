import { useState } from 'react'
import { Link } from 'react-router-dom'

const COVERAGE_CATS = ['World', 'Technology', 'Finance', 'Science', 'Sports', 'Health']
const COMPANY_LINKS = ['About PulseWire', 'Our Journalists', 'Careers', 'Advertise']
const LEGAL_LINKS   = ['Privacy Policy', 'Terms of Use', 'Cookie Settings', 'Accessibility']

export function Footer() {
  const [email, setEmail] = useState('')
  const [done, setDone]   = useState(false)
  const year = new Date().getFullYear()

  const handleSubscribe = (e) => {
    e.preventDefault()
    if (email) setDone(true)
  }

  return (
    <footer>
      {/* ── Dark main footer ─────────────────────── */}
      <div style={{ background: '#0F172A' }}>
        <div className="max-w-site mx-auto px-4 sm:px-6 py-12">
          {/* 4-column grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-10">

            {/* Brand column */}
            <div className="col-span-2 sm:col-span-1">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-7 h-7 flex items-center justify-center bg-white">
                  <span className="font-ui font-bold text-ink text-xs">P</span>
                </div>
                <span className="font-display font-bold text-xl text-white">PulseWire</span>
              </div>
              <p className="font-ui text-sm leading-relaxed" style={{ color: '#94A3B8' }}>
                AI-powered news intelligence delivering premium editorial coverage across
                the world's most important stories.
              </p>
            </div>

            {/* Company */}
            <div>
              <h3 className="font-ui text-[11px] font-bold tracking-[0.12em] uppercase mb-4"
                style={{ color: '#64748B' }}>Company</h3>
              <ul className="space-y-2.5">
                {COMPANY_LINKS.map(link => (
                  <li key={link}>
                    <a href="#"
                      className="font-ui text-sm transition-colors"
                      style={{ color: '#CBD5E1' }}
                      onMouseEnter={e => e.currentTarget.style.color = '#FFFFFF'}
                      onMouseLeave={e => e.currentTarget.style.color = '#CBD5E1'}
                    >{link}</a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Coverage */}
            <div>
              <h3 className="font-ui text-[11px] font-bold tracking-[0.12em] uppercase mb-4"
                style={{ color: '#64748B' }}>Coverage</h3>
              <ul className="space-y-2.5">
                {COVERAGE_CATS.map(cat => (
                  <li key={cat}>
                    <Link to="/"
                      className="font-ui text-sm transition-colors"
                      style={{ color: '#CBD5E1' }}
                      onMouseEnter={e => e.currentTarget.style.color = '#FFFFFF'}
                      onMouseLeave={e => e.currentTarget.style.color = '#CBD5E1'}
                    >{cat}</Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h3 className="font-ui text-[11px] font-bold tracking-[0.12em] uppercase mb-4"
                style={{ color: '#64748B' }}>Legal</h3>
              <ul className="space-y-2.5">
                {LEGAL_LINKS.map(link => (
                  <li key={link}>
                    <a href="#"
                      className="font-ui text-sm transition-colors"
                      style={{ color: '#CBD5E1' }}
                      onMouseEnter={e => e.currentTarget.style.color = '#FFFFFF'}
                      onMouseLeave={e => e.currentTarget.style.color = '#CBD5E1'}
                    >{link}</a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t" style={{ borderColor: '#1E293B' }} />

          {/* Bottom copyright row */}
          <div className="pt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <p className="font-ui text-xs" style={{ color: '#475569' }}>
              © {year} PulseWire. All rights reserved. Powered by AI News Intelligence.
            </p>
            <div className="flex items-center gap-4">
              {['Real-time coverage', 'AI-verified', 'Editorial standards'].map((item, i, arr) => (
                <span key={item} className="flex items-center gap-4">
                  <span className="font-ui text-xs" style={{ color: '#475569' }}>{item}</span>
                  {i < arr.length - 1 && (
                    <span style={{ color: '#334155' }}>·</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom newsletter bar ──────────────────── */}
      <div className="border-t" style={{ background: '#0F172A', borderColor: '#1E293B' }}>
        <div className="max-w-site mx-auto px-4 sm:px-6 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h4 className="font-display font-bold text-white text-base mb-0.5">
                The Daily Briefing
              </h4>
              <p className="font-ui text-sm" style={{ color: '#94A3B8' }}>
                The top stories, curated by our AI editors. Delivered each morning.
              </p>
            </div>
            {done ? (
              <p className="font-ui text-sm font-medium text-green-400 shrink-0">✓ You're subscribed!</p>
            ) : (
              <form onSubmit={handleSubscribe}
                className="flex gap-2 w-full sm:w-auto shrink-0">
                <input
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  className="font-ui text-sm px-3 py-2 bg-white text-ink outline-none border-0 w-full sm:w-56"
                  style={{ minWidth: 0 }}
                />
                <button
                  type="submit"
                  className="font-ui text-xs font-bold uppercase tracking-widest px-4 py-2 shrink-0
                             bg-white text-ink hover:bg-gray-100 transition-colors"
                >
                  Subscribe
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </footer>
  )
}

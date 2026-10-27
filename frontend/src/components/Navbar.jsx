import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCategories } from '../hooks/useData'
import { useDebounce } from '../hooks/useDebounce'
import { searchArticles } from '../api/client'

const NAV_CATS = ['World', 'Tech', 'Finance', 'Science', 'Sports', 'Health']

/* Map display names to API topic names */
const CAT_MAP = {
  'World':   'World News',
  'Tech':    'Technology',
  'Finance': 'Finance',
  'Science': 'Science',
  'Sports':  'Sports',
  'Health':  'Health',
}

export function Navbar({ activeCategory, onCategory, searchQuery, onSearch }) {
  const [searchOpen, setSearchOpen] = useState(false)
  const inputRef = useRef(null)
  const { data: cats } = useCategories()

  /* current day string */
  const dateStr = new Intl.DateTimeFormat('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
  }).format(new Date())

  useEffect(() => {
    if (searchOpen) inputRef.current?.focus()
  }, [searchOpen])

  const handleCatClick = (display) => {
    const apiName = CAT_MAP[display] || display
    onCategory(activeCategory === apiName ? null : apiName)
  }

  const isActive = (display) => {
    const apiName = CAT_MAP[display] || display
    return activeCategory === apiName
  }

  return (
    <header className="bg-white sticky top-0 z-50">
      {/* ── Utility bar ─────────────────────────────── */}
      <div className="border-b border-rule-DEFAULT" style={{ borderColor: '#E5E7EB' }}>
        <div className="max-w-site mx-auto px-4 sm:px-6 h-8 flex items-center justify-between">
          <p className="font-ui text-[11px] text-ink-muted">{dateStr}</p>
          <div className="hidden sm:flex items-center gap-4">
            <span className="font-ui text-[11px] text-ink-muted">AI-Powered News Intelligence</span>
            <span className="text-rule-bold">|</span>
            <button className="font-ui text-[11px] text-ink-muted hover:text-ink transition-colors">Subscribe</button>
            <span className="text-rule-bold">|</span>
            <button className="font-ui text-[11px] text-ink-muted hover:text-ink transition-colors">Sign In</button>
          </div>
        </div>
      </div>

      {/* ── Logo row ────────────────────────────────── */}
      <div className="border-b-2" style={{ borderColor: '#111827' }}>
        <div className="max-w-site mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 shrink-0" onClick={() => onCategory(null)}>
            <div className="w-7 h-7 flex items-center justify-center" style={{ background: '#111827' }}>
              <span className="font-ui font-bold text-white text-xs">P</span>
            </div>
            <span className="font-display font-bold text-xl text-ink" style={{ letterSpacing: '-0.01em' }}>
              PulseWire
            </span>
          </Link>

          {/* Right: search icon */}
          <div className="flex items-center gap-3">
            {searchOpen ? (
              <div className="flex items-center gap-2 animate-fade-in">
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Search articles…"
                  value={searchQuery}
                  onChange={e => onSearch(e.target.value)}
                  className="input-field w-56 sm:w-72"
                />
                <button
                  onClick={() => { setSearchOpen(false); onSearch('') }}
                  className="font-ui text-ink-muted hover:text-ink text-lg leading-none transition-colors"
                >×</button>
              </div>
            ) : (
              <button
                onClick={() => setSearchOpen(true)}
                aria-label="Search"
                className="text-ink-muted hover:text-ink transition-colors p-1"
              >
                <svg className="w-4.5 h-4.5 w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24"
                  stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Category nav strip ───────────────────────── */}
      <div className="border-b" style={{ borderColor: '#E5E7EB' }}>
        <div className="max-w-site mx-auto px-4 sm:px-6">
          <nav className="flex items-center gap-0 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
            <button
              onClick={() => onCategory(null)}
              className={`nav-link mr-6 ${!activeCategory ? 'active' : ''}`}
            >All</button>
            {NAV_CATS.map(cat => (
              <button
                key={cat}
                onClick={() => handleCatClick(cat)}
                className={`nav-link mr-6 ${isActive(cat) ? 'active' : ''}`}
              >{cat}</button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  )
}

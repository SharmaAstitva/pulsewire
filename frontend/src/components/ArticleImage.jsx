import { useState } from 'react'

// One deep tone per topic, so image-less stories still read as a deliberate tile.
const TOPIC_TONES = {
  'World News':  '#334155',
  Politics:      '#7F1D1D',
  Technology:    '#1E3A8A',
  Finance:       '#14532D',
  Science:       '#4C1D95',
  Health:        '#115E59',
  Sports:        '#9A3412',
  Entertainment: '#831843',
}

/* Article photo, or a topic-coloured placeholder when there is none or it fails to load. */
export function ArticleImage({ article, className = '', showLabel = true }) {
  const [failed, setFailed] = useState(false)

  if (article.image_url && !failed) {
    return (
      <img
        src={article.image_url}
        alt={article.title}
        loading="lazy"
        className={className}
        onError={() => setFailed(true)}
      />
    )
  }

  const tone = TOPIC_TONES[article.topic_primary] || TOPIC_TONES['World News']
  return (
    <div
      role="img"
      aria-label={article.title}
      className={`${className} flex items-center justify-center text-white`}
      style={{ background: `linear-gradient(135deg, ${tone} 0%, #0B0F19 100%)` }}
    >
      {showLabel && (
        <span className="font-display italic text-2xl opacity-90 px-4 text-center">
          {article.source || 'PulseWire'}
        </span>
      )}
    </div>
  )
}

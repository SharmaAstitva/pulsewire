/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body:    ['"Source Serif 4"', 'Georgia', 'serif'],
        ui:      ['"Inter"', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          DEFAULT: '#0F172A',   // deep navy-black (logo bg, footer bg)
          soft:    '#1E293B',
        },
        ink: {
          DEFAULT: '#111827',
          soft:    '#374151',
          muted:   '#6B7280',
          faint:   '#9CA3AF',
          light:   '#D1D5DB',
        },
        paper: {
          DEFAULT: '#FFFFFF',
          warm:    '#F9FAFB',
          tint:    '#F3F4F6',
        },
        accent: {
          DEFAULT: '#111827',   // black accent for active states
          red:     '#B91C1C',
        },
        sentiment: {
          positive: '#16A34A',
          neutral:  '#D97706',
          negative: '#DC2626',
          pos_bg:   '#DCFCE7',
          neu_bg:   '#FEF9C3',
          neg_bg:   '#FEE2E2',
        },
        rule: {
          DEFAULT: '#E5E7EB',
          bold:    '#D1D5DB',
        },
      },
      fontSize: {
        '2xs': ['0.625rem', '0.875rem'],
        '3xl': ['1.875rem', '2.25rem'],
        '4xl': ['2.25rem',  '2.6rem'],
        '5xl': ['3rem',     '3.4rem'],
      },
      maxWidth: { site: '1200px' },
      lineHeight: { snug: '1.25', heading: '1.15' },
    },
  },
  plugins: [],
}

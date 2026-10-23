/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#1E2B23',
          soft: '#37473C',
          faint: '#6B7A6E',
        },
        paper: {
          DEFAULT: '#EEF0E7',
          card: '#F9FAF4',
          raised: '#FFFFFF',
        },
        line: {
          DEFAULT: '#D9DBCE',
          soft: '#E3E4D8',
        },
        brass: {
          DEFAULT: '#B8923F',
          soft: '#E7D4A5',
          deep: '#8F701F',
        },
        tier: {
          excellent: '#2F6F62',
          good: '#6B8E4E',
          pass: '#4C6B8A',
          fail: '#B4453A',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      boxShadow: {
        ledger: '0 1px 0 0 rgba(30,43,35,0.06)',
        card: '0 2px 10px -4px rgba(30,43,35,0.15)',
      },
      borderRadius: {
        stamp: '999px',
      },
    },
  },
  plugins: [],
}

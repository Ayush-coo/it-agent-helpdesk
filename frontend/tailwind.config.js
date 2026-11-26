/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#050811',
        panel: 'rgba(4, 10, 20, 0.62)',
        'panel-border': 'rgba(255, 255, 255, 0.1)',
        armin: '#8bd4ff',
        'armin-hover': '#9ff3e7',
      },
      fontFamily: {
        sans: ['"Segoe UI"', '"Helvetica Neue"', 'Arial', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: 1, boxShadow: '0 0 10px rgba(139, 212, 255, 0.5)' },
          '50%': { opacity: .5, boxShadow: '0 0 20px rgba(139, 212, 255, 0.8)' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

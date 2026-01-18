/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./App.tsx",
    "./main.tsx",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./services/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: '#030305',
        obsidian: '#0a0a0f',
        graphite: '#12121a',
        carbon: '#1a1a25',
        surface: '#1e293b',
        primary: '#3b82f6',
        cyan: {
          DEFAULT: '#00f0ff',
          dim: '#00b8c5',
          glow: 'rgba(0, 240, 255, 0.15)',
        },
        magenta: {
          DEFAULT: '#ff00aa',
          dim: '#c5007f',
          glow: 'rgba(255, 0, 170, 0.15)',
        },
        lime: '#b8ff00',
        amber: '#ffb800',
        coral: '#ff6b6b',
      },
      fontFamily: {
        sans: ['Outfit', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
        display: ['Outfit', 'sans-serif'],
      },
      animation: {
        'slide-up': 'slideUp 0.6s ease-out forwards',
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 10px rgba(0, 240, 255, 0.15)' },
          '50%': { opacity: '0.7', boxShadow: '0 0 30px rgba(0, 240, 255, 0.3)' },
        },
      },
    },
  },
  plugins: [],
}
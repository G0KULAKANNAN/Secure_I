/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#070a0f',
          900: '#0a0e17',
          850: '#0f1422',
          800: '#141b2d',
          750: '#1a233a',
          700: '#212d4a',
        },
        cyan: {
          400: '#38bdf8',
          500: '#00f0ff',
          600: '#0284c7',
        },
        violet: {
          500: '#8a2be2',
          600: '#7c3aed',
        },
        emerald: {
          400: '#34d399',
          500: '#10b981',
        },
        amber: {
          400: '#fbbf24',
          500: '#f59e0b',
        },
        rose: {
          500: '#f43f5e',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}

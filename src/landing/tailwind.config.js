/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // System font stacks: no network fetch at build time, fast first paint.
        display: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        body: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        selph: {
          violet: '#7C3AED',
          purple: '#9333EA',
          sky: '#0EA5E9',
          emerald: '#10B981',
          coral: '#F43F5E',
          cloud: '#F5F3FF',
          mist: '#F0F9FF',
          title: '#0F172A',
          body: '#334155',
          muted: '#475569',
        },
      },
    },
  },
  plugins: [],
}

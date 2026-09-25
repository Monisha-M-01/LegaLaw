/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#FAF7FF',
        ink: '#1E1B29',
        accent: '#5B3DF5',
        safe: '#C9EFD8',
        caution: '#FFE3A3',
        flag: '#FFC9C9',
        muted: '#8A8594'
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Noto Sans Kannada"', '"Noto Sans Tamil"', '"Noto Sans Telugu"', '"Noto Sans Malayalam"', '"Noto Sans Devanagari"', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
      },
      boxShadow: {
        'hard': '3px 3px 0px 0px rgba(30, 27, 41, 1)',
        'hard-sm': '2px 2px 0px 0px rgba(30, 27, 41, 1)',
      },
      keyframes: {
        'slide-up': {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0)' },
        }
      },
      animation: {
        'slide-up': 'slide-up 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }
    },
  },
  plugins: [],
}

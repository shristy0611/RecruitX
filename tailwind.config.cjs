/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './**/*.{html,js,jsx,ts,tsx}',
  ],
  darkMode: 'class', 
  theme: {
    extend: {
      colors: {
        primary: { 
          light: '#5D9BFF',   // Brighter blue for highlights
          DEFAULT: '#3B71F6', // Main action blue
          dark: '#2A59C4',    // Darker blue for active/hover states
          text: '#A3C5FF',    // Blue for text links on dark backgrounds
          glow: 'rgba(59, 113, 246, 0.4)', // For subtle glows around primary elements
        },
        accent: { // Vibrant Teal for secondary highlights and data emphasis
          light: '#4FD1C5',   // teal-400
          DEFAULT: '#38B2AC', // teal-500
          dark: '#319795',    // teal-600
          text: '#81E6D9',    // teal-200 
        },
        success: { 
            DEFAULT: '#10b981', // emerald-500
            text: '#a7f3d0',    // emerald-200
            border: '#059669',  // emerald-600
            bg: 'bg-emerald-500',
            textDarkBg: 'text-emerald-400'
        },
        warning: { 
            DEFAULT: '#f59e0b', // amber-500
            text: '#fde68a',    // amber-200
            border: '#d97706',  // amber-600
            bg: 'bg-amber-500',
            textDarkBg: 'text-amber-400'
        },
        danger: { 
            DEFAULT: '#ef4444', // red-500
            text: '#fca5a5',    // red-300
            border: '#dc2626',  // red-600
            bg: 'bg-red-500',
            textDarkBg: 'text-red-400'
        },
        neutral: { // "Luminous Depths" Palette
          50: '#F8FAFC',   // slate-50 (very light gray, for light mode if ever needed)
          100: '#F1F5F9',  // slate-100
          200: '#E2E8F0',  // slate-200 (light text on dark)
          300: '#CBD5E1',  // slate-300 (standard text on dark)
          400: '#94A3B8',  // slate-400 (muted text)
          500: '#64748B',  // slate-500
          600: '#475569',  // slate-600 (borders, subtle elements)
          700: '#334155',  // slate-700 (interactive element backgrounds, card borders)
          800: '#1E293B',  // slate-800 (card/section backgrounds)
          850: '#111827',  // gray-900 equivalent (primary surface color for depth)
          900: '#0B0F19',  // Near-black (main body background)
          950: '#01020A',  // Deepest black with a hint of blue/purple (for gradients/accents)
        }
      },
      animation: {
        'text-gradient': 'text-gradient 3s linear infinite alternate',
        'pulse-strong': 'pulse-strong 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in-out-scale': 'fade-in-out-scale 2s ease-in-out forwards',
        'checkmark-draw': 'checkmark-draw 0.5s ease-out 0.3s forwards',
      },
      keyframes: {
        'text-gradient': {
          '0%': { backgroundPosition: '0% center' },
          '100%': { backgroundPosition: '150% center' }, 
        },
        'pulse-strong': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '.7', transform: 'scale(1.03)' },
        },
        'fade-in-out-scale': {
          '0%': { opacity: '0', transform: 'scale(0.8)' },
          '20%': { opacity: '1', transform: 'scale(1.05)' },
          '30%': { opacity: '1', transform: 'scale(1)' },
          '80%': { opacity: '1', transform: 'scale(1)' },
          '100%': { opacity: '0', transform: 'scale(0.7)' },
        },
        'checkmark-draw': {
          '0%': { strokeDashoffset: '48' },
          '100%': { strokeDashoffset: '0' },
        },
      },
      boxShadow: { // Refined shadows for dark theme
        'md-dark': '0 4px 6px -1px rgba(0, 0, 0, 0.25), 0 2px 4px -1px rgba(0, 0, 0, 0.15)',
        'lg-dark': '0 10px 15px -3px rgba(0, 0, 0, 0.25), 0 4px 6px -2px rgba(0, 0, 0, 0.15)',
        'xl-dark': '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
        '2xl-dark': '0 25px 50px -12px rgba(0, 0, 0, 0.4)',
        'inner-dark': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.2)',
        'primary-glow': '0 0 15px 2px rgba(59, 113, 246, 0.4)', // Example for primary color glow
        'accent-glow': '0 0 15px 2px rgba(56, 178, 172, 0.4)', // Example for accent color glow
      },
      typography: (theme) => ({
        DEFAULT: { 
          css: {
            color: theme('colors.neutral.300'), // slate-300
            a: {
              color: theme('colors.primary.text'), // new primary.text
              '&:hover': {
                color: theme('colors.primary.light'),
              },
            },
            strong: { color: theme('colors.neutral.100') }, // slate-100
            h1: { color: theme('colors.neutral.100') },
            h2: { color: theme('colors.neutral.100') },
            h3: { color: theme('colors.neutral.200') },
            h4: { color: theme('colors.neutral.200') },
            blockquote: {
              color: theme('colors.neutral.400'), // slate-400
              borderLeftColor: theme('colors.neutral.700'), // slate-700
            },
            'code::before': { content: '""' },
            'code::after': { content: '""' },
            code: { 
              color: theme('colors.accent.text'), // Using new accent.text (teal)
              backgroundColor: theme('colors.neutral.800'), // slate-800
              padding: '0.2em 0.4em',
              borderRadius: '0.25rem',
            },
             hr: { borderColor: theme('colors.neutral.700') }, // slate-700
          },
        },
      }),
    }
  },
  plugins: [],
} 
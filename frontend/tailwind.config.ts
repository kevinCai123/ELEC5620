import type { Config } from 'tailwindcss';
import forms from '@tailwindcss/forms';
import lineClamp from '@tailwindcss/line-clamp';
import typography from '@tailwindcss/typography';

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '1rem',
      screens: {
        lg: '1024px',
        xl: '1280px',
        '2xl': '1440px',
      },
    },
    extend: {
      fontFamily: {
        sans: ['"Inter var"', 'Inter', 'system-ui', 'sans-serif'],
        heading: ['"Geist Variable"', '"Inter var"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: '#6E7AFF',
          foreground: 'hsl(var(--primary-foreground))',
        },
        accent: {
          DEFAULT: '#22d3ee',
          foreground: 'hsl(var(--accent-foreground))',
        },
        glass: 'var(--glass)',
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'hsl(var(--muted-foreground))',
        },
      },
      borderRadius: {
        lg: '0.75rem',
        xl: '16px',
        '2xl': '24px',
        pill: '9999px',
      },
      boxShadow: {
        'glow-md': '0 10px 40px -10px rgba(0,0,0,0.55)',
        'glow-lg': '0 25px 80px -20px rgba(32,64,128,0.65)',
        'soft-inner': 'inset 0 1px 0 rgba(255,255,255,0.04)',
      },
      backgroundImage: {
        aurora: 'linear-gradient(130deg, rgba(110,122,255,0.9), rgba(168,85,247,0.75), rgba(34,211,238,0.75))',
        'noise-texture': 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'64\' height=\'64\' viewBox=\'0 0 64 64\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'1.2\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'64\' height=\'64\' filter=\'url(%23n)\' opacity=\'0.2\'/%3E%3C/svg%3E")',
      },
      keyframes: {
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        beam: {
          '0%': { transform: 'translateX(-40%) skewX(-15deg)', opacity: '0.0' },
          '30%': { opacity: '0.45' },
          '100%': { transform: 'translateX(140%) skewX(-15deg)', opacity: '0' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        gradient: 'gradient 6s ease infinite',
        beam: 'beam 10s ease-in-out infinite',
        'fade-in-up': 'fade-in-up 0.6s ease both',
      },
      dropShadow: {
        glow: '0 0 35px rgba(110,122,255,0.35)',
      },
      ringColor: {
        aurora: 'rgba(110,122,255,0.35)',
      },
      transitionTimingFunction: {
        aurora: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
      zIndex: {
        1: '1',
        5: '5',
        10: '10',
        20: '20',
        30: '30',
        40: '40',
        50: '50',
      },
    },
  },
  plugins: [forms, typography, lineClamp],
};

export default config;

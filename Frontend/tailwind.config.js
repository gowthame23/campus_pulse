/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary)',
        'primary-hover': 'var(--primary-hover)',
        campus: {
          ink: 'var(--ink)',
          muted: 'var(--muted)',
          page: 'var(--page)',
          surface: 'var(--surface)',
          border: 'var(--border)',
          success: 'var(--success)',
          danger: 'var(--danger)',
          warning: 'var(--warning)',
          info: 'var(--info)',
          orange: 'var(--orange)',
        },
      },
      boxShadow: {
        sm: '0 2px 8px rgba(15, 23, 42, 0.04)',
        md: '0 8px 24px rgba(15, 23, 42, 0.06)',
        lg: '0 16px 48px rgba(15, 23, 42, 0.1)',
        soft: '0 16px 40px rgba(15, 23, 42, 0.08)',
      },
      borderRadius: {
        xl: '12px',
      },
    },
  },
  plugins: [],
};

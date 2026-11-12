/**
 * Tailwind de Chester's (spec 003). El CSS compilado se versiona en el repo.
 * Regenerarlo después de tocar clases en plantillas o en forms.py:
 *
 *   npx tailwindcss@3.4.17 -i assets/tailwind.css -o pedidos/static/pedidos/css/chesters.css --minify
 */
module.exports = {
  content: ['./pedidos/templates/**/*.html', './pedidos/forms.py'],
  theme: {
    extend: {
      colors: {
        // Tomados del logo: fondo crema y collar rojo de Chester.
        crema: { DEFAULT: '#F4E5D2', 50: '#FBF6EF', 100: '#F8EEE2', 200: '#F4E5D2', 300: '#E9D1B3' },
        collar: { 50: '#FEF2F2', 100: '#FDE3E2', 200: '#FBCBC9', 400: '#F26D69', 500: '#EF3B36', 600: '#D62828', 700: '#B21F1F', 800: '#8F1B1B' },
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Nunito', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
};

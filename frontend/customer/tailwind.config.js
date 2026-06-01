/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        tripoly: {
          primary: "#16a34a",
          accent: "#86efac",
          dark: "#10231d",
          surface: "#f8fafc",
        },
      },
    },
  },
  plugins: [],
};

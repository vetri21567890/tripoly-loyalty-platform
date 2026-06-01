/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: { colors: { admin: { primary: "#10231d", accent: "#16a34a", surface: "#f8fafc" } } } },
  plugins: [],
};

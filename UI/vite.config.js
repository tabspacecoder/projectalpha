import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path';



// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),tailwindcss()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        chat: resolve(__dirname, 'chat.html'),
      },
    },
  },
  extend: {
  animation: {
    'waving-hand': 'wave 1.6s ease-in-out infinite',
    'fade-in-down': 'fadeInDown 0.4s ease-out',
  },
  keyframes: {
    wave: {
      '0%': { transform: 'rotate(0deg)' },
      '10%': { transform: 'rotate(14deg)' },
      '20%': { transform: 'rotate(-8deg)' },
      '30%': { transform: 'rotate(14deg)' },
      '40%': { transform: 'rotate(-4deg)' },
      '50%': { transform: 'rotate(10deg)' },
      '60%': { transform: 'rotate(0deg)' },
      '100%': { transform: 'rotate(0deg)' },
    },
    fadeInDown: {
      '0%': { opacity: 0, transform: 'translateY(-10px)' },
      '100%': { opacity: 1, transform: 'translateY(0)' },
    },
  },
}
})

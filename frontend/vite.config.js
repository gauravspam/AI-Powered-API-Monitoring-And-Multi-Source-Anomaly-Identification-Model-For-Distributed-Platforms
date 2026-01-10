import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default {
  build: {
    outDir: 'dist'  // or 'build'
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify('http://localhost:8080')
  }
}


// https://vite.dev/config/
// export default defineConfig({
//   plugins: [react()],
//   resolve: {
//     alias: {
//       '@': path.resolve(__dirname, './src'),
//     },
//   },
//   build: {
//     rollupOptions: {
//       output: {
//         manualChunks: {
//           react: ['react', 'react-dom'],
//           router: ['react-router-dom'],
//           muiCore: ['@mui/material', '@mui/lab'],
//           muiIcons: ['@mui/icons-material'],
//           muiCharts: ['@mui/x-charts'],
//           muiDataGrid: ['@mui/x-data-grid']
//         }

//       }
//     }
//   }
// });


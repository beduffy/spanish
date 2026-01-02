const { defineConfig } = require('@vue/cli-service')
const path = require('path')
const fs = require('fs')

// Load .env from project root (parent of anki_web_app/spanish_anki_frontend)
// Vue CLI requires VUE_APP_ prefix, so we map root .env vars to VUE_APP_ vars
// Try multiple possible paths for .env file (works in both local dev and Docker)
const possibleEnvPaths = [
  path.resolve(__dirname, '../../.env'),  // From frontend dir: ../../.env
  path.resolve(__dirname, '../../../.env'), // Alternative path
  '/.env',  // Docker root mount
  path.resolve(process.cwd(), '../../.env'), // From working directory
]

let envFileRead = false
for (const rootEnvPath of possibleEnvPaths) {
  if (fs.existsSync(rootEnvPath)) {
    try {
      const envFile = fs.readFileSync(rootEnvPath, 'utf8')
      envFile.split('\n').forEach(line => {
        const trimmed = line.trim()
        if (trimmed && !trimmed.startsWith('#')) {
          const [key, ...valueParts] = trimmed.split('=')
          if (key && valueParts.length > 0) {
            const value = valueParts.join('=').trim().replace(/^["']|["']$/g, '')
            // Map SUPABASE_* vars to VUE_APP_SUPABASE_* for Vue CLI
            if (key.startsWith('SUPABASE_')) {
              process.env[`VUE_APP_${key}`] = value
            } else if (key.startsWith('VUE_APP_')) {
              process.env[key] = value
            }
          }
        }
      })
      envFileRead = true
      break
    } catch (error) {
      // Continue to next path
    }
  }
}

// Fallback: Also check environment variables directly (for Docker env_file)
// This allows docker-compose env_file to work as a fallback
if (!envFileRead) {
  if (process.env.SUPABASE_URL) {
    process.env.VUE_APP_SUPABASE_URL = process.env.SUPABASE_URL
  }
  if (process.env.SUPABASE_ANON_KEY) {
    process.env.VUE_APP_SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY
  }
  if (process.env.VUE_APP_SUPABASE_URL) {
    // Already set, keep it
  }
  if (process.env.VUE_APP_SUPABASE_ANON_KEY) {
    // Already set, keep it
  }
}

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8080, // This is the port the dev server will listen on INSIDE the container
    proxy: {
      '/api': { // Assuming your Django API URLs start with /api/
        target: 'http://backend:8000', // 'backend' is the service name in docker-compose.yml
        ws: true, // If you use websockets
        changeOrigin: true
      },
      '/media': { // Proxy media files (TTS audio, uploaded files) to Django backend
        target: 'http://backend:8000',
        ws: false,
        changeOrigin: true,
        secure: false,
        logLevel: 'debug'
      }
    }
  },
  chainWebpack: config => {
    config.plugin('define').tap(definitions => {
      Object.assign(definitions[0], {
        '__VUE_OPTIONS_API__': JSON.stringify(true),
        '__VUE_PROD_DEVTOOLS__': JSON.stringify(false),
        '__VUE_PROD_HYDRATION_MISMATCH_DETAILS__': JSON.stringify(true)
      });
      return definitions;
    });
  }
})

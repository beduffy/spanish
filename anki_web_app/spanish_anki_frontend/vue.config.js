const { defineConfig } = require('@vue/cli-service')
const path = require('path')
const fs = require('fs')

// Load .env from project root (parent of anki_web_app/spanish_anki_frontend)
// Vue CLI requires VUE_APP_ prefix, so we map root .env vars to VUE_APP_ vars
const rootEnvPath = path.resolve(__dirname, '../../.env')
if (fs.existsSync(rootEnvPath)) {
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

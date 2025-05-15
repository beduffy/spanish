const { defineConfig } = require('@vue/cli-service')
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

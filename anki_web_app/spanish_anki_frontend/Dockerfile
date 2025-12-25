# Stage 1: Development stage (for npm run serve)
FROM node:18-alpine as build-stage

WORKDIR /app

COPY package*.json ./

RUN npm install

# Don't build here - let npm run serve handle it in development
# The build step is only needed for production
COPY . .

# Default command (can be overridden in docker-compose.yml)
CMD ["npm", "run", "serve"]

# Stage 2: Production build stage
FROM node:18-alpine as production-build

WORKDIR /app

# Accept build arguments for Supabase configuration
ARG SUPABASE_URL
ARG SUPABASE_ANON_KEY

# Set as environment variables for the build process
ENV VUE_APP_SUPABASE_URL=${SUPABASE_URL}
ENV VUE_APP_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}

COPY package*.json ./

RUN npm install --production=false

COPY . .

RUN npm run build

# Stage 3: Production serve stage with Nginx
FROM nginx:stable-alpine as production

# Copy built assets from the build stage
COPY --from=production-build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"] 
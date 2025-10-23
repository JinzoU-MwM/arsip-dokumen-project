FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY ./src ./src
COPY ./tsconfig.json ./

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Change ownership of the app directory
RUN chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Start command
CMD ["node", "dist/index.js"]
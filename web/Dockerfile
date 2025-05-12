# -- RecruitX App Image --
FROM node:20-alpine AS base

# Enable pnpm
RUN corepack enable

WORKDIR /app

# Copy package files first to leverage Docker caching
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Generate Prisma client
RUN pnpm prisma generate

# Development image
FROM base AS dev
ENV NODE_ENV=development
CMD ["pnpm", "dev"]

# Production build image
FROM base AS builder
ENV NODE_ENV=production
RUN pnpm build

# Production runtime image
FROM node:20-alpine AS production
WORKDIR /app

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

ENV NODE_ENV=production
CMD ["node", "server.js"]

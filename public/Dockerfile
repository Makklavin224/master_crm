# Stage 1: Build
FROM node:20-alpine AS build
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf 'server {\n\
    listen 3002;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    # Static assets -- serve directly\n\
    location /assets/ {\n\
        try_files $uri =404;\n\
    }\n\
\n\
    # Master public pages -- SPA fallback\n\
    location /m/ {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
\n\
    # Client cabinet -- SPA fallback\n\
    location /my/ {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
\n\
    # Default fallback\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 3002
CMD ["nginx", "-g", "daemon off;"]

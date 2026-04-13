FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
ARG VITE_API_BASE=https://sismasens.iotzator.com/api
ARG VITE_WS_BASE=wss://sismasens.iotzator.com
RUN npm run build

FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

# Campus Pulse Frontend — Vite dev server
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# CLAUDE.md's documented run command is `npm run dev`, which runs
# `vite --host 127.0.0.1 --port 5173` (see package.json). 127.0.0.1 only
# binds the container's loopback interface, which the published port
# cannot reach from outside — so we invoke vite directly with
# --host 0.0.0.0 instead, keeping the same port.
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]

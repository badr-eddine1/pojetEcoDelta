# Emplacement : ecodelta_frontend/Dockerfile

# --- Étape 1 : build ---
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# VITE_API_URL n'est pas un secret : on le passe explicitement au build
# (le .env est exclu par .dockerignore, donc Vite ne le verrait pas sinon)
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Étape 2 : service des fichiers statiques ---
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

FROM node:18-alpine as build-stage

WORKDIR /app

# Install Dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy Source Code
COPY . .

RUN npm run build

# Serve
FROM nginx:stable-alpine as production-stage

# Copy the build output 
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy our custom Nginx config to handle the API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
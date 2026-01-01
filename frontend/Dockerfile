# Stage 1: Build the React app with Node.js
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve the static files with Nginx
FROM nginx:alpine
# Copy the built files from the 'builder' stage to the Nginx web directory
COPY --from=builder /app/dist /usr/share/nginx/html
# Expose port 80 to the host machine
EXPOSE 80
# Command to start Nginx
CMD ["nginx", "-g", "daemon off;"]

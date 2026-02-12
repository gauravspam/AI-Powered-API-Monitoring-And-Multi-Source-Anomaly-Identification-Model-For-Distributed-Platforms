FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
# REMOVED: RUN npm start  <-- This was the bug
EXPOSE 8082
CMD ["npm", "start"]

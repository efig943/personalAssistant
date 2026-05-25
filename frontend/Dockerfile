FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies first (leverage Docker cache)
COPY package*.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Expose the Vite default port
EXPOSE 5173

# Start the Vite development server bound to all interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

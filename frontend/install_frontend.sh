#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting Frontend Dependency Setup..."

# Ensure package.json exists
if [ ! -f "package.json" ]; then
    echo "No package.json found, creating default..."
    npm init -y
fi

# Install Runtime Dependencies
echo "Installing Core Libraries..."
npm install vue@^3.5 pinia@^2.2 axios@^1.7 @vueuse/core@^11 lucide-vue-next

# Install Development Dependencies
echo "Installing Build Tools & Plugins..."
npm install --save-dev @vitejs/plugin-vue vite @types/node

# Install the rest of the stack
npm install --save-dev typescript@^5 tailwindcss@^3 postcss autoprefixer vue-tsc

# Add the scripts to package.json
echo "Adding Scripts to package.json..."
npm pkg set scripts.dev="vite"
npm pkg set scripts.build="vue-tsc -b && vite build"
npm pkg set scripts.preview="vite preview"

# Initialize Tailwind Configuration
if [ ! -f "tailwind.config.js" ]; then
    echo "Initializing Tailwind CSS Config..."
    npx tailwindcss init -p
else
    echo "tailwind.config.js already exists, skipping init."
fi

echo "Installation Complete!"
echo "-------------------------------------------------------"
echo "To start the development server, run:"
echo "  npm run dev"
echo "-------------------------------------------------------"
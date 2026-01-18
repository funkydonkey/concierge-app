#!/bin/bash

# Setup script for Voice Notes Service

echo "🚀 Setting up Voice Notes Service..."

# Check if uv is installed
if ! command -v uv &> /dev/null
then
    echo "❌ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed!"
else
    echo "✅ uv already installed"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Create .env from example
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo "✅ .env already exists"
fi

# Create temp directory for audio files
mkdir -p temp_audio

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Complete the learning assignments in LEARNING.md"
echo "3. Run: uvicorn app.main:app --reload"
echo ""
echo "Happy coding! 🎓"

#!/bin/bash
# Simple script to start Kith Platform locally

echo "🚀 Starting Kith Platform Local Development..."
echo "📍 Make sure you're in the Spiderman-v3-main directory"
echo ""

# Check if we're in the right directory
if [ ! -d "kith-platform" ]; then
    echo "❌ Error: kith-platform directory not found!"
    echo "Please run this script from the Spiderman-v3-main directory"
    exit 1
fi

echo "✅ Found kith-platform directory"
echo "🔧 Starting Python server..."
echo ""

# Run the Python script
python3 start-kith-local.py

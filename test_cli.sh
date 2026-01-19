#!/bin/bash

# Quick test script for muncho CLI

echo "🧪 Testing muncho CLI tool"
echo ""

echo "1️⃣  Testing --help"
muncho --help
echo ""

echo "2️⃣  Listing profiles"
muncho profiles
echo ""

echo "3️⃣  Testing build --help"
muncho build --help
echo ""

echo "4️⃣  Testing with custom profiles"
muncho build --list-profiles --config example_profiles.yml
echo ""

echo "✅ All basic CLI tests passed!"

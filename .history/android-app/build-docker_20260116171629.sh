#!/bin/bash
# Script para compilar o APK usando Docker

echo "🐳 Compilando APK com Docker..."
echo "Isso pode demorar ~30 minutos na primeira vez."
echo ""

cd "$(dirname "$0")"

# Build da imagem Docker
docker build -t youtube-downloader-builder .

# Executa o build
docker run --rm \
    -v "$(pwd)":/app \
    -v "$(pwd)/.buildozer":/app/.buildozer \
    youtube-downloader-builder

echo ""
echo "✅ Build concluído!"
echo "📦 APK disponível em: bin/"
ls -la bin/*.apk 2>/dev/null || echo "❌ Nenhum APK encontrado. Verifique os logs acima."

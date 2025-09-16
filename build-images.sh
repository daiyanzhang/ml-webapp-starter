#!/bin/bash

# 构建自定义镜像脚本
# Usage: ./build-images.sh [--no-cache]

set -e

echo "🚀 Building custom Docker images for webapp-starter..."

# 检查是否传入 --no-cache 参数
NO_CACHE=""
if [[ "$1" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
    echo "📝 Building with --no-cache flag"
fi

# 确保在项目根目录
if [[ ! -f "docker-compose.dev.yml" ]]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# 创建 docker 目录（如果不存在）
mkdir -p docker

echo "📦 Building webapp-starter-jupyter image..."
docker build $NO_CACHE -f docker/Dockerfile.jupyter -t webapp-starter-jupyter:latest .

echo "ℹ️  Skipping Ray image build (using runtime installation)"
echo "   Ray services will install dependencies at startup"

echo "✅ All images built successfully!"
echo ""
echo "📋 Built images:"
docker images | grep webapp-starter
echo ""
echo "🎯 Next steps:"
echo "1. Run: docker-compose -f docker-compose.dev.yml up -d"
echo "2. Your services will now use the pre-built images with dependencies"
echo ""
echo "💡 To rebuild images when dependencies change:"
echo "   ./build-images.sh --no-cache"
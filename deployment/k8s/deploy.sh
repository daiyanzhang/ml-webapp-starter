#!/bin/bash

# Kubernetes部署脚本

echo "部署 Web App Starter 到 Kubernetes..."

# 创建命名空间
kubectl apply -f namespace.yaml

# 部署PostgreSQL
echo "部署 PostgreSQL..."
kubectl apply -f postgres.yaml

# 等待PostgreSQL就绪
echo "等待 PostgreSQL 就绪..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n webapp-starter

# 部署后端
echo "部署后端服务..."
kubectl apply -f backend.yaml

# 等待后端就绪
echo "等待后端服务就绪..."
kubectl wait --for=condition=available --timeout=300s deployment/backend -n webapp-starter

# 部署前端
echo "部署前端服务..."
kubectl apply -f frontend.yaml

# 等待前端就绪
echo "等待前端服务就绪..."
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n webapp-starter

echo "部署完成！"
echo "请确保已配置 DNS 或 hosts 文件指向 webapp-starter.local"
echo "或者使用端口转发："
echo "kubectl port-forward svc/frontend-service 3000:80 -n webapp-starter"
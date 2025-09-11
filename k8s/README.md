# Kubernetes Development Environment with minikube

本目录包含将整个webapp-starter应用部署到minikube的Kubernetes配置，实现真正的资源隔离和Ray队列管理。

## 🏗️ 架构设计

### Ray集群架构
```
minikube集群 (4节点)
├── Node1 (Head节点)
│   └── ray-head (Dashboard + GCS)
├── Node2 (Default队列)
│   └── ray-worker-default (通用任务)
├── Node3 (CPU队列)  
│   └── ray-worker-cpu (CPU密集型任务)
└── Node4 (Memory/GPU队列)
    ├── ray-worker-memory (高内存任务)
    └── ray-worker-gpu (GPU任务)
```

### 应用程序架构
```
webapp-starter namespace
├── postgres (数据库)
├── webapp-backend (API服务)
└── webapp-frontend (React应用)
```

## 🚀 快速开始

### 1. 安装依赖
```bash
# macOS
brew install minikube
brew install kubectl

# 验证安装
minikube version
kubectl version --client
```

### 2. 启动Ray集群
```bash
# 启动minikube并部署Ray集群
./k8s/minikube-setup.sh
```

### 3. 部署应用程序
```bash
# 构建镜像并部署应用
./k8s/deploy-webapp.sh
```

### 4. 访问服务
```bash
# 获取服务URL
minikube service webapp-frontend -n webapp-starter --url
minikube service ray-dashboard -n ray-system --url

# 或使用端口转发
kubectl port-forward -n webapp-starter svc/webapp-frontend 3000:3000
kubectl port-forward -n ray-system svc/ray-dashboard 8265:8265
```

## 📊 资源管理对比

### Docker Compose vs minikube

| 特性 | Docker Compose | minikube K8s |
|-----|----------------|--------------|
| 资源隔离 | 容器级别 | 节点+Pod级别 |
| 资源限制 | 软限制 | 硬限制 |
| 调度 | 无调度 | K8s调度器 |
| 扩展性 | 单机 | 多节点模拟 |
| 故障恢复 | 手动重启 | 自动重启 |
| 服务发现 | 容器名 | K8s服务 |
| 配置管理 | 环境变量 | ConfigMap/Secret |

### Ray Worker资源配置

```yaml
# CPU队列节点
ray-worker-cpu:
  resources:
    requests: {cpu: "2", memory: "4Gi"}
    limits: {cpu: "4", memory: "8Gi"}
  ray_resources: {"queue_cpu": 1}

# Memory队列节点  
ray-worker-memory:
  resources:
    requests: {cpu: "2", memory: "8Gi"}
    limits: {cpu: "4", memory: "16Gi"}
  ray_resources: {"queue_memory": 1, "CPU": 4, "memory": 17179869184}

# GPU队列节点
ray-worker-gpu:
  resources:
    requests: {cpu: "4", memory: "8Gi"}
    limits: {cpu: "8", memory: "16Gi"}
  ray_resources: {"queue_gpu": 1, "CPU": 8, "GPU": 1}
```

## 🔧 管理命令

### 集群管理
```bash
# 查看集群状态
kubectl get nodes --show-labels
kubectl get pods -A

# 查看Ray集群状态
kubectl get pods -n ray-system
kubectl logs -n ray-system deployment/ray-head

# 查看应用状态
kubectl get pods -n webapp-starter
kubectl logs -n webapp-starter deployment/webapp-backend
```

### 资源监控
```bash
# 查看资源使用
kubectl top nodes
kubectl top pods -n ray-system
kubectl top pods -n webapp-starter

# 查看资源配额
kubectl describe quota -n ray-system
kubectl describe quota -n webapp-starter
```

### 调试命令
```bash
# 进入容器调试
kubectl exec -it -n ray-system deployment/ray-head -- bash
kubectl exec -it -n webapp-starter deployment/webapp-backend -- bash

# 端口转发调试
kubectl port-forward -n webapp-starter svc/webapp-backend 8000:8000
kubectl port-forward -n ray-system svc/ray-head 6379:6379
```

## 🎯 Ray任务调度验证

### 测试不同队列调度
```python
# 提交到不同队列的任务会被调度到对应的worker节点
# 通过Ray Dashboard可以看到任务分布

# Default队列任务
job1 = {"queue": "default", "github_repo": "example/simple-task"}

# CPU队列任务  
job2 = {"queue": "cpu", "github_repo": "example/cpu-intensive"}

# Memory队列任务
job3 = {"queue": "memory", "github_repo": "example/memory-heavy"}

# GPU队列任务
job4 = {"queue": "gpu", "github_repo": "example/ml-training"}
```

### 验证资源隔离
1. 提交CPU密集型任务到CPU队列
2. 同时提交内存密集型任务到Memory队列  
3. 通过 `kubectl top pods` 观察资源使用
4. 通过Ray Dashboard观察任务分布

## 🛠️ 故障排除

### 常见问题

1. **minikube启动失败**
   ```bash
   minikube delete && minikube start --driver=docker
   ```

2. **镜像拉取失败**  
   ```bash
   eval $(minikube docker-env)
   # 重新构建本地镜像
   ```

3. **资源不足**
   ```bash
   minikube start --cpus=8 --memory=16384
   ```

4. **Ray集群连接失败**
   ```bash
   kubectl logs -n ray-system deployment/ray-head
   kubectl port-forward -n ray-system svc/ray-head 8265:8265
   ```

### 清理环境
```bash
# 删除应用
kubectl delete namespace webapp-starter

# 删除Ray集群
kubectl delete namespace ray-system  

# 完全清理minikube
minikube delete
```

## 🔄 从Docker Compose迁移

1. **停止Docker Compose服务**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

2. **启动minikube环境**
   ```bash
   ./k8s/minikube-setup.sh
   ./k8s/deploy-webapp.sh
   ```

3. **更新开发工作流**
   - 使用 `kubectl` 替代 `docker-compose`
   - 使用K8s服务名替代容器名
   - 使用 `minikube service` 访问服务

## 📈 生产环境考虑

将此配置应用到真实K8s集群时需要考虑：

1. **GPU节点**：添加真实GPU资源和NVIDIA device plugin
2. **存储**：使用持久卷存储数据库数据  
3. **网络**：配置Ingress和负载均衡
4. **安全**：添加RBAC和网络策略
5. **监控**：集成Prometheus和Grafana
6. **扩展**：配置HPA和VPA
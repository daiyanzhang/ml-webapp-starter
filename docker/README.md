# Docker 自定义镜像

本目录包含用于构建预装依赖的自定义 Docker 镜像的配置文件。

## 🎯 镜像策略

### 混合镜像配置
- **Jupyter**: 自定义镜像（性能优化）
- **Ray**: 原始镜像 + 运行时安装（兼容性优化）

## 📦 镜像说明

### webapp-starter-jupyter
- **基础镜像**: `jupyter/minimal-notebook:latest`
- **预装内容**:
  - ✅ Ray 2.30.0 及所有依赖
  - ✅ IPython 和 Jupyter 完整套件
  - ✅ NumPy, Pandas 等数据科学库
  - ✅ webapp-starter-utils 工具包
- **特性**:
  - 🚀 快速启动（10-20秒 vs 2-3分钟）
  - 🔒 免登录访问
  - 📦 依赖预装，避免ModuleNotFoundError
  - 🔄 与 Ray 集群无缝集成

### Ray 服务（运行时安装）
- **基础镜像**: `rayproject/ray:2.30.0-py39`
- **依赖管理**: 容器启动时安装
- **优势**:
  - 🔧 平台兼容性（M1/M2 Mac 支持）
  - 🔄 灵活的依赖管理
  - 📏 镜像体积较小

## 🏗️ 构建镜像

### 快速构建
```bash
# 在项目根目录运行
./build-images.sh
```

### 完整重建
```bash
# 清除缓存重新构建（依赖更新后）
./build-images.sh --no-cache
```

### 手动构建
```bash
# 仅构建 Jupyter 镜像
docker build -f docker/Dockerfile.jupyter -t webapp-starter-jupyter:latest .

# 检查构建结果
docker images | grep webapp-starter
```

## 🚀 使用方法

### 开发环境启动
```bash
# 构建镜像
./build-images.sh

# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 验证服务状态
docker ps --filter name=webapp-starter
```

### 测试镜像功能
```bash
# 测试 Jupyter 镜像中的 utils 包
docker run --rm webapp-starter-jupyter:latest python -c "
from utils.direct_ray_magic import load_direct_ray_magic;
print('✅ Utils package works!')
"

# 测试 Ray 版本
docker run --rm webapp-starter-jupyter:latest python -c "
import ray;
print(f'✅ Ray version: {ray.__version__}')
"
```

## 🔄 依赖更新流程

### 1. 更新依赖文件
```bash
# 编辑依赖
vim notebooks/requirements.txt
vim notebooks/setup.py
```

### 2. 重新构建
```bash
# 强制重建
./build-images.sh --no-cache
```

### 3. 重启服务
```bash
# 停止并重启
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

## 📊 性能对比

| 指标 | 原始配置 | 优化后配置 |
|------|----------|------------|
| Jupyter 启动时间 | 2-3 分钟 | 10-20 秒 |
| 依赖安装错误 | 经常出现 | 完全消除 |
| 网络依赖 | 每次启动需要 | 仅构建时需要 |
| 开发体验 | 等待时间长 | 即时可用 |

## 🏭 生产环境部署

### 镜像仓库推送
```bash
# 标签化版本
docker tag webapp-starter-jupyter:latest your-registry.com/webapp-starter-jupyter:v1.0.0

# 推送到仓库
docker push your-registry.com/webapp-starter-jupyter:v1.0.0
```

### CI/CD 集成
```yaml
# .github/workflows/build.yml 示例
- name: Build and Push Images
  run: |
    ./build-images.sh --no-cache
    docker tag webapp-starter-jupyter:latest ${{ secrets.REGISTRY }}/webapp-starter-jupyter:${{ github.sha }}
    docker push ${{ secrets.REGISTRY }}/webapp-starter-jupyter:${{ github.sha }}
```

### 生产配置
```yaml
# docker-compose.prod.yml
services:
  jupyterhub:
    image: your-registry.com/webapp-starter-jupyter:v1.0.0
    # 其他生产配置...
```

## 🔧 故障排除

### 常见问题

**Q: 构建失败，权限错误**
```bash
# 解决方案：确保 Docker 有足够权限
sudo usermod -aG docker $USER
# 重新登录后重试
```

**Q: M1/M2 Mac 平台问题**
```bash
# 解决方案：指定平台构建
docker build --platform linux/amd64 -f docker/Dockerfile.jupyter -t webapp-starter-jupyter:latest .
```

**Q: 镜像体积过大**
```bash
# 查看镜像层级
docker history webapp-starter-jupyter:latest

# 清理未使用镜像
docker image prune -f
```

### 调试命令
```bash
# 进入容器调试
docker run -it --rm webapp-starter-jupyter:latest bash

# 查看安装的包
docker run --rm webapp-starter-jupyter:latest pip list

# 检查工作目录
docker run --rm webapp-starter-jupyter:latest ls -la /home/jovyan/work/
```

## 📝 最佳实践

1. **版本管理**: 使用语义化版本标签
2. **安全扫描**: 定期扫描镜像漏洞
3. **体积优化**: 使用多阶段构建
4. **缓存利用**: 合理安排 Dockerfile 层级
5. **文档同步**: 及时更新依赖文档

## 📚 相关文档

- [Docker 最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [多阶段构建](https://docs.docker.com/develop/multistage-build/)
- [镜像安全扫描](https://docs.docker.com/engine/scan/)
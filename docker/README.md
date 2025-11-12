# Docker 部署指南

本目录包含 Docker 部署相关的配置文件。

## 📁 文件说明

### 核心配置文件

- **`docker-compose.yml`** - Docker Compose 配置文件
  - 从 Docker Hub 拉取预构建镜像
  - 无需本地构建，快速部署
  - 使用方法：`docker compose up -d`

### 构建文件

- **`Dockerfile.backend`** - 后端镜像构建文件
- **`Dockerfile.frontend`** - 前端镜像构建文件
- **`nginx.conf`** - Nginx 配置文件
- **`backend-entrypoint.sh`** - 后端容器启动脚本

## 🚀 快速开始

### 启动服务

```bash
cd docker
docker compose up -d
```

首次运行会从 Docker Hub 拉取镜像，可能需要几分钟（取决于网络速度）。

### 访问应用

启动成功后，访问：
- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 📋 常用命令

### 查看服务状态

```bash
docker compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 停止服务

```bash
# 停止服务（保留数据）
docker compose down

# 停止服务并删除数据卷（谨慎使用）
docker compose down -v
```

### 重启服务

```bash
# 重启服务
docker compose restart

# 重新拉取镜像并启动
docker compose pull
docker compose up -d
```

## 🔧 配置端口

可以通过环境变量配置端口：

```bash
# 方式 1：在命令行指定
FRONTEND_PORT=8080 BACKEND_PORT=8001 docker compose up -d

# 方式 2：创建 .env 文件
echo "FRONTEND_PORT=8080" > .env
echo "BACKEND_PORT=8001" >> .env
docker compose up -d
```

## ⚙️ 配置 API 密钥

1. 首次启动后，系统会自动从 `.env.example` 创建 `.env` 文件
2. 访问前端界面：http://localhost:5173
3. 在左侧导航栏点击"环境配置"
4. 在"🤖 模型与API配置"分组中，填入您的 `DASHSCOPE_API_KEY`
5. 点击"💾 保存配置"按钮

## 📦 数据持久化

所有数据（包括 `.env` 配置、历史记录、用户数据、日志）都保存在 Docker Volume 中，即使删除容器也不会丢失。

数据卷说明：
- `arxiv_history` - 论文历史记录
- `user_data` - 用户配置和数据（包括 `.env` 文件）
- `logs` - 应用日志

## ❓ 常见问题

### Q: 如何更新到新版本？

**A:** 
```bash
# 拉取最新镜像
docker compose pull

# 重启服务
docker compose up -d
```

### Q: 数据会丢失吗？

**A:** 不会。所有数据都保存在 Docker Volume 中，即使删除容器也不会丢失。只有使用 `docker compose down -v` 才会删除数据卷。

### Q: 如何查看容器日志？

**A:** 
```bash
# 查看所有日志
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail=100
```

### Q: 端口被占用怎么办？

**A:** 可以通过环境变量修改端口：
```bash
FRONTEND_PORT=8080 BACKEND_PORT=8001 docker compose up -d
```

### Q: 如何完全重置？

**A:** 
```bash
# 停止服务并删除所有数据（谨慎使用）
docker compose down -v

# 重新启动
docker compose up -d
```

## 🔗 相关链接

- [主项目 README](../README.md)

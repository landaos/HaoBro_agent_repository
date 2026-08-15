# 部署说明

此目录包含生产环境部署所需的配置文件。

## 目录结构

```
deploy/
├── nginx.conf          # Nginx 反向代理配置（HTTPS + 限流）
├── supervisor.conf     # Supervisor 进程管理配置（非容器部署）
└── ssl/                # SSL 证书存放目录（.gitignore 中忽略）
```

## 部署方式

### 方案 A：Docker Compose（推荐）

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动（PostgreSQL + Redis + 后端）
docker-compose up -d

# 3. 数据库迁移
docker-compose exec backend alembic upgrade head
```

### 方案 B：裸机部署（无 Docker）

```bash
# 1. 安装依赖
pip install -e ".[dev]"

# 2. 启动 uvicorn（通过 supervisor 管理）
# 详见 supervisor.conf 配置
```

## 安全注意事项

1. **.env 文件**：不要提交到 Git，生产环境的密钥通过 CI/CD 环境变量注入
2. **SSL 证书**：使用 Let's Encrypt 免费证书，每 90 天自动续期
3. **防火墙**：只开放 443（HTTPS）和 22（SSH）端口
4. **日志**：生产环境日志按天轮转，保留 30 天

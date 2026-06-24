# Billing Alert System - Linux 部署文档

## 1. 环境准备

在开始部署之前，请确保 Linux 服务器（如 Ubuntu/CentOS）已安装以下基础环境：
- **Python 3.9+** (用于运行 FastAPI 后端)
- **Node.js 18+ & npm** (用于构建 React 前端)
- **PostgreSQL** (项目当前配置指向 `192.168.200.124:5432`，若使用外部数据库则无需在本地安装)
- **Nginx** (用于提供前端静态文件服务)
- **Git** (用于拉取代码)

## 2. 后端部署 (Backend)

后端采用 FastAPI 框架，使用 Uvicorn 作为 ASGI 服务器。

### 2.1 进入后端目录并配置虚拟环境
```bash
cd /path/to/Billing_Alert/backend

# 创建 Python 虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 2.2 安装依赖
```bash
# 安装 requirements.txt 中的依赖
pip install -r requirements.txt

# 注意：代码中使用了 PostgreSQL，但 requirements.txt 中未包含驱动，需要手动补充安装
pip install psycopg2-binary
```

### 2.3 配置文件与凭证准备
1. **数据库配置**：检查 `database.py` 和 `init_db_partitions.py` 中的数据库连接信息（当前硬编码为 `192.168.200.124`，用户 `postgres`）。如需更改，请直接修改这两个文件。
2. **GCP 凭证**：确保 `backend/credentials.json` 文件存在且包含有效的 Google Cloud BigQuery 访问凭证。

### 2.4 初始化数据库
项目使用了 PostgreSQL 的表分区功能，首次部署需要执行初始化脚本：
```bash
python init_db_partitions.py
```
*(该脚本会清理旧的 `daily_usage` 表并按月创建 2024-2027 年的分区表)*

### 2.5 启动后端服务
推荐使用 `systemd` 或 `nohup` / `tmux` 在后台运行后端服务。
**使用 nohup 启动示例：**
```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```
*(后端服务将运行在 `8000` 端口，请确保服务器防火墙已放行该端口)*

---

## 3. 前端部署 (Frontend)

前端采用 React + Vite 构建，部署时需要先编译成静态文件。

### 3.1 进入前端目录并安装依赖
```bash
cd /path/to/Billing_Alert/frontend

# 安装 Node.js 依赖
npm install
```

### 3.2 构建生产环境代码
```bash
npm run build
```
构建完成后，会在 `frontend` 目录下生成一个 `dist` 文件夹，里面包含了所有需要部署的静态资源。

---

## 4. Nginx 配置 (Web 服务器)

使用 Nginx 来托管前端的 `dist` 静态文件。

### 4.1 安装 Nginx
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 4.2 配置 Nginx
创建或修改 Nginx 配置文件（例如 `/etc/nginx/sites-available/billing_alert` 或 `/etc/nginx/conf.d/billing_alert.conf`）：

```nginx
server {
    listen 80;
    server_name your_domain_or_ip; # 替换为你的服务器 IP 或域名

    # 前端静态文件代理
    location / {
        root /path/to/Billing_Alert/frontend/dist; # 替换为实际的 dist 目录绝对路径
        index index.html;
        try_files $uri $uri/ /index.html; # 支持 React Router 的 History 路由模式
    }
}
```

### 4.3 启动并重载 Nginx
```bash
# 测试配置是否正确
sudo nginx -t

# 重载 Nginx 使配置生效
sudo systemctl reload nginx

# 设置开机自启
sudo systemctl enable nginx
```

---

## 5. 常见问题与注意事项

1. **前后端通信端口**：
   前端代码 (`src/api.js`) 中配置了动态获取当前域名并请求 `8000` 端口：
   ```javascript
   const apiBaseUrl = window.location.hostname === 'localhost' 
     ? 'http://localhost:8000/api' 
     : `http://${window.location.hostname}:8000/api`;
   ```
   因此，**必须确保 Linux 服务器的 `8000` 端口对客户端浏览器是可访问的**（配置云服务器安全组或 iptables/ufw 防火墙）。

2. **日志查看**：
   后端代码中配置了日志双写，你可以通过查看 `backend/app.log` 文件来排查后端运行时的错误和定时任务（APScheduler）的执行情况。

3. **默认管理员账号**：
   后端在首次启动时（`@app.on_event("startup")`）会自动创建一个默认管理员账号：
   - 用户名：`admin`
   - 密码：`admin`

4. **后端启动报错及依赖缺失问题**：
   如果在启动后端服务或登录时遇到报错，通常是因为 `requirements.txt` 中遗漏了部分隐式依赖。请手动执行以下命令补充安装：
   ```bash
   # 1. 修复 Pydantic 邮箱验证报错 (ImportError: email-validator is not installed)
   pip install email-validator
   
   # 2. 修复 JWT 和密码加密报错 (ModuleNotFoundError: No module named 'jose')
   pip install "python-jose[cryptography]" "passlib[bcrypt]" python-multipart
   
   # 3. 修复 bcrypt 密码长度验证报错 (ValueError: password cannot be longer than 72 bytes)
   # 降级 bcrypt 版本以兼容 passlib
   pip install bcrypt==4.0.1
   
   # 4. 修复 GCP 账单模块报错 (ImportError: cannot import name 'billing_v1' from 'google.cloud')
   pip install google-cloud-billing
   ```

5. **刷新页面或直接访问子路由（如 `/alerts`）出现 Nginx 404 错误**：
   这是单页应用（SPA）路由的经典问题。因为 React Router 使用的是前端 History 路由，当直接访问或刷新 `http://gen101.gcp-billing.cloud/alerts` 时，Nginx 会在服务器磁盘上寻找名为 `alerts` 的真实文件或文件夹。由于找不到，就会返回 404。
   
   **解决方案**：
   确保 Nginx 配置文件中的 `location /` 块中配置了 `try_files` 指令，将所有未匹配到的静态资源请求全部重定向到 `index.html`，交给前端路由处理：
   ```nginx
   location / {
       root /path/to/Billing_Alert/frontend/dist;
       index index.html;
       # 关键配置：如果找不到请求的文件或目录，则返回 index.html
       try_files $uri $uri/ /index.html;
   }
   ```
   修改配置后，记得重载 Nginx：
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

---

## 6. 本地开发与调试指南

如果您需要在本地环境（如 Windows/macOS/Linux 桌面版）进行开发和调试，请按照以下步骤启动服务：

### 6.1 启动后端服务 (开发模式)
在开发模式下，建议使用 `--reload` 参数启动 Uvicorn，这样在修改代码后服务会自动热重载。

```bash
cd backend

# 激活虚拟环境 (Windows: venv\Scripts\activate, macOS/Linux: source venv/bin/activate)
source venv/bin/activate

# 启动 FastAPI 服务并开启热重载
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6.2 启动前端服务 (开发模式)
前端使用 Vite 构建，自带了极速的开发服务器，支持模块热替换 (HMR)。

```bash
cd frontend

# 启动 Vite 开发服务器
npm run dev
```
启动后，终端会输出一个本地访问地址（通常是 `http://localhost:5173`）。在浏览器中打开该地址即可进行调试。前端会自动将 API 请求发送到 `http://localhost:8000/api`。

---

## 7. Docker Compose 部署 (推荐)

为了简化部署流程，项目现已支持使用 Docker Compose 进行一键部署。该方式会自动拉起 PostgreSQL 16 数据库、FastAPI 后端服务以及基于 Nginx 的 React 前端服务，并配置好数据持久化。

### 7.1 环境准备
请确保服务器已安装以下软件：
- **Docker**
- **Docker Compose** (或 `docker compose` 插件)

### 7.2 配置文件准备
1. 确保项目根目录下存在 `docker-compose.yml` 文件。
2. 确保 `backend/credentials.json` 文件存在，这是访问 Google Cloud API 所必需的凭证。

### 7.3 一键启动服务
在项目根目录（即 `docker-compose.yml` 所在的目录）下执行以下命令：

```bash
# 创建docker网络
docker network create billing_shared_net

# 构建镜像并在后台启动所有服务
docker-compose up -d --build
```

### 7.4 验证部署
- **前端服务**：将运行在宿主机的 `80` 端口。你可以直接通过浏览器访问 `http://<服务器IP>` 来使用系统。
- **后端服务**：将运行在宿主机的 `8000` 端口。你可以通过访问 `http://<服务器IP>:8000/docs` 来查看 FastAPI 的 Swagger 接口文档。
- **数据库服务**：PostgreSQL 运行在宿主机的 `15432` 端口，数据已挂载到本地的 `billing_alert_postgres_data` 卷中，确保数据不会因容器重启而丢失。

### 7.5 常用 Docker 命令
```bash
# 查看服务运行状态
docker-compose ps

# 查看服务日志 (例如查看前端或后端日志)
docker-compose logs -f frontend
docker-compose logs -f backend

# 停止并移除容器（保留数据卷）
docker-compose down

# 停止并移除容器，同时清理数据卷（警告：会丢失数据库数据！）
docker-compose down -v
```

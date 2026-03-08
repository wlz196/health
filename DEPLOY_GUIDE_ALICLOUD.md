# 生产环境服务器部署指南 (阿里云 2C2G)

您的 2核 2G 服务器对于目前的 MVP 项目资源实际上**非常充足**。针对前后端分离项目，业界最规范也最高效的做法是**将前后端都部署在同一台服务器上，用 Nginx 作为入口的「交通警察」**。

## 🎯 整体架构思路
*   **前端 (Vue 3)**：在本地电脑上执行 `npm run build`。这个操作会把所有的 .vue 代码压缩成一堆轻巧纯洁的静态文件库（HTML/CSS/JS）。将这些静态库丢给服务器上的 **Nginx** 托管，不消耗任何动态 CPU 资源。
*   **后端 (FastAPI)**：在服务器上启动后，它作为守护进程常驻在比如 `8080` 端口。我们不再使用开发环境的单进程 `uvicorn`，而是换成 `gunicorn + uvicorn worker` 实现多进程多核负载。
*   **Nginx的反向代理**：配置 Nginx 统一掌管 `80` (HTTP) 或 `443` (HTTPS) 端口。如果用户访问 `/` 则直接返回前端静态文件；如果访问带有 `/api` 的路径，偷偷把流量转交给本机的 `8080` 后端去处理。

---

## 🚀 极其详细的部署实施步骤

### 步骤一：服务器环境大扫除与准备 (在阿里云服务器执行)
1. 登录阿里云控制台，找到这台服务器，进入**安全组**，确保 **80 (HTTP)**、**443 (HTTPS)** 和 **22 (SSH)** 端口对外开放。
2. 通过 SSH 终端连接进您的服务器（假设为 Ubuntu 系统）。
3. 安装必要的底层基础设施：
   ```bash
   sudo apt update
   sudo apt install -y nginx python3-pip python3-venv git
   ```

### 步骤二：把代码搬移上云端
您可以把当前电脑里的 `backend` 文件夹整体压缩传到服务器，或者通过 Git 仓库拉取上去。我们把它们放在云服务器的 `/var/www/health_dash/` 目录中。

```bash
# 在云服务器上准备目录结构
sudo mkdir -p /var/www/health_dash/frontend
sudo mkdir -p /var/www/health_dash/backend
sudo chown -R $USER:$USER /var/www/health_dash
```

### 步骤三：前端打包出海 (在本地电脑执行)
1. 在您现在**本地电脑**的前端目录下：
   打开 `frontend/src/views/Intake.vue` 与其他有请求的地方，将代码里的 `http://127.0.0.1:8080/api/...` 改写为相对路径 `'/api/...'` 或您在阿里云绑定的 `http://您的IP或域名/api/...`。
2. 运行打包命令：
   ```bash
   cd frontend
   npm run build
   ```
3. 这个命令会生成一个名为 `dist` 的文件夹。请利用 SCP（或宝塔面板/SFTP 等工具），把这个 `dist` 里面所有的文件上传到云服务器刚才建好的 `/var/www/health_dash/frontend` 里面。

### 步骤四：配好后端的多核马达 (在阿里云服务器执行)
进入您刚刚传好代码的 `/var/www/health_dash/backend` 目录，安装生产环境依赖：

```bash
cd /var/www/health_dash/backend

# 为了不弄乱服务器原生环境，创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 除了之前那些包，我们还需要安装高并发引擎 gunicorn
pip install -r requirements.txt
pip install gunicorn

# 设置好 .env 文件（包含您的 ZHIPU_API_KEY）
nano .env 

# 把跑过一次且有了登录缓存记录的 ~/.garminconnect 这个隐藏文件夹也要传上服务器
```

### 步骤五：让后端长生不老 (常驻进程 Supervisor 方案)
千万不要直接 `python main.py`，因为 SSH 一关它就死了。

我们可以使用 Systemd 把 FastAPI 做成一个系统级服务：
`sudo nano /etc/systemd/system/health_backend.service`
写入如下内容：
```ini
[Unit]
Description=Gunicorn daemon for Health App
After=network.target

[Service]
User=root
# 将下面路径替换为真实包含后端的路径
WorkingDirectory=/var/www/health_dash/backend
# 开启2个进程来压满 2C 的 CPU
ExecStart=/var/www/health_dash/backend/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker main:app -w 2 --bind 127.0.0.1:8080

[Install]
WantedBy=multi-user.target
```

启动并把它设为开机自启：
```bash
sudo systemctl daemon-reload
sudo systemctl start health_backend
sudo systemctl enable health_backend
```

### 步骤六：让 Nginx 上岗 (终极反向代理)
`sudo nano /etc/nginx/sites-available/health`

放入以下配置：
```nginx
server {
    listen 80;
    # server_name 您的域名或者云服务器公网IP;
    server_name 123.45.67.89;

    # 1. 拦截前端静态页面请求
    location / {
        root /var/www/health_dash/frontend;
        index index.html index.htm;
        # 支持 Vue Router 的 history 模式
        try_files $uri $uri/ /index.html; 
    }

    # 2. 拦截带 API 前缀的请求，全扔给后端的 8080 端口处理
    location /api {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

激活这个配置并重启 Nginx：
```bash
sudo ln -s /etc/nginx/sites-available/health /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

🎉 **大功告成！** 现在，只要在手机浏览器里输入您的阿里云外网 IP，就可以完美访问不仅超快而且极省流量的 AI 营养师大盘了！

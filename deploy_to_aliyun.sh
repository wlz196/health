#!/bin/bash
# AI Health Dashboard 阿里云 Ubuntu 一键自动化配置脚本
# 请将整个项目文件夹（包含 frontend/dist 和 backend）上传到阿里云服务器的 /var/www/health_dash 目录后执行此脚本

set -e # 发生任何错误即中止脚本

echo "================================================="
echo "开始在您的阿里云服务器上自动化部署 AI 健康面板..."
echo "================================================="

# 1. 安装系统级基础设施
echo "[1/4] 正在安装必要基建 (Nginx / Python3 / Venv)..."
sudo apt-get update -y
sudo apt-get install -y nginx python3-pip python3-venv git

# 2. 初始化后端代码与沙盒环境
echo "[2/4] 正在安装 Python 后端多路高并发运行依赖..."
cd /var/www/health_dash/backend
rm -rf venv  # 🌟 强制清理可能从 Mac 误推上去的旧沙盒环境，防止架构错乱
python3 -m venv venv
# 隐式激活直接绝对路径调用
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install gunicorn

# 3. 配置 SystemD 守护进程让它开机自启动不死机
echo "[3/4] 正在挂载系统级守护兵卫保持运行..."
SERVICE_FILE="/etc/systemd/system/health_backend.service"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=Gunicorn daemon for Health App
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/health_dash/backend
ExecStart=/var/www/health_dash/backend/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker main:app -w 2 --bind 127.0.0.1:8080

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart health_backend
sudo systemctl enable health_backend

# 4. 配置 Nginx 取代 Uvicorn 进行流量拦截
echo "[4/4] 正在绑定 Nginx 处理纯前端流量与转发 API..."
NGINX_CONF="/etc/nginx/sites-available/health"
sudo bash -c "cat > $NGINX_CONF" << EOF
server {
    listen 80;
    server_name _; 

    access_log /var/log/nginx/health_access.log;
    error_log /var/log/nginx/health_error.log;

    # 代理纯静态优化的前端 (这里对应 frontend/dist)
    location / {
        root /var/www/health_dash/frontend/dist;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
    }

    # 动态数据放给后台接盘
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 清除默认并上线新防流
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/health /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "================================================="
echo "🚀 恭喜！服务器配置已全部绿灯通过并成功部署！"
echo "👉 请在手机或电脑浏览器中，直接输入本服务器的外网 IP ("http://您的弹性公网IP") 即可访问！"
echo "================================================="

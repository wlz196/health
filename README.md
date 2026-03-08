# AI Health Dashboard (智能健康面板)

AI Health Dashboard 是一个极简、现代的个人健康管理面板 MVP。它通过整合用户的**佳明 (Garmin)** 运动健康数据，并结合强大的**智谱 AI (ZhipuAI)** 视觉大模型能力，让你不仅能随时追踪运动和睡眠表现，还能通过手机拍照或文字输入一键分析每餐的营养摄入。

## ✨ 核心功能
*   **Garmin 数据自动同步**：实时拉取并展示今日卡路里、步数、睡眠详情、近期有氧/无氧运动记录。
*   **AI 营养师分析**：支持上传照片或直接输入文字描述，调用国内智谱大模型 (`glm-4-flash`, `glm-4v-flash`)，瞬间返回食物的热量、蛋白质、脂肪和碳水数据。
*   **渐进式移动端体验**：轻快、顺滑的 Vue 3 组件化界面体验，适配手机与 PC 查阅。

## 🛠 技术栈
**前端 (Frontend)**
*   Vue 3 (Composition API) + Vite
*   Tailwind CSS (样式、自适应以及渐变 UI 设计)
*   Vant 4 (移动端轻量级 UI 组件库)

**后端 (Backend)**
*   FastAPI (极速后台与 RESTful API)
*   SQLite + SQLAlchemy (本地轻量级数据库存储与 ORM)
*   python-garminconnect (拉取 Garmin API)
*   ZhipuAI SDK (连接智谱大语言模型进行食物成分识别)

## 🚀 本地开发与运行指南

### 前期准备
1. 确保已安装 Python 3.9+ 
2. 确保已安装 Node.js (建议 18+) 和 npm
3. **获取智谱大模型 API Key**: 免费注册 [智谱大模型开放平台](https://open.bigmodel.cn/)，在后台页面获取免费的 API Key。
4. **准备 Garmin 账号**: 您需要确保您的 Garmin Connect (CN/国际区) 账号和密码有效，便于首次脚本拉取数据授权。

### 运行后端 (Backend)
```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活虚拟环境 (可选但推荐)
python3 -m venv venv
source venv/bin/activate

# 3. 安装所需 Python 依赖包
pip install -r requirements.txt

# 4. 配置环境变量
# 在 backend 目录下创建文件 .env，并写入您的智谱 API Key：
# ZHIPU_API_KEY="您的智谱API Key"

# 5. 首次登录佳明获取 Token (后续将缓存在 ~/.garminconnect 中)
python login.py 

# 6. 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```
> 默认启动后，FastAPI Swagger UI 可以在浏览器访问 `http://127.0.0.1:8080/docs` 查看并测试 API。

### 运行前端 (Frontend)
```bash
# 1. 另开一个终端窗口，进入前端目录
cd frontend

# 2. 安装 Node.js 依赖
npm install

# 3. 启动 Vite 开发服务器
npm run dev
```

### 访问面板
在浏览器中打开前端开发者热更新地址（通常为 `http://localhost:5173` 或随终端提示访问），即可体验该健康大盘！使用底部导航栏切换在 **总览 / 运动 / 饮食录入** 之间跳转。

# AI Health Dashboard (智能健康面板)

AI Health Dashboard 是一个极简、现代的个人健康与饮食管理面板。它不仅整合了运动数据的记录，还结合强大的 **智谱 AI (ZhipuAI)** 大模型视觉与自然语言能力，让您能通过手机拍照或文字输入一键分析每餐的营养摄入。最新架构支持多用户逻辑隔离与高级热量预算计算。

## ✨ 核心功能与亮点

* **🤖 智能 AI 营养师 (ZhipuAI 赋能)**：
  * 支持上传照片或输入自然语言描述。
  * 自动识别食物组分，精准换算返回热量 (kcal) 及三大营养素 (蛋白质、脂肪、碳水)。
* **🍱 灵活的食材模板与记录系统**：
  * **配料表模板**：支持以 100g 为基准录入常见食材（支持 kJ 自动换算大卡），记录时只需输入食用克数，系统自动按比例结算。
  * **我的常用食物**：一键保存心头好，支持列表模糊搜索、一键快捷删除。
  * **自定义补录**：支持选择非当前时间的进食，完善您的摄入时间线。
* **📊 实时热量看板与运动模式 (TDEE Deficit)**：
  * 根据用户的基础代谢 (BMR) 与灵活选择的**“今日运动模式”** (练腿、胸背、有氧、休息、放纵)，自动调配全天热量预算与碳水/蛋白质配比。
  * **实时缺口追踪**：直观展示今日热量缺口与剩余可摄入预算，超标即时红色预警。
* **🔐 多用户安全隔离**：
  * 引入 JWT Token 鉴权，支持多人注册登录。
  * 单库多租户模型：底层 SQLite 数据库通过 `user_id` 严格隔离每个用户的饮食账单与模板储备。
* **📱 渐进式移动端体验**：
  * 采用 Vue 3 + Vant 4 构建，深度适配手机端操作（支持原生呼出手机相册或摄像头双擎选项）。

## 🛠 技术栈

**前端 (Frontend)**
* Vue 3 (Composition API) + Vite
* Tailwind CSS (流体排版、渐变 UI 与深色适配)
* Vant 4 (移动端轻量级 UI 组件库)
* Vue Router & LocalStorage auth states

**后端 (Backend)**
* FastAPI (极致性能的异步 Python 框架)
* SQLite + SQLAlchemy (轻量级本地防拥堵存储带 ORM 映射)
* ZhipuAI SDK (`glm-4-flash`, `glm-4v-flash` 高速视觉与自然语言识别)
* JWT (JSON Web Tokens) 会话鉴权与密码哈希加密

## 🚀 本地开发与运行指南

### 前期准备
1. 安装 Python 3.10+ 与 Node.js 18+
2. **获取智谱大模型 API Key**: 免费注册 [智谱大模型平台](https://open.bigmodel.cn/) 获取免费 API Key。

### 运行后端 (Backend)
```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖包
pip install -r requirements.txt

# 4. 配置环境变量
# 在 backend 目录下创建 .env 文件，并写入：
# ZHIPU_API_KEY="您的智谱API Key"
# SECRET_KEY="任填一串乱码用于JWT签名"

# 5. 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 运行前端 (Frontend)
```bash
# 1. 进入前端目录
cd frontend

# 2. 安装并启动
npm install
npm run dev
```
> 此时访问 `http://localhost:5173` 即可进入系统进行注册体验。

## ☁️ 生产环境部署 (Ubuntu 服务器)
项目内附自动化部署脚本 `deploy_to_aliyun.sh`：
1. 请先在本地完成 `npm run build` 生成生产级的 `dist`。
2. 将全套项目传至服务器 `/var/www/health_dash` 目录。
3. `sudo bash deploy_to_aliyun.sh` 一键配置好 Nginx 静态代理与 Systemd 的 Gunicorn 守护进程，真正实现云端高可用部署。

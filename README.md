# 律师事务所案件管理系统

一款专注于案件全流程管理的律师事务所管理系统，集案件审核（含利冲检索）、合同审核、结案审核(含案卷归档)和已结案等关键环节于一体，支持历史案件批量导入和导出，为中小律师事务所提供高效、专业的案件管理解决方案。

![Language - Vue](https://img.shields.io/badge/Vue-53.9%25-34C26F?logo=vue.js)
![Language - Python](https://img.shields.io/badge/Python-42%25-3776AB?logo=python)
![Language - JavaScript](https://img.shields.io/badge/JavaScript-3.6%25-F7DF1E?logo=javascript)
![License](https://img.shields.io/badge/License-MIT-green)

---

##  项目特色

### 核心定位

本系统**只专注案件管理一条主线**，区别于全场景、全功能（人事财）的传统律所管理系统：
-  案件全流程管理（收案 → 审核 → 结案）
-  简单律师管理
-  财务数据记录（多律师可设置分配比例）
-  不涉及行政管理（交由钉钉、飞书等处理）
-  不处理财务结算（交由线下或第三方财务系统）

### 业务流程

系统通过以下4个关键状态控制案件流程：
1. **案件审核** - 新案件风控审核（收案登记）
2. **合同审核** - 委托合同的核准（上传委托合同）
3. **结案审核** - 案件结束的审核（上伟归档案卷）
4. **已结案** - 案件归档状态

###  系统设计亮点

- **专注设计** - 只专注案件管理一条主线，功能简洁高效
- **权限体系** - RBAC 模型，满足不同角色需求
- **可扩展性** - Python 技术栈为 AI 应用预留充足空间
- **完整流程** - 覆盖 80% + 中小律所案件管理需求
- **高性能** - FastAPI + 异步处理，支持高并发
- **企业级** - Nginx + Gunicorn 高可用架构
- **安全性** - JWT认证、密码加密、权限控制

###  系统适用范围

 **适用于** - 中小律师事务所（全国近 80% ）
- 案件集中度高
- 需要简洁高效的管理工具
- 数据敏感性要求高

 **不适用于** - 大型律所
- 需要完整的 HR、财务系统
- 需要多维度数据分析
- 有分所的律所

---

##  功能模块

系统共设计了 6 个功能页面：

### 1. 后台登录页（Login）
- 用户身份认证
- 角色权限识别
  <img width="3408" height="1898" alt="Screenshot 2026-04-28 at 20-06-44 成立律师事务所案件管理系统" src="https://github.com/user-attachments/assets/b0bd7be3-b949-4d48-a9af-d2b50a6325bc" />


### 2. 控制台首页（Dashboard）
- 统计栏：案件数、客户数、案件类型分布
- 关键指标快速览览
- 实时数据展示
  <img width="3408" height="1898" alt="Screenshot 2026-04-28 at 20-06-09 成立律师事务所案件管理系统" src="https://github.com/user-attachments/assets/bac4dcae-242e-44f5-a5d2-019fc2c83869" />


### 3. 收案登记页（CaseRegistration）
- 冲突检索（必须通过后才能收案）
- 案件基本信息登记
- 自动生成流水号
- 登记后需风控审核
  <img width="3408" height="5048" alt="Screenshot 2026-04-28 at 20-06-18 成立律师事务所案件管理系统" src="https://github.com/user-attachments/assets/217bfed7-6319-4ae4-9b20-bd42af0beee0" />


### 4. 案件管理页（CaseManagement）
-  4个关键节点的案件统计
-  案件流转管理
-  案件作废处理
-  合同解除功能
-  历史案件导入/导出
-  对接线下函件签发管理
  <img width="3408" height="2154" alt="Screenshot 2026-04-28 at 20-06-32 成立律师事务所案件管理系统" src="https://github.com/user-attachments/assets/b251860c-27e4-41be-b60d-fbf738b41e21" />


### 5. 案件详情页（CaseDetail）
-  完整案件信息展示
-  关联人员、律师、阶段信息
-  财务数据详情
-  案件信息导出功能
  <img width="3408" height="3096" alt="Screenshot 2026-04-28 at 20-08-54 成立律师事务所案件管理系统" src="https://github.com/user-attachments/assets/4d4d07ea-2d22-4045-97c9-4b6baaa4bcb5" />


### 6. 律师管理页（LawyerManagement）
-  律师基本信息管理
-  在职/离职状态管理
-  律师案件统计
  <img width="3408" height="2154" alt="Screenshot 2026-04-28 at 20-12-39 成立律师事务所案件管理系统" src="https://github.com/user-attachments/assets/a7f7bb62-a0a4-470e-9913-a9fb09bc5d9b" />
 
---

##  快速开始

### 前置要求
- Python 3.8+
- Node.js 16+
- PostgreSQL 13+
- Git

### 本地开发环境

#### 1. 克隆项目
```bash
git clone https://github.com/chengliji/LawFirmSystem.git
cd LawFirmSystem
```

#### 2. 后端设置
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r backend/requirements.txt

# 配置数据库连接 (修改 backend/database.py)
# 修改 SECRET_KEY (修改 backend/auth.py)

# 初始化数据库
python -m backend.seeder

# 运行后端服务
uvicorn backend.main:app --reload --port 8000
```

#### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 生产环境构建
npm run build
```

#### 4. 数据库初始化
```sql
-- 连接 PostgreSQL
psql -U postgres

-- 创建用户和数据库
CREATE USER law_user WITH PASSWORD '你的密码';
CREATE DATABASE law_db OWNER law_user;
GRANT ALL PRIVILEGES ON DATABASE law_db TO law_user;
```

---

##  部署指南

### 云服务器部署架构
```
Internet
   ↓
Nginx (反向代理 + 静态资源服务器)
   ↓
├─ /api → Gunicorn/Uvicorn (后端进程)
│          ↓
│      FastAPI + SQLAlchemy
│          ↓
│      PostgreSQL
│
└─ / → 静态资源 (Vue 3 编译产物)
```

### 部署环境（推荐）
- **云服务器** - 阿里云([点击去购买](https://www.aliyun.com/daily-act/ecs/activity_selection?userCode=l3df7skw))
、腾讯云([点击去购买](https://curl.qcloud.com/SSZ4gX3w))
等
- **操作系统** - Debian 13 或 Ubuntu 22.04
- **最小配置** - 2核2GB内存

### 快速部署命令

#### 1. 系统包更新
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. 安装依赖环境
```bash
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx
```

#### 3. PostgreSQL 配置
```bash
sudo -u postgres psql

CREATE USER law_user WITH PASSWORD '你的生产强密码';
CREATE DATABASE law_db OWNER law_user;
GRANT ALL PRIVILEGES ON DATABASE law_db TO law_user;
\q
```

#### 4. 后端部署
```bash
# 创建应用目录
sudo mkdir -p /var/www/lawfirm
cd /var/www/lawfirm

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt
pip install gunicorn

# 初始化数据库
python -m backend.seeder

# 配置 Systemd 服务 (参考下面的配置)
```

#### 5. Systemd 配置（后端进程守护）
```bash
sudo nano /etc/systemd/system/lawfirm-backend.service
```

写入以下内容：
```ini
[Unit]
Description=Gunicorn instance to serve Law Firm FastAPI Backend
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/lawfirm
Environment="PATH=/var/www/lawfirm/venv/bin"
ExecStart=/var/www/lawfirm/venv/bin/gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start lawfirm-backend
sudo systemctl enable lawfirm-backend
sudo systemctl status lawfirm-backend
```

#### 6. 前端部署与 Nginx 配置
```bash
# 本地编译
cd frontend
npm run build

# 上传 dist 文件内容到服务器
# /var/www/lawfirm/frontend
```

配置 Nginx：
```bash
sudo nano /etc/nginx/sites-available/lawfirm
```

写入以下配置：
```nginx
server {
    listen 80;
    server_name 你的域名或公网IP;

    # 前端路由
    location / {
        root /var/www/lawfirm/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 文件上传
    location /uploads/ {
        alias /var/www/lawfirm/uploads/;
        client_max_body_size 50M;
    }
}
```

激活配置：
```bash
# 建立软链接
sudo ln -s /etc/nginx/sites-available/lawfirm /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 7. 安全检查清单
```bash
#  修改前端 API 基地址
# 文件：frontend/src/utils/request.js
# 将 http://localhost:8000/api 改为 /api

#  修改后端 JWT 密钥
# 文件：backend/auth.py
# 替换 SECRET_KEY 为超长随机复杂密钥

#  修改数据库密码
# 文件：backend/database.py
# 确保与云服务器 PostgreSQL 密码一致

#  赋予上传目录写权限
sudo chmod -R 777 /var/www/lawfirm/uploads

#  安全组配置
# 放行 80 端口 (HTTP)
# 放行 443 端口 (HTTPS) - 如需 SSL
# 可选放行 22 端口 (SSH) - 仅限管理

#  配置 SSL 证书 (推荐)
# 使用 Let's Encrypt 免费证书
# 参考：https://certbot.eff.org/
```

---

## 使用建议

1. **行政管理** → 交由钉钉、飞书等第三方OA处理
2. **财务结算** → 使用专业财务系统或线下管理
3. **数据安全** → 定期备份数据库，配置SSL证书
4. **性能优化** → 根据案件量调整Gunicorn进程数
5. **定期维护** → 及时更新系统补丁和依赖包

---

**最后更新** - 2026年04月

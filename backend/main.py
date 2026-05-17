# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import auth_router, case_router, user_router, dict_router

# 启动时自动创建数据库表结构
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="成立律师事务所管理系统 API", version="1.0.0")

# 配置 CORS，允许 Vue 3 前端（通常运行在 5173 或 8080 端口）访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境请替换为具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router.router)
app.include_router(case_router.router)
app.include_router(user_router.router)
app.include_router(dict_router.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Backend is running."}


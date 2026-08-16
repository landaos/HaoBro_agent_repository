"""应用启动入口 — 在项目根目录直接运行此文件即可"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],  # 只监控 src 目录，避免 .venv 依赖库文件变化触发重启
        log_level="info",
    )

"""应用启动入口 — 在项目根目录直接运行此文件即可"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[".venv/*"],  # 排除虚拟环境，避免 comtypes 生成文件触发重启
        log_level="info",
    )

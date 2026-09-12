"""
GitHub 仓库分析器 - 后端打包脚本
用法: python scripts/build_backend.py

构建产物: backend/dist/backend.exe
"""

import os
import sys
import shutil
from pathlib import Path

# 项目根目录 (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent


def build():
    """使用 PyInstaller 打包后端"""
    # 清理旧构建
    for d in ['build', 'dist']:
        p = BASE_DIR / d
        if p.exists():
            shutil.rmtree(p)
            print(f"  已清理: {d}/")

    # 构建参数
    args = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onefile',
        '--log-level=WARN',
        '--name=backend',
        '--add-data', f'{BASE_DIR / "app"}{os.pathsep}app',
        '--add-data', f'{BASE_DIR / ".env"}{os.pathsep}.',
        '--runtime-hook', str(BASE_DIR / 'scripts' / 'pyi_rth_pydantic_fix.py'),
        # Hidden imports
        '--hidden-import=uvicorn',
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.h11_impl',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.websockets_impl',
        '--hidden-import=uvicorn.middleware',
        '--hidden-import=uvicorn.middleware.wsgi',
        '--hidden-import=starlette.applications',
        '--hidden-import=starlette.routing',
        '--hidden-import=starlette.middleware',
        '--hidden-import=starlette.middleware.cors',
        '--hidden-import=starlette.responses',
        '--hidden-import=starlette.requests',
        '--hidden-import=starlette.datastructures',
        '--hidden-import=starlette.convertors',
        '--hidden-import=fastapi',
        '--hidden-import=fastapi.routing',
        '--hidden-import=fastapi.openapi',
        '--hidden-import=fastapi.openapi.utils',
        '--hidden-import=fastapi.encoders',
        '--hidden-import=pydantic',
        '--hidden-import=pydantic.dataclasses',
        '--hidden-import=sqlalchemy',
        '--hidden-import=sqlalchemy.orm',
        '--hidden-import=sqlalchemy.ext.declarative',
        '--hidden-import=sqlalchemy.sql',
        '--hidden-import=sqlalchemy.engine',
        '--hidden-import=sqlalchemy.pool',
        '--hidden-import=httpx',
        '--hidden-import=httpx._content',
        '--hidden-import=dotenv',
        '--hidden-import=dotenv.parser',
        '--hidden-import=dotenv.variables',
        '--hidden-import=loguru',
        '--hidden-import=loguru._logger',
        '--hidden-import=markdown',
        '--hidden-import=bs4',
        '--hidden-import=bs4.builder._lxml',
        '--hidden-import=yaml',
        '--hidden-import=tiktoken',
        '--hidden-import=tiktoken_ext',
        '--hidden-import=tiktoken_ext.openai_public',
        '--hidden-import=asyncio',
        '--hidden-import=concurrent',
        '--hidden-import=concurrent.futures',
        '--hidden-import=json',
        '--hidden-import=email',
        '--hidden-import=email.mime',
        '--hidden-import=email.mime.multipart',
        '--hidden-import=email.mime.text',
        '--hidden-import=http',
        '--hidden-import=http.cookies',
        # Excludes (减小体积)
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=cv2',
        '--exclude-module=pandas',
        '--exclude-module=numpy',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        '--exclude-module=notebook',
        '--exclude-module=ipython',
        '--exclude-module=jupyter',
        '--exclude-module=tensorflow',
        '--exclude-module=torch',
        '--exclude-module=transformers',
        # 入口脚本
        str(BASE_DIR / 'run.py'),
    ]

    print(f"执行: PyInstaller 打包中...")
    print()

    os.chdir(BASE_DIR)
    import subprocess
    proc = subprocess.run(args, capture_output=False)
    ret = proc.returncode

    if ret == 0:
        dist_dir = BASE_DIR / 'dist'
        # 创建 data/ 目录
        (dist_dir / 'data').mkdir(exist_ok=True)
        print(f"\n[OK] 构建成功: {dist_dir / 'backend.exe'}")

        # 复制 .env.example 作为模板
        env_example = BASE_DIR / '.env.example'
        if env_example.exists() and not (dist_dir / '.env').exists():
            shutil.copy2(str(env_example), str(dist_dir / '.env.example'))
            print(f"[INFO] 已复制 .env.example: {dist_dir / '.env.example'}")
    else:
        print(f"\n[错误] 构建失败 (exit code: {ret})")

    return ret


if __name__ == '__main__':
    sys.exit(build())
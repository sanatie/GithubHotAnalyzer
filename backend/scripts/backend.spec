# -*- mode: python ; coding: utf-8 -*-
#
# GitHub 仓库分析器 - 后端 PyInstaller 构建配置
# 构建命令: pyinstaller backend/scripts/backend.spec
#

import sys
from pathlib import Path

# 项目根目录 (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent

block_cipher = None

a = Analysis(
    # 入口脚本
    [str(BASE_DIR / 'run.py')],

    # 额外的探测路径 (让 PyInstaller 能找到 app/ 和 scripts/)
    pathex=[str(BASE_DIR)],

    binaries=[],
    datas=[
        # 将整个 app/ 包打包进去
        (str(BASE_DIR / 'app'), 'app'),
        # 将 .env 配置文件放在 exe 同级目录
        (str(BASE_DIR / '.env'), '.'),
    ],

    hiddenimports=[
        # FastAPI / Starlette 相关
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.middleware',
        'uvicorn.middleware.wsgi',
        'starlette',
        'starlette.applications',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.responses',
        'starlette.requests',
        'starlette.datastructures',
        'starlette.convertors',
        'fastapi',
        'fastapi.routing',
        'fastapi.openapi',
        'fastapi.openapi.utils',
        'fastapi.encoders',
        'pydantic',
        'pydantic.dataclasses',
        # SQLAlchemy 相关
        'sqlalchemy',
        'sqlalchemy.orm',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.sql',
        'sqlalchemy.engine',
        'sqlalchemy.pool',
        # HTTP 客户端
        'httpx',
        'httpx._content',
        # 工具库
        'dotenv',
        'dotenv.parser',
        'dotenv.variables',
        'loguru',
        'loguru._logger',
        'markdown',
        'bs4',
        'bs4.builder._lxml',
        'yaml',
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        # Python 内置模块
        'asyncio',
        'concurrent',
        'concurrent.futures',
        'json',
        'email',
        'email.mime',
        'email.mime.multipart',
        'email.mime.text',
        'http',
        'http.cookies',
    ],

    hookspath=[],
    hooksconfig={},

    # 排除不需要的模块，减小体积
    excludes=[
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'matplotlib',
        'cv2',
        'pandas',
        'numpy',
        'scipy',
        'PIL',
        'notebook',
        'ipython',
        'jupyter',
        'tensorflow',
        'torch',
        'transformers',
    ],

    runtime_hooks=[
        str(BASE_DIR / 'scripts' / 'pyi_rth_pydantic_fix.py'),
    ],

    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='.',
)

# 构建后创建 data/ 目录和 .env 模板
if __name__ == '__main__':
    import shutil
    src_dir = Path(a.scripts[-1].real_dest) if hasattr(a.scripts[-1], 'real_dest') else BASE_DIR
    dist_dir = Path(__file__).resolve().parent.parent / 'dist'
    if dist_dir.exists():
        (dist_dir / 'data').mkdir(exist_ok=True)
        print(f"[INFO] 已创建 data/ 目录: {dist_dir / 'data'}")
        if not (dist_dir / '.env').exists():
            env_template = BASE_DIR / '.env.example'
            if env_template.exists():
                shutil.copy2(str(env_template), str(dist_dir / '.env'))
                print(f"[INFO] 已复制 .env 模板: {dist_dir / '.env'}")
import sys
import os

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    os.environ['BASE_DIR'] = base_dir
    sys.path.insert(0, base_dir)

from scripts import pydantic_patch

import uvicorn
from app.main import app

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')

#!/bin/zsh
cd "${0:A:h}"
if command -v python3 >/dev/null; then
  python3 tools/manage.py serve
else
  print '請安裝 Python 3.10 或更新版本。'
  read
fi

# 每日励志思考桌面应用 (Python)

简介
- 这是一个小型桌面应用，启动时会显示“今日励志语录”（从 ZenQuotes API 获取），并带有刷新/复制/关闭按钮。
- 支持每日缓存：同一天内多次打开会显示相同的一句“今日语录”。

运行（开发环境）
1. 安装 Python 3.8+。
2. 建立虚拟环境并安装依赖：
   python -m venv venv
   # Windows:
   venv\\Scripts\\activate
   # macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
3. 运行：
   python quote_app.py

打包为 Windows 可执行文件 (.exe)
- 使用 PyInstaller 打包为单文件窗口应用：
  pip install pyinstaller
  pyinstaller --onefile --windowed quote_app.py

- 常用选项说明：
  - --onefile：生成单个 exe（启动时会解包到临时目录）。
  - --windowed：不显示控制台窗口（适合 GUI）。
  - --icon=app.ico：指定图标（可选）。

示例打包命令（带图标）：
  pyinstaller --onefile --windowed --icon=app.ico quote_app.py

生成结果位置：
- 打包成功后，exe 位于 dist/quote_app.exe，直接双击即可打开对话框显示语录。

常见问题
- 如果 API 请求失败，程序会使用内置备用语录并在缓存中记录。
- 缓存文件位置：~/.daily_quote_cache.json（可删除以强制重新获取）

扩展建议
- 加入“每天定时弹窗”功能（使用系统计划任务/定时器）。
- 换成更丰富的 UI（PyQt 或 Electron）以获得更漂亮的对话框/动画。
- 加入多语言/主题切换功能。

API 说明
- 使用 ZenQuotes（免费公共 API）：https://zenquotes.io
  - /api/today 获取当天语录
  - /api/random 获取随机语录
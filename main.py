#!/usr/bin/env python3
"""
FileTool - 文件处理工具箱
- 文件解压/压缩
- 图片/音频/视频/PDF格式转换
"""
import sys
import os

# 确保app目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from app.ui.main_window import MainWindow
from app.core.ffmpeg_helper import setup_ffmpeg_env, ensure_ffmpeg


def _get_icon_path():
    """获取图标路径，支持打包后路径"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    icon = os.path.join(base, 'app', 'assets', 'icon.png')
    if os.path.exists(icon):
        return icon
    return ''


def main():
    # 初始化 ffmpeg
    setup_ffmpeg_env()
    ffmpeg_ok = ensure_ffmpeg()
    if not ffmpeg_ok:
        print("[警告] ffmpeg 未找到，音视频转换功能将不可用")

    # 高DPI适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("文件工具箱")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("FileTool")

    # 全局样式
    app.setStyle("Fusion")

    window = MainWindow()
    # 设置图标
    icon_path = _get_icon_path()
    if icon_path:
        window.setWindowIcon(QIcon(icon_path))

    # 在状态栏显示 ffmpeg 状态（仅激活后，功能页面才有status_bar）
    if window.license_mgr.is_activated():
        if not ffmpeg_ok:
            window.status_bar.showMessage("⚠️ ffmpeg 未加载，音视频转换不可用")
        else:
            window.status_bar.showMessage("✅ 已激活 · 所有功能可用")

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

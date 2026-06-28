"""
ffmpeg 路径管理
自动查找内置的 ffmpeg.exe，确保音视频转换可用
"""
import os
import sys
import subprocess


def get_ffmpeg_dir() -> str:
    """返回 ffmpeg 所在目录"""
    # 打包后: _MEIPASS/app/assets/ffmpeg/
    # 开发时: app/assets/ffmpeg/
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(__file__), '..', '..')

    return os.path.join(base, 'app', 'assets', 'ffmpeg')


def get_ffmpeg_path() -> str:
    """返回 ffmpeg.exe 绝对路径"""
    return os.path.join(get_ffmpeg_dir(), 'ffmpeg.exe')


def get_ffprobe_path() -> str:
    """返回 ffprobe.exe 绝对路径"""
    return os.path.join(get_ffmpeg_dir(), 'ffprobe.exe')


def ensure_ffmpeg() -> bool:
    """检查 ffmpeg 是否可用"""
    path = get_ffmpeg_path()
    if os.path.exists(path):
        return True
    # fallback: 检查系统 PATH
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def setup_ffmpeg_env():
    """设置环境变量，让 ffmpeg-python 能找到 ffmpeg"""
    ffmpeg_dir = get_ffmpeg_dir()
    if os.path.exists(ffmpeg_dir):
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        # ffmpeg-python 也读这个
        os.environ['FFMPEG_BINARY'] = get_ffmpeg_path()

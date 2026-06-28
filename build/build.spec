# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置

使用方法：
    cd FileTool
    pyinstaller build/build.spec --clean
"""
import os
import sys

# 项目根目录 (build.spec 在 build/ 下，用当前工作目录)
ROOT_DIR = os.getcwd()

block_cipher = None

a = Analysis(
    [os.path.join(ROOT_DIR, 'main.py')],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        # 打包 ffmpeg (保留目录结构)
        (os.path.join(ROOT_DIR, 'app', 'assets', 'ffmpeg'), 'app/assets/ffmpeg'),
        # 打包图标
        (os.path.join(ROOT_DIR, 'app', 'assets', 'icon.png'), 'app/assets'),
        (os.path.join(ROOT_DIR, 'app', 'assets', 'icon.ico'), 'app/assets'),
        # 打包收款码（如果有）
        (os.path.join(ROOT_DIR, 'app', 'assets', 'pay_qr.png'), 'app/assets'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'py7zr',
        'PIL',
        'PIL._imaging',
        'fitz',
        'ffmpeg',
        'pdf2docx',
        'pptx',
        'openpyxl',
        'docx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'notebook',
        'PyQt5',
        'test',
        'unittest',
        'setuptools',
    ],
    noarchive=False,
    module_collection_mode={},
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FileTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, 'app', 'assets', 'icon.ico'),
)

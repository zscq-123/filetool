# 文件工具箱 (FileTool)

一款简单易用的 Windows 文件处理工具，买断制 10 元。

## 功能

### 📦 文件解压
- 支持格式：zip, rar, 7z, tar, gz, bz2, xz, tgz
- 拖拽文件解压
- 加密压缩包支持
- 内容预览

### 📁 文件压缩
- 输出格式：zip, 7z, tar.gz
- 支持加密（zip/7z）
- 文件夹压缩

### 🔄 格式转换
- **图片转换**：jpg, png, webp, bmp, gif, tiff, ico 互转（批量）
- **音频转换**：mp3, wav, flac, aac, ogg, m4a, wma（需要 ffmpeg）
- **视频转换**：mp4, avi, mkv, mov, wmv, webm, flv（需要 ffmpeg）
- **PDF 转换**：
  - 图片→PDF / PDF→图片
  - PDF→Word (.docx)
  - PDF→Excel (.xlsx)
  - PDF→PPT (.pptx)

## 开发

### 环境要求
- Python 3.10+
- pip

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行
```bash
python main.py
```

### 打包
```bash
pip install pyinstaller
pyinstaller build/build.spec --clean
```

打包后的 exe 在 `dist/FileTool/` 目录下。

## License 生成

给买家激活码：
```bash
python build/generate_license.py <买家机器码>
```

## 技术栈
- **UI**: PySide6 (Qt6)
- **解压**: py7zr + patool + 内置 zipfile/tarfile
- **图片**: Pillow
- **音视频**: ffmpeg-python (需安装 ffmpeg)
- **PDF**: PyMuPDF (fitz)
- **打包**: PyInstaller

"""
解压引擎 - 支持 zip/rar/7z/tar/gz/bz2/xz
"""
import os
import zipfile
import tarfile
import shutil
from pathlib import Path
from typing import Optional, Callable

try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False

# 支持的压缩格式
SUPPORTED_EXTRACT = {
    '.zip': 'ZIP',
    '.rar': 'RAR',
    '.7z': '7z',
    '.tar': 'TAR',
    '.gz': 'GZip',
    '.bz2': 'BZip2',
    '.xz': 'XZ',
    '.tgz': 'TAR.GZip',
}

SUPPORTED_COMPRESS = {
    'zip': '.zip',
    '7z': '.7z',
    'tar': '.tar',
    'gz': '.tar.gz',
}


def get_archive_formats() -> list[str]:
    """获取支持的压缩格式列表"""
    return sorted(SUPPORTED_EXTRACT.keys())


def get_compress_formats() -> list[str]:
    """获取支持的压缩格式列表"""
    return sorted(SUPPORTED_COMPRESS.keys())


def _get_ext_group(path: str) -> str:
    """判断压缩包类型，处理双扩展名"""
    name = Path(path).name.lower()
    # tar.* 双扩展名
    for double_ext in ['.tar.gz', '.tar.bz2', '.tar.xz', '.tgz']:
        if name.endswith(double_ext):
            return double_ext
    return Path(path).suffix.lower()


def list_archive_contents(archive_path: str) -> list[dict]:
    """
    列出压缩包内容
    返回: [{'name': str, 'size': int, 'is_dir': bool}, ...]
    """
    ext = _get_ext_group(archive_path)
    items = []

    try:
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for info in zf.infolist():
                    items.append({
                        'name': info.filename,
                        'size': info.file_size,
                        'is_dir': info.filename.endswith('/'),
                    })
        elif ext == '.7z' and HAS_7Z:
            with py7zr.SevenZipFile(archive_path, 'r') as szf:
                for info in szf.list():
                    # py7zr 不同版本的属性名不同
                    is_dir = getattr(info, 'is_directory', False) or getattr(info, 'is_dir', False) or info.filename.endswith('/')
                    size = getattr(info, 'uncompressed', 0) or 0
                    items.append({
                        'name': info.filename,
                        'size': size,
                        'is_dir': is_dir,
                    })
        elif ext in ('.tar', '.gz', '.bz2', '.xz', '.tgz', '.tar.gz', '.tar.bz2', '.tar.xz'):
            with tarfile.open(archive_path, 'r:*') as tf:
                for info in tf.getmembers():
                    items.append({
                        'name': info.name,
                        'size': info.size,
                        'is_dir': info.isdir(),
                    })
        elif ext == '.rar':
            items.append({'name': Path(archive_path).name, 'size': 0, 'is_dir': False})
    except Exception as e:
        raise RuntimeError(f"无法读取压缩包: {e}")

    return items


def extract_archive(
    archive_path: str,
    output_dir: str,
    password: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> int:
    """
    解压文件
    返回: 解压的文件数
    """
    ext = _get_ext_group(archive_path)
    os.makedirs(output_dir, exist_ok=True)
    count = 0

    password_fail_count = 0

    try:
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                members = zf.infolist()
                total = len(members)
                pwd_bytes = password.encode() if password else None
                for i, member in enumerate(members):
                    try:
                        zf.extract(member, output_dir, pwd=pwd_bytes)
                        count += 1
                    except RuntimeError as e:
                        # zipfile 密码错误时抛 RuntimeError("Bad password")
                        if 'password' in str(e).lower():
                            raise RuntimeError(f"解压失败: 密码错误") from e
                        # 其他运行时错误也要记录
                        password_fail_count += 1
                    except Exception:
                        password_fail_count += 1
                    if progress_callback:
                        progress_callback(i + 1, total)

                if password_fail_count > 0 and count == 0:
                    raise RuntimeError(f"解压失败: 所有 {password_fail_count} 个文件均未能解压，可能密码错误或文件损坏")

        elif ext == '.7z' and HAS_7Z:
            with py7zr.SevenZipFile(archive_path, 'r', password=password) as szf:
                szf.extractall(output_dir)
                contents = szf.list()
                count = len(contents)

        elif ext in ('.tar', '.gz', '.bz2', '.xz', '.tgz', '.tar.gz', '.tar.bz2', '.tar.xz'):
            mode = 'r:*'
            with tarfile.open(archive_path, mode) as tf:
                members = tf.getmembers()
                total = len(members)
                for i, member in enumerate(members):
                    try:
                        tf.extract(member, output_dir)
                        count += 1
                    except Exception:
                        continue
                    if progress_callback:
                        progress_callback(i + 1, total)

        elif ext == '.rar':
            # RAR 解压：尝试用 patool 或 unrar
            try:
                import patoolib
                patoolib.extract_archive(archive_path, outdir=output_dir)
                count = len(os.listdir(output_dir))
            except ImportError:
                # fallback 提示
                raise RuntimeError("RAR 解压需要安装 unrar 工具或 patool 库")

        else:
            raise RuntimeError(f"不支持的格式: {ext}")

    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"解压失败: {e}")

    return count

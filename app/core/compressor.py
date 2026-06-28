"""
压缩引擎 - 支持 zip/7z/tar.gz
"""
import os
import zipfile
import tarfile
from pathlib import Path
from typing import Optional, Callable

try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False


def get_compress_formats() -> list[str]:
    """获取支持的压缩格式列表"""
    return ['zip', '7z', 'gz']


def compress_files(
    file_paths: list[str],
    output_path: str,
    format_name: str = 'zip',
    password: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """
    压缩文件/文件夹
    format_name: zip / 7z / gz (tar.gz)
    """
    total = len(file_paths)
    if total == 0:
        return False

    # 确保输出路径有正确扩展名
    format_ext_map = {'zip': '.zip', '7z': '.7z', 'gz': '.tar.gz'}
    ext = format_ext_map.get(format_name, '.zip')
    if not output_path.endswith(ext):
        output_path += ext

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    try:
        if format_name == 'zip':
            if password:
                # zipfile 标准库不支持创建加密 zip；自动改用 7z
                if not HAS_7Z:
                    raise RuntimeError("zip 加密需要 py7zr 库，或请选择 7z 格式")
                # 修正输出扩展名
                if output_path.endswith('.zip'):
                    output_path = output_path[:-4] + '.7z'
                elif not output_path.endswith('.7z'):
                    output_path += '.7z'
                with py7zr.SevenZipFile(output_path, 'w', password=password) as szf:
                    for path in file_paths:
                        p = Path(path)
                        if p.is_dir():
                            szf.write_all(path, p.name)
                        else:
                            szf.write(path, p.name)
                    if progress_callback:
                        progress_callback(total, total)
            else:
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for i, path in enumerate(file_paths):
                        _add_to_zip(zf, path, '')
                        if progress_callback:
                            progress_callback(i + 1, total)

        elif format_name == '7z' and HAS_7Z:
            pwd = password if password else None
            with py7zr.SevenZipFile(output_path, 'w', password=pwd) as szf:
                for path in file_paths:
                    p = Path(path)
                    if p.is_dir():
                        szf.write_all(path, p.name)
                    else:
                        szf.write(path, p.name)
                if progress_callback:
                    progress_callback(total, total)

        elif format_name == 'gz':
            with tarfile.open(output_path, 'w:gz') as tf:
                for i, path in enumerate(file_paths):
                    p = Path(path)
                    tf.add(path, arcname=p.name)
                    if progress_callback:
                        progress_callback(i + 1, total)

        else:
            raise RuntimeError(f"不支持的压缩格式: {format_name}")

        return True

    except Exception as e:
        raise RuntimeError(f"压缩失败: {e}")


def _add_to_zip(zf, path: str, arc_prefix: str):
    """递归添加文件/文件夹到 zip"""
    p = Path(path)
    arc_name = os.path.join(arc_prefix, p.name) if arc_prefix else p.name

    if p.is_dir():
        try:
            children = list(p.iterdir())
        except PermissionError:
            return
        if not children:
            zf.writestr(arc_name + '/', '')
        else:
            for child in children:
                _add_to_zip(zf, str(child), arc_name)
    else:
        zf.write(path, arc_name)

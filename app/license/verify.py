"""
授权验证模块

简单买断授权方案：
- 基于机器码生成 License
- 本地文件存储激活状态
- 支持离线验证
"""
import os
import json
import hashlib
import platform
from pathlib import Path

# 密钥从环境变量读取，不硬编码在代码中
_DEFAULT_SECRET = os.environ.get('FILETOOL_SECRET', '')


# 激活文件路径
def _get_license_path() -> str:
    """获取授权文件存储路径"""
    if platform.system() == 'Windows':
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    else:
        base = os.path.expanduser('~/.config')
    
    lic_dir = os.path.join(base, 'FileTool')
    os.makedirs(lic_dir, exist_ok=True)
    return os.path.join(lic_dir, 'license.json')


def get_machine_code() -> str:
    """
    生成唯一机器码
    基于: 主板序列号 + MAC地址 + 硬盘序列号 + 系统信息
    多个源组合，单一源失效不影响整体
    """
    sources = []

    if platform.system() == 'Windows':
        import subprocess
        try:
            # 1. 主板序列号
            result = subprocess.run(
                ['wmic', 'baseboard', 'get', 'serialnumber'],
                capture_output=True, text=True, timeout=5
            )
            serial = result.stdout.strip().split('\n')[-1].strip() if result.stdout else ''
            if serial and serial not in ('To be filled by O.E.M.', 'Default string', ''):
                sources.append(serial)
        except Exception:
            pass

        try:
            # 2. 硬盘序列号
            result = subprocess.run(
                ['wmic', 'diskdrive', 'get', 'serialnumber'],
                capture_output=True, text=True, timeout=5
            )
            disk_serial = result.stdout.strip().split('\n')[-1].strip() if result.stdout else ''
            if disk_serial and disk_serial.strip():
                sources.append(disk_serial)
        except Exception:
            pass

        try:
            # 3. MAC 地址
            import uuid
            mac = uuid.getnode()
            sources.append(f"MAC:{mac}")
        except Exception:
            pass
    else:
        try:
            import uuid
            mac = uuid.getnode()
            sources.append(f"MAC:{mac}")
        except Exception:
            pass

    # 兜底：系统节点名
    try:
        sources.append(f"HOST:{platform.node()}")
        sources.append(f"ARCH:{platform.machine()}")
    except Exception:
        pass

    if not sources:
        import uuid
        sources.append(str(uuid.uuid4()))

    raw = ':'.join(sources)
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def generate_license_key(machine_code: str, secret: str = '') -> str:
    """生成 License Key (服务端用)
    secret 参数优先使用传入值，否则从环境变量 FILETOOL_SECRET 读取
    """
    if not secret:
        secret = _DEFAULT_SECRET
    if not secret:
        raise RuntimeError("未设置 FILETOOL_SECRET 环境变量，无法生成激活码")
    """生成 License Key (服务端用)"""
    raw = f"{machine_code}:{secret}"
    key = hashlib.sha256(raw.encode()).hexdigest()[:24].upper()
    # 格式化: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
    return '-'.join(key[i:i+4] for i in range(0, 24, 4))


def verify_license_key(machine_code: str, license_key: str, secret: str = '') -> bool:
    """验证 License Key（本地验证）"""
    if not secret:
        secret = _DEFAULT_SECRET
    if not secret:
        raise RuntimeError("未设置 FILETOOL_SECRET 环境变量，无法验证激活码")
    expected = generate_license_key(machine_code, secret)
    # 去除分隔符再比较
    clean_input = license_key.replace('-', '').upper()
    clean_expected = expected.replace('-', '').upper()
    return clean_input == clean_expected


class LicenseManager:
    """授权管理器"""

    def __init__(self):
        self.license_path = _get_license_path()
        self._activated = False
        self._machine_code = get_machine_code()
        self._load()

    def _load(self):
        """从文件加载激活状态"""
        try:
            if os.path.exists(self.license_path):
                with open(self.license_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('machine_code') == self._machine_code:
                        self._activated = data.get('activated', False)
        except Exception:
            self._activated = False

    def _save(self):
        """保存激活状态到文件"""
        try:
            data = {
                'machine_code': self._machine_code,
                'activated': self._activated,
            }
            with open(self.license_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def is_activated(self) -> bool:
        return self._activated

    def get_machine_code_display(self) -> str:
        """获取可显示的机器码"""
        code = self._machine_code
        return '-'.join(code[i:i+4] for i in range(0, len(code), 4))

    def activate(self, license_key: str) -> tuple[bool, str]:
        """
        尝试激活
        返回: (成功, 消息)
        """
        if self._activated:
            return True, "已激活，无需重复激活"

        if verify_license_key(self._machine_code, license_key):
            self._activated = True
            self._save()
            return True, "🎉 激活成功！感谢您的购买！"
        else:
            return False, "❌ 激活码无效，请检查后重试"

    def deactivate(self):
        """反激活"""
        self._activated = False
        self._save()

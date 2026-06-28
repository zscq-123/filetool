#!/usr/bin/env python3
"""
License Key 生成工具
用于给买家生成激活码

使用前需设置环境变量：
    set FILETOOL_SECRET=你的密钥

使用方法：
    python build/generate_license.py <机器码>

机器码由用户的软件界面上显示。
"""
import sys
import os

# 把项目根目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.license.verify import generate_license_key, get_machine_code


def main():
    # 检查密钥
    if not os.environ.get('FILETOOL_SECRET'):
        print("❌ 错误：未设置 FILETOOL_SECRET 环境变量")
        print("   请先执行: set FILETOOL_SECRET=你的密钥")
        sys.exit(1)

    if len(sys.argv) > 1:
        machine_code = sys.argv[1].replace('-', '').upper()
    else:
        print("=== 本机测试 ===")
        machine_code = get_machine_code()
        print(f"本机机器码:  {get_machine_code()}")
        print()

    try:
        key = generate_license_key(machine_code)
        print(f"机器码:      {machine_code}")
        print(f"激活码:      {key}")
        print()
        print("使用说明:")
        print("  1. 买家打开软件，复制机器码发给你")
        print("  2. 运行此脚本，传入机器码生成激活码")
        print("  3. 把激活码发给买家，在软件中激活")
        print()
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

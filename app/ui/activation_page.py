"""
激活引导页面 - 全屏引导页，首次运行时显示
含付款码 + 机器码 + 激活步骤
"""
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QGroupBox, QFrame,
    QScrollArea, QApplication,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from ..license.verify import LicenseManager


class ActivationPage(QWidget):
    """激活引导页面（全屏，未激活时显示）"""
    activated = Signal()  # 激活成功后发出

    def __init__(self, license_mgr: LicenseManager, parent=None):
        super().__init__(parent)
        self.license_mgr = license_mgr
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # ── 标题区 ──
        title = QLabel("📁 文件工具箱")
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: #4a9eff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("简单好用的文件处理工具 · 买断制 ¥10")
        subtitle.setStyleSheet("font-size: 15px; color: #888;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # ── 价格卡片 ──
        price_card = QFrame()
        price_card.setStyleSheet("""
            QFrame {
                background: #f0f5ff;
                border: 2px solid #4a9eff;
                border-radius: 12px;
            }
        """)
        price_layout = QVBoxLayout(price_card)
        price_layout.setAlignment(Qt.AlignCenter)
        price_layout.setSpacing(4)

        price_label = QLabel("¥10")
        price_label.setStyleSheet("font-size: 42px; font-weight: 800; color: #4a9eff;")
        price_label.setAlignment(Qt.AlignCenter)
        price_layout.addWidget(price_label)

        price_hint = QLabel("一次购买 · 永久使用 · 免费更新")
        price_hint.setStyleSheet("font-size: 13px; color: #666;")
        price_hint.setAlignment(Qt.AlignCenter)
        price_layout.addWidget(price_hint)

        layout.addWidget(price_card)

        # ── 功能展示 ──
        features = QLabel("📦 文件解压 · 📁 文件压缩 · 🖼 图片转换 · 🎵 音频转换 · 🎬 视频转换 · 📄 PDF")
        features.setWordWrap(True)
        features.setStyleSheet("font-size: 14px; color: #555; padding: 8px;")
        features.setAlignment(Qt.AlignCenter)
        layout.addWidget(features)

        layout.addSpacing(16)

        # ── 付款码区 ──
        pay_group = QGroupBox("💳 扫码付款")
        pay_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px; font-weight: 600;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 24px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        pay_layout = QVBoxLayout(pay_group)
        pay_layout.setAlignment(Qt.AlignCenter)
        pay_layout.setSpacing(12)

        pay_desc = QLabel("请使用 微信 / 支付宝 扫描下方二维码付款 ¥10")
        pay_desc.setStyleSheet("font-size: 14px; color: #333;")
        pay_desc.setAlignment(Qt.AlignCenter)
        pay_layout.addWidget(pay_desc)

        # 二维码展示区（占位，卖家替换为自己的收款码图片）
        qr_container = QFrame()
        qr_container.setFixedSize(220, 220)
        qr_container.setStyleSheet("""
            QFrame {
                background: #f9f9f9;
                border: 2px dashed #ccc;
                border-radius: 12px;
            }
        """)
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setAlignment(Qt.AlignCenter)

        # 先尝试加载二维码图片
        qr_img_path = self._find_qr_image()
        if qr_img_path:
            qr_pixmap = QPixmap(qr_img_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            qr_label = QLabel()
            qr_label.setPixmap(qr_pixmap)
            qr_label.setAlignment(Qt.AlignCenter)
            qr_layout.addWidget(qr_label)
        else:
            qr_placeholder = QLabel("📱\n请将您的收款码\n命名为 pay_qr.png\n放入 app/assets/ 目录")
            qr_placeholder.setAlignment(Qt.AlignCenter)
            qr_placeholder.setStyleSheet("font-size: 13px; color: #999; line-height: 1.6;")
            qr_layout.addWidget(qr_placeholder)

        pay_layout.addWidget(qr_container, 0, Qt.AlignCenter)

        pay_hint = QLabel("支持微信 / 支付宝 · 付款后请复制下方机器码发给卖家")
        pay_hint.setStyleSheet("font-size: 12px; color: #999;")
        pay_hint.setAlignment(Qt.AlignCenter)
        pay_layout.addWidget(pay_hint)

        layout.addWidget(pay_group)

        # ── 机器码区 ──
        code_group = QGroupBox("🔑 您的机器码")
        code_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px; font-weight: 600;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 24px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        code_layout = QVBoxLayout(code_group)
        code_layout.setSpacing(8)

        code_desc = QLabel("付款后请将下方机器码发给卖家，卖家会回复激活码")
        code_desc.setStyleSheet("font-size: 13px; color: #666;")
        code_desc.setAlignment(Qt.AlignCenter)
        code_layout.addWidget(code_desc)

        self.machine_code_display = QLineEdit()
        self.machine_code_display.setText(self.license_mgr.get_machine_code_display())
        self.machine_code_display.setReadOnly(True)
        self.machine_code_display.setAlignment(Qt.AlignCenter)
        self.machine_code_display.setStyleSheet("""
            QLineEdit {
                font-family: Consolas, 'Courier New', monospace;
                font-size: 22px;
                font-weight: bold;
                letter-spacing: 3px;
                padding: 12px;
                background: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
                color: #333;
            }
        """)
        code_layout.addWidget(self.machine_code_display)

        btn_copy = QPushButton("📋 复制机器码")
        btn_copy.setMinimumHeight(36)
        btn_copy.setStyleSheet("""
            QPushButton {
                background: #4a9eff;
                color: white;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #3a8eef; }
        """)
        btn_copy.clicked.connect(self._copy_code)
        code_layout.addWidget(btn_copy, 0, Qt.AlignCenter)

        layout.addWidget(code_group)

        # ── 激活码输入区 ──
        activate_group = QGroupBox("✅ 已付款？在此输入激活码")
        activate_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px; font-weight: 600;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 24px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        activate_layout = QVBoxLayout(activate_group)
        activate_layout.setSpacing(8)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("在此粘贴卖家给您的激活码")
        self.key_input.setStyleSheet("""
            QLineEdit {
                font-family: Consolas, 'Courier New', monospace;
                font-size: 18px;
                padding: 10px;
                letter-spacing: 2px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus { border-color: #4a9eff; }
        """)
        activate_layout.addWidget(self.key_input)

        btn_activate = QPushButton("🚀 立即激活")
        btn_activate.setMinimumHeight(44)
        btn_activate.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background: #45a049; }
        """)
        btn_activate.clicked.connect(self._do_activate)
        activate_layout.addWidget(btn_activate)

        layout.addWidget(activate_group)

        # ── 激活后使用按钮 ──
        self.btn_use = QPushButton("🎉 激活成功！开始使用")
        self.btn_use.setMinimumHeight(50)
        self.btn_use.setStyleSheet("""
            QPushButton {
                background: #4a9eff;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover { background: #3a8eef; }
        """)
        self.btn_use.clicked.connect(self.activated.emit)
        self.btn_use.setVisible(False)
        layout.addWidget(self.btn_use)

        layout.addStretch()

        scroll.setWidget(wrapper)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _find_qr_image(self):
        """查找二维码图片，支持打包后路径"""
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        search_paths = [
            os.path.join(base, 'app', 'assets', 'pay_qr.png'),
            os.path.join(base, 'app', 'assets', 'pay_qr.jpg'),
            os.path.join(base, 'app', 'assets', 'pay_qr.jpeg'),
        ]
        for p in search_paths:
            if os.path.exists(p):
                return p
        return None

    def _copy_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.license_mgr.get_machine_code_display())
        # 简单反馈

    def _do_activate(self):
        key = self.key_input.text().strip()
        if not key:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请输入卖家给您的激活码")
            return

        success, msg = self.license_mgr.activate(key)
        if success:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "激活成功", "\U0001f389 欢迎使用文件工具箱！")
            self.activated.emit()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "激活失败", msg)

    def _show_activated(self):
        """激活成功后切换显示"""
        self.activated.emit()

"""
授权激活对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QMessageBox, QGroupBox,
    QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard

from ..license.verify import LicenseManager


class LicenseDialog(QDialog):
    def __init__(self, license_mgr: LicenseManager, parent=None):
        super().__init__(parent)
        self.license_mgr = license_mgr
        self.setWindowTitle("激活文件工具箱")
        self.setFixedSize(500, 350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # 标题
        title = QLabel("🔑 文件工具箱 - 激活")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("感谢购买！请输入您的激活码完成激活。\n激活后即可使用全部功能。")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # 机器码显示
        code_group = QGroupBox("本机机器码（请发给卖家生成激活码）")
        code_layout = QHBoxLayout()

        self.machine_code_label = QLabel(self.license_mgr.get_machine_code_display())
        self.machine_code_label.setStyleSheet("""
            QLabel {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                padding: 8px;
                background: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        self.machine_code_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        code_layout.addWidget(self.machine_code_label, 1)

        self.btn_copy = QPushButton("📋 复制")
        self.btn_copy.clicked.connect(self._copy_code)
        code_layout.addWidget(self.btn_copy)

        code_group.setLayout(code_layout)
        layout.addWidget(code_group)

        # 激活码输入
        input_group = QGroupBox("输入激活码")
        input_layout = QVBoxLayout()

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX-XXXX")
        self.key_input.setStyleSheet("""
            QLineEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 16px;
                padding: 8px;
                letter-spacing: 2px;
            }
        """)
        self.key_input.setMaxLength(29)
        input_layout.addWidget(self.key_input)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_activate = QPushButton("✅ 激活")
        self.btn_activate.setMinimumHeight(36)
        self.btn_activate.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        self.btn_activate.clicked.connect(self._activate)
        btn_layout.addWidget(self.btn_activate)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _copy_code(self):
        """复制机器码到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.license_mgr.get_machine_code_display())
        self.btn_copy.setText("✅ 已复制")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.btn_copy.setText("📋 复制"))

    def _activate(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "提示", "请输入激活码")
            return

        success, msg = self.license_mgr.activate(key)
        if success:
            QMessageBox.information(self, "激活成功", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "激活失败", msg)

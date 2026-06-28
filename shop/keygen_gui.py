#!/usr/bin/env python3
"""
激活码生成工具（卖家用）
根据买家提供的机器码生成激活码

启动前需设置环境变量：
    set FILETOOL_SECRET=你的密钥
"""
import sys
import os
import json
from datetime import datetime

# 把项目根目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog,
)
from PySide6.QtCore import Qt, QTimer

from app.license.verify import generate_license_key

# 销售记录文件
SALES_FILE = os.path.join(os.path.dirname(__file__), 'sales.json')


def load_sales():
    """加载销售记录"""
    if os.path.exists(SALES_FILE):
        try:
            with open(SALES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_sales(records):
    """保存销售记录"""
    with open(SALES_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


class KeygenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔑 文件工具箱 - 激活码生成器")
        self.setFixedSize(600, 500)
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # 标题
        title = QLabel("🔑 激活码生成器（卖家专用）")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4a9eff;")
        layout.addWidget(title)

        # 输入区域
        input_group = QGroupBox("生成激活码")
        input_layout = QVBoxLayout()

        # 机器码输入
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("买家机器码："))
        self.machine_code_input = QLineEdit()
        self.machine_code_input.setPlaceholderText("例：C970-5B57-C627-BE51")
        self.machine_code_input.setStyleSheet("font-family: Consolas; font-size: 14px; padding: 6px;")
        code_layout.addWidget(self.machine_code_input, 1)
        input_layout.addLayout(code_layout)

        # 备注
        note_layout = QHBoxLayout()
        note_layout.addWidget(QLabel("备注（买家昵称）："))
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("可选：记录买家信息")
        note_layout.addWidget(self.note_input, 1)
        input_layout.addLayout(note_layout)

        # 生成按钮
        btn_layout = QHBoxLayout()
        self.btn_generate = QPushButton("🎯 生成激活码")
        self.btn_generate.setMinimumHeight(36)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background: #4CAF50; color: white; font-weight: bold;
                font-size: 14px; border-radius: 4px;
            }
            QPushButton:hover { background: #45a049; }
        """)
        self.btn_generate.clicked.connect(self._generate_key)
        btn_layout.addWidget(self.btn_generate)

        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._clear_inputs)
        btn_layout.addWidget(self.btn_clear)

        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 结果显示
        result_group = QGroupBox("生成的激活码")
        result_layout = QVBoxLayout()

        self.result_display = QLineEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText("激活码将显示在这里...")
        self.result_display.setStyleSheet("""
            QLineEdit {
                font-family: Consolas; font-size: 20px; font-weight: bold;
                padding: 10px; background: #f0f8ff;
                border: 2px solid #4a9eff; border-radius: 6px;
                letter-spacing: 2px;
            }
        """)
        result_layout.addWidget(self.result_display)

        copy_btn_layout = QHBoxLayout()
        self.btn_copy = QPushButton("📋 复制激活码")
        self.btn_copy.setMinimumHeight(32)
        self.btn_copy.clicked.connect(self._copy_key)
        self.btn_copy.setEnabled(False)
        copy_btn_layout.addWidget(self.btn_copy)
        copy_btn_layout.addStretch()
        result_layout.addLayout(copy_btn_layout)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # 销售历史
        history_group = QGroupBox("📊 销售记录")
        history_layout = QVBoxLayout()

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "机器码", "激活码", "备注"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        history_layout.addWidget(self.history_table)

        btn_export = QPushButton("📤 导出记录")
        btn_export.clicked.connect(self._export_sales)
        history_layout.addWidget(btn_export)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        self.setLayout(layout)

    def _generate_key(self):
        # 检查密钥
        if not os.environ.get('FILETOOL_SECRET'):
            QMessageBox.critical(self, "错误",
                "未设置 FILETOOL_SECRET 环境变量\n\n"
                "请先执行: set FILETOOL_SECRET=你的密钥")
            return

        raw_code = self.machine_code_input.text().strip()
        if not raw_code:
            QMessageBox.warning(self, "提示", "请输入买家机器码")
            return

        # 清理格式
        clean_code = raw_code.replace('-', '').replace(' ', '').upper()
        if len(clean_code) != 16:
            QMessageBox.warning(self, "提示", "机器码长度不正确（应为16位）")
            return

        try:
            key = generate_license_key(clean_code)
        except RuntimeError as e:
            QMessageBox.critical(self, "错误", str(e))
            return
        self.result_display.setText(key)
        self.btn_copy.setEnabled(True)

        # 保存记录
        note = self.note_input.text().strip()
        record = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'machine_code': raw_code,
            'license_key': key,
            'note': note,
        }
        records = load_sales()
        records.append(record)
        save_sales(records)
        self._load_history()

        note_text = f" 备注: {note}" if note else ""
        # auto copy
        self._copy_key()

    def _copy_key(self):
        key = self.result_display.text()
        if key:
            clipboard = QApplication.clipboard()
            clipboard.setText(key)
            self.btn_copy.setText("✅ 已复制到剪贴板！")
            QTimer.singleShot(3000, lambda: self.btn_copy.setText("📋 复制激活码"))

    def _clear_inputs(self):
        self.machine_code_input.clear()
        self.note_input.clear()

    def _load_history(self):
        records = load_sales()
        self.history_table.setRowCount(len(records))
        for i, rec in enumerate(reversed(records)):
            self.history_table.setItem(i, 0, QTableWidgetItem(rec['time']))
            self.history_table.setItem(i, 1, QTableWidgetItem(rec['machine_code']))
            self.history_table.setItem(i, 2, QTableWidgetItem(rec['license_key']))
            self.history_table.setItem(i, 3, QTableWidgetItem(rec.get('note', '')))

    def _export_sales(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出销售记录", "sales.json", "JSON (*.json)"
        )
        if path:
            records = load_sales()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "导出成功", f"已导出 {len(records)} 条记录")


def main():
    app = QApplication(sys.argv)
    window = KeygenWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

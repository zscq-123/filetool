"""
压缩标签页 - 图形界面
"""
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QListWidget,
    QListWidgetItem, QProgressBar, QMessageBox,
    QGroupBox, QComboBox, QGridLayout, QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

from ..core.compressor import compress_files, get_compress_formats
from .widgets import DropArea


class CompressWorker(QThread):
    progress = Signal(int, int)
    finished = Signal()
    error = Signal(str)

    def __init__(self, file_paths, output_path, format_name, password=None):
        super().__init__()
        self.file_paths = file_paths
        self.output_path = output_path
        self.format_name = format_name
        self.password = password

    def run(self):
        try:
            compress_files(
                self.file_paths,
                self.output_path,
                self.format_name,
                self.password,
                progress_callback=self._on_progress,
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, current, total):
        self.progress.emit(current, total)


class CompressTab(QWidget):
    def __init__(self):
        super().__init__()
        self.file_list: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # ── 文件选择 ──
        file_group = QGroupBox("选择要压缩的文件/文件夹")
        file_layout = QVBoxLayout()

        self.drop_area = DropArea(
            hint="📂 拖拽文件/文件夹到这里\n或点击下方按钮添加",
            min_height=80,
        )
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        file_layout.addWidget(self.drop_area)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("📂 添加文件")
        self.btn_add.clicked.connect(self._add_files)
        self.btn_add.setMinimumHeight(36)

        self.btn_add_dir = QPushButton("📁 添加文件夹")
        self.btn_add_dir.clicked.connect(self._add_dir)
        self.btn_add_dir.setMinimumHeight(36)

        self.btn_clear = QPushButton("🗑 清空列表")
        self.btn_clear.clicked.connect(self._clear_list)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_add_dir)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        file_layout.addLayout(btn_layout)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setAlternatingRowColors(True)
        file_layout.addWidget(self.file_list_widget)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # ── 压缩选项 ──
        options_group = QGroupBox("压缩选项")
        options_layout = QGridLayout()
        options_layout.setSpacing(8)

        options_layout.addWidget(QLabel("压缩格式："), 0, 0)
        self.format_combo = QComboBox()
        for fmt in get_compress_formats():
            self.format_combo.addItem(fmt)
        options_layout.addWidget(self.format_combo, 0, 1)

        options_layout.addWidget(QLabel("输出路径："), 1, 0)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("默认：保存到桌面")
        options_layout.addWidget(self.output_path, 1, 1)

        self.btn_output = QPushButton("选择...")
        self.btn_output.clicked.connect(self._select_output)
        options_layout.addWidget(self.btn_output, 1, 2)

        options_layout.addWidget(QLabel("密码（可选）："), 2, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("加密压缩包（7z 格式支持，选 zip 时自动切换为 7z）")
        options_layout.addWidget(self.password_input, 2, 1)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # ── 进度 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.btn_compress = QPushButton("📦 开始压缩")
        self.btn_compress.setMinimumHeight(40)
        self.btn_compress.setStyleSheet("""
            QPushButton {
                background: #4a9eff;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #3a8eef;
            }
            QPushButton:disabled {
                background: #ccc;
            }
        """)
        self.btn_compress.clicked.connect(self._start_compress)
        self.btn_compress.setEnabled(False)
        layout.addWidget(self.btn_compress)

        layout.addStretch()
        self.setLayout(layout)

        # 快捷键
        self.addAction(QAction("添加文件", self, shortcut="Ctrl+O", triggered=self._add_files))

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        for f in files:
            if f not in self.file_list:
                self.file_list.append(f)
                self.file_list_widget.addItem(f"📄 {f}")

        self._update_compress_button()

    def _on_files_dropped(self, files):
        """拖拽添加文件/文件夹"""
        for f in files:
            if f not in self.file_list:
                icon = "📁" if os.path.isdir(f) else "📄"
                self.file_list.append(f)
                self.file_list_widget.addItem(f"{icon} {f}")
        self._update_compress_button()

    def _add_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if path:
            if path not in self.file_list:
                self.file_list.append(path)
                self.file_list_widget.addItem(f"📁 {path}")
                self._update_compress_button()

    def _clear_list(self):
        self.file_list.clear()
        self.file_list_widget.clear()
        self._update_compress_button()

    def _select_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存压缩包", "",
            "压缩包 (*.zip *.7z *.tar.gz);;所有文件 (*.*)"
        )
        if path:
            self.output_path.setText(path)

    def _update_compress_button(self):
        self.btn_compress.setEnabled(len(self.file_list) > 0)

    def _get_default_output(self) -> str:
        """生成默认输出路径"""
        from pathlib import Path
        desktop = os.path.join(Path.home(), "Desktop")
        fmt = self.format_combo.currentText()
        ext_map = {'zip': '.zip', '7z': '.7z', 'gz': '.tar.gz'}
        name = "archive"
        if self.file_list:
            name = Path(self.file_list[0]).stem

        return os.path.join(desktop, f"{name}{ext_map.get(fmt, '.zip')}")

    def _start_compress(self):
        if not self.file_list:
            return

        output_path = self.output_path.text().strip()
        if not output_path:
            output_path = self._get_default_output()

        fmt = self.format_combo.currentText()
        password = self.password_input.text().strip() or None

        # 确保扩展名正确
        ext_map = {'zip': '.zip', '7z': '.7z', 'gz': '.tar.gz'}
        ext = ext_map.get(fmt, '.zip')
        if not output_path.endswith(ext):
            output_path += ext

        self.btn_compress.setEnabled(False)
        self.btn_compress.setText("⏳ 压缩中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = CompressWorker(
            self.file_list, output_path, fmt, password
        )
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_compress_finished)
        self.worker.error.connect(self._on_compress_error)
        self.worker.start()

    def _update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_compress_finished(self):
        self.btn_compress.setEnabled(True)
        self.btn_compress.setText("📦 开始压缩")
        self.progress_bar.setVisible(False)

        output_path = self.output_path.text().strip()
        if not output_path:
            output_path = self._get_default_output()

        QMessageBox.information(
            self, "压缩完成",
            f"✅ 压缩完成！\n📁 {output_path}"
        )

        # 打开位置
        output_dir = os.path.dirname(output_path)
        if os.path.exists(output_dir):
            os.startfile(output_dir)

    def _on_compress_error(self, error_msg):
        self.btn_compress.setEnabled(True)
        self.btn_compress.setText("📦 开始压缩")
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "压缩失败", f"❌ {error_msg}")

"""
解压标签页 - 图形界面
"""
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QListWidget,
    QListWidgetItem, QProgressBar, QMessageBox,
    QGroupBox, QGridLayout, QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

from ..core.extractor import (
    extract_archive, list_archive_contents,
    get_archive_formats,
)
from .widgets import DropArea


class ExtractWorker(QThread):
    """后台解压线程"""
    progress = Signal(int, int)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, archive_path, output_dir, password=None):
        super().__init__()
        self.archive_path = archive_path
        self.output_dir = output_dir
        self.password = password

    def run(self):
        try:
            count = extract_archive(
                self.archive_path,
                self.output_dir,
                self.password,
                progress_callback=self._on_progress,
            )
            self.finished.emit(count)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, current, total):
        self.progress.emit(current, total)




class ExtractTab(QWidget):
    def __init__(self):
        super().__init__()
        self.current_archive = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # ── 文件选择区域 ──
        file_group = QGroupBox("选择压缩包")
        file_layout = QVBoxLayout()

        self.drop_area = DropArea(
            hint="📂 拖拽压缩包到这里\n或点击「选择文件」按钮",
            min_height=100,
        )
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        file_layout.addWidget(self.drop_area)

        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("📂 选择文件")
        self.btn_select.clicked.connect(self._select_archive)
        self.btn_select.setMinimumHeight(36)

        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("未选择文件...")

        btn_layout.addWidget(self.btn_select)
        btn_layout.addWidget(self.file_path, 1)
        file_layout.addLayout(btn_layout)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # ── 选项区域 ──
        options_group = QGroupBox("解压选项")
        options_layout = QGridLayout()
        options_layout.setSpacing(8)

        options_layout.addWidget(QLabel("解压到："), 0, 0)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("默认：压缩包所在目录")
        options_layout.addWidget(self.output_path, 0, 1)

        self.btn_output = QPushButton("选择...")
        self.btn_output.clicked.connect(self._select_output)
        options_layout.addWidget(self.btn_output, 0, 2)

        options_layout.addWidget(QLabel("密码（可选）："), 1, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("加密压缩包的密码")
        options_layout.addWidget(self.password_input, 1, 1)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # ── 文件预览区域 ──
        preview_group = QGroupBox("压缩包内容预览")
        preview_layout = QVBoxLayout()
        self.preview_list = QListWidget()
        self.preview_list.setAlternatingRowColors(True)
        preview_layout.addWidget(self.preview_list)

        preview_btn_layout = QHBoxLayout()
        self.btn_preview = QPushButton("👁 预览内容")
        self.btn_preview.clicked.connect(self._preview_contents)
        preview_btn_layout.addWidget(self.btn_preview)
        preview_btn_layout.addStretch()
        preview_layout.addLayout(preview_btn_layout)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # ── 进度与操作区域 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.btn_extract = QPushButton("🚀 开始解压")
        self.btn_extract.setMinimumHeight(40)
        self.btn_extract.setStyleSheet("""
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
        self.btn_extract.clicked.connect(self._start_extract)
        self.btn_extract.setEnabled(False)
        layout.addWidget(self.btn_extract)

        layout.addStretch()
        self.setLayout(layout)

        # 快捷键
        self.addAction(QAction("打开", self, shortcut="Ctrl+O", triggered=self._select_archive))

    def _on_files_dropped(self, files):
        if files:
            self._set_archive(files[0])

    def _select_archive(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择压缩包", "",
            "压缩包 (*.zip *.rar *.7z *.tar *.gz *.bz2 *.xz *.tgz *.tar.gz);;所有文件 (*.*)"
        )
        if path:
            self._set_archive(path)

    def _set_archive(self, path):
        self.current_archive = path
        self.file_path.setText(path)

        # 自动设置输出路径
        if not self.output_path.text():
            default_dir = os.path.dirname(path)
            self.output_path.setText(default_dir)

        self.btn_extract.setEnabled(True)

    def _select_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择解压目录")
        if path:
            self.output_path.setText(path)

    def _preview_contents(self):
        if not self.current_archive:
            return

        self.preview_list.clear()
        self.preview_list.addItem("⏳ 正在读取...")
        QApplication.processEvents()

        try:
            items = list_archive_contents(self.current_archive)
            self.preview_list.clear()

            if not items:
                self.preview_list.addItem("(空压缩包)")
                return

            for item in items:
                icon = "📁" if item['is_dir'] else "📄"
                size_str = f"({self._format_size(item['size'])})" if not item['is_dir'] else ""
                self.preview_list.addItem(f"{icon} {item['name']} {size_str}")

        except Exception as e:
            self.preview_list.clear()
            self.preview_list.addItem(f"❌ 读取失败: {e}")

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def _start_extract(self):
        if not self.current_archive:
            return
        if not os.path.exists(self.current_archive):
            QMessageBox.warning(self, "错误", "压缩包文件不存在")
            return

        output_dir = self.output_path.text().strip()
        if not output_dir:
            output_dir = os.path.dirname(self.current_archive)

        # 创建子目录：解压到压缩包名目录下
        archive_name = Path(self.current_archive).stem
        output_dir = os.path.join(output_dir, archive_name)

        password = self.password_input.text().strip() or None

        self.btn_extract.setEnabled(False)
        self.btn_extract.setText("⏳ 解压中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = ExtractWorker(self.current_archive, output_dir, password)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_extract_finished)
        self.worker.error.connect(self._on_extract_error)
        self.worker.start()

    def _update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_extract_finished(self, count):
        self.btn_extract.setEnabled(True)
        self.btn_extract.setText("🚀 开始解压")
        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self, "解压完成",
            f"✅ 成功解压 {count} 个文件"
        )

        # 打开输出目录
        output_dir = self.output_path.text().strip()
        if not output_dir:
            output_dir = os.path.dirname(self.current_archive)
        archive_name = Path(self.current_archive).stem
        output_dir = os.path.join(output_dir, archive_name)
        os.startfile(output_dir)

    def _on_extract_error(self, error_msg):
        self.btn_extract.setEnabled(True)
        self.btn_extract.setText("🚀 开始解压")
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "解压失败", f"❌ {error_msg}")

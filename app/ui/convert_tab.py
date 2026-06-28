"""
转换标签页 - 图片/音频/视频/PDF 格式转换 (子标签页)
"""
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QListWidget,
    QListWidgetItem, QProgressBar, QMessageBox,
    QGroupBox, QComboBox, QGridLayout,
    QTabWidget, QSpinBox, QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

from ..core.converter import (
    convert_image, convert_images_batch,
    convert_audio, convert_video,
    images_to_pdf, pdf_to_images,
    pdf_to_docx, pdf_to_pptx, pdf_to_excel,
    get_image_formats, get_audio_formats, get_video_formats,
    IMAGE_FORMATS, AUDIO_FORMATS, VIDEO_FORMATS,
)
from .widgets import DropArea


class ConvertWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(str)  # 结果消息
    error = Signal(str)

    def __init__(self, convert_type: str, **kwargs):
        super().__init__()
        self.convert_type = convert_type
        self.kwargs = kwargs

    def run(self):
        try:
            # 统一用 worker 自身的 signal 作为 progress callback
            if 'progress_callback' in self.kwargs:
                self.kwargs['progress_callback'] = self._on_progress

            result = ""
            if self.convert_type == 'image_batch':
                count = convert_images_batch(**self.kwargs)
                result = f"✅ 成功转换 {count}/{len(self.kwargs['input_paths'])} 个文件"
            elif self.convert_type == 'image':
                convert_image(**self.kwargs)
                result = "✅ 转换完成"
            elif self.convert_type == 'audio':
                convert_audio(**self.kwargs)
                result = "✅ 转换完成"
            elif self.convert_type == 'video':
                convert_video(**self.kwargs)
                result = "✅ 转换完成"
            elif self.convert_type == 'images_to_pdf':
                images_to_pdf(**self.kwargs)
                result = "✅ PDF 生成完成"
            elif self.convert_type == 'pdf_to_images':
                count = pdf_to_images(**self.kwargs)
                result = f"✅ 成功导出 {count} 页图片"
            elif self.convert_type == 'pdf_to_docx':
                pdf_to_docx(**self.kwargs)
                result = "✅ 成功转换为 Word (.docx) 文件"
            elif self.convert_type == 'pdf_to_excel':
                pdf_to_excel(**self.kwargs)
                result = "✅ 成功转换为 Excel (.xlsx) 文件"
            elif self.convert_type == 'pdf_to_pptx':
                pdf_to_pptx(**self.kwargs)
                result = "✅ 成功转换为 PPT (.pptx) 文件"

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, current, total):
        self.progress.emit(current, total)


# ── 图片转换子标签页 ────────────────

class ImageConvertWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.file_list: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 文件选择
        self.drop_area = DropArea(
            hint="🖼 拖拽图片到这里\n或点击下方按钮选择",
            min_height=80,
        )
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_area)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("📂 选择图片")
        self.btn_add.clicked.connect(self._add_files)
        btn_layout.addWidget(self.btn_add)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._clear)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.file_list_widget)

        # 转换选项
        opt_layout = QGridLayout()
        opt_layout.setSpacing(6)

        opt_layout.addWidget(QLabel("目标格式："), 0, 0)
        self.format_combo = QComboBox()
        for fmt in get_image_formats():
            self.format_combo.addItem(fmt)
        opt_layout.addWidget(self.format_combo, 0, 1)

        opt_layout.addWidget(QLabel("质量："), 0, 2)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(10, 100)
        self.quality_spin.setValue(90)
        self.quality_spin.setSuffix("%")
        opt_layout.addWidget(self.quality_spin, 0, 3)

        opt_layout.addWidget(QLabel("输出目录："), 1, 0)
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("默认：原文件所在目录")
        opt_layout.addWidget(self.output_dir, 1, 1, 1, 2)
        self.btn_output = QPushButton("选择...")
        self.btn_output.clicked.connect(self._select_output)
        opt_layout.addWidget(self.btn_output, 1, 3)

        layout.addLayout(opt_layout)

        self.btn_convert = QPushButton("🔄 开始转换")
        self.btn_convert.setMinimumHeight(36)
        self.btn_convert.setStyleSheet("background: #4a9eff; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_convert.clicked.connect(self._start_convert)
        self.btn_convert.setEnabled(False)
        layout.addWidget(self.btn_convert)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 快捷键
        self.addAction(QAction("选择图片", self, shortcut="Ctrl+O", triggered=self._add_files))

        self.setLayout(layout)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片 (*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff *.ico);;所有文件 (*.*)"
        )
        for f in files:
            if f not in self.file_list:
                self.file_list.append(f)
                self.file_list_widget.addItem(f"🖼 {Path(f).name}")
        self.btn_convert.setEnabled(len(self.file_list) > 0)

    def _clear(self):
        self.file_list.clear()
        self.file_list_widget.clear()
        self.btn_convert.setEnabled(False)

    def _on_files_dropped(self, files):
        """拖拽添加图片"""
        for f in files:
            if f not in self.file_list:
                self.file_list.append(f)
                self.file_list_widget.addItem(f"🖼 {Path(f).name}")
        self.btn_convert.setEnabled(len(self.file_list) > 0)

    def _select_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_dir.setText(path)

    def _start_convert(self):
        if not self.file_list:
            return

        target_fmt = self.format_combo.currentText()
        out_dir = self.output_dir.text().strip()
        if not out_dir:
            out_dir = os.path.dirname(self.file_list[0])

        quality = self.quality_spin.value()

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("⏳ 转换中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = ConvertWorker(
            'image_batch',
            input_paths=self.file_list,
            output_dir=out_dir,
            target_format=target_fmt,
            quality=quality,
            progress_callback=None,
        )
        self._last_output_dir = out_dir
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_finished(self, msg):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("🔄 开始转换")
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "完成", msg)
        out_dir = getattr(self, '_last_output_dir', '')
        if out_dir and os.path.exists(out_dir):
            os.startfile(out_dir)

    def _on_error(self, msg):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("🔄 开始转换")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", msg)


# ── 音频转换子标签页 ────────────────

class AudioConvertWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 文件选择
        self.drop_area = DropArea(
            hint="🎵 拖拽音频文件到这里\n或点击下方按钮选择",
            min_height=80,
        )
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_area)

        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("🎵 选择音频文件")
        self.btn_select.clicked.connect(self._select_file)
        btn_layout.addWidget(self.btn_select)
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("未选择文件...")
        btn_layout.addWidget(self.file_path, 1)
        layout.addLayout(btn_layout)

        # 选项
        opt_layout = QGridLayout()
        opt_layout.setSpacing(6)

        opt_layout.addWidget(QLabel("目标格式："), 0, 0)
        self.format_combo = QComboBox()
        for fmt in get_audio_formats():
            self.format_combo.addItem(fmt)
        opt_layout.addWidget(self.format_combo, 0, 1)

        opt_layout.addWidget(QLabel("比特率："), 0, 2)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['128k', '192k', '256k', '320k'])
        self.bitrate_combo.setCurrentText('192k')
        opt_layout.addWidget(self.bitrate_combo, 0, 3)

        opt_layout.addWidget(QLabel("输出路径："), 1, 0)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("默认：原文件同目录")
        opt_layout.addWidget(self.output_path, 1, 1, 1, 2)
        self.btn_output = QPushButton("选择...")
        self.btn_output.clicked.connect(self._select_output)
        opt_layout.addWidget(self.btn_output, 1, 3)

        layout.addLayout(opt_layout)

        self.btn_convert = QPushButton("🔄 开始转换")
        self.btn_convert.setMinimumHeight(36)
        self.btn_convert.setStyleSheet("background: #4a9eff; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_convert.clicked.connect(self._start_convert)
        self.btn_convert.setEnabled(False)
        layout.addWidget(self.btn_convert)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        # 快捷键
        self.addAction(QAction("选择音频", self, shortcut="Ctrl+O", triggered=self._select_file))

        self.setLayout(layout)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频", "",
            "音频 (*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma);;所有文件 (*.*)"
        )
        if path:
            self.file_path.setText(path)
            self.btn_convert.setEnabled(True)

    def _on_files_dropped(self, files):
        """拖拽音频文件"""
        if files:
            f = files[0]
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'):
                self.file_path.setText(f)
                self.btn_convert.setEnabled(True)

    def _select_output(self):
        fmt = self.format_combo.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", f"{fmt.upper()} (*.{fmt})"
        )
        if path:
            self.output_path.setText(path)

    def _start_convert(self):
        in_path = self.file_path.text().strip()
        if not in_path:
            return

        fmt = self.format_combo.currentText()
        out_path = self.output_path.text().strip()
        if not out_path:
            out_path = os.path.join(os.path.dirname(in_path), f"{Path(in_path).stem}.{fmt}")

        bitrate = self.bitrate_combo.currentText()

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("⏳ 转换中...")
        self.progress_bar.setVisible(True)

        self.worker = ConvertWorker(
            'audio',
            input_path=in_path,
            output_path=out_path,
            bitrate=bitrate,
            progress_callback=None,
        )
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(lambda msg: self._on_done(msg, out_path))
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_done(self, msg, out_path):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("🔄 开始转换")
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "完成", msg)
        out_dir = os.path.dirname(out_path)
        if os.path.exists(out_dir):
            os.startfile(out_dir)

    def _on_error(self, msg):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("🔄 开始转换")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", msg)


# ── 视频转换子标签页 ────────────────

class VideoConvertWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.drop_area = DropArea(
            hint="🎬 拖拽视频文件到这里\n或点击下方按钮选择",
            min_height=80,
        )
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_area)

        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("🎬 选择视频文件")
        self.btn_select.clicked.connect(self._select_file)
        btn_layout.addWidget(self.btn_select)
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("未选择文件...")
        btn_layout.addWidget(self.file_path, 1)
        layout.addLayout(btn_layout)

        opt_layout = QGridLayout()
        opt_layout.setSpacing(6)

        opt_layout.addWidget(QLabel("目标格式："), 0, 0)
        self.format_combo = QComboBox()
        for fmt in get_video_formats():
            self.format_combo.addItem(fmt)
        opt_layout.addWidget(self.format_combo, 0, 1)

        opt_layout.addWidget(QLabel("视频码率："), 0, 2)
        self.vbitrate_combo = QComboBox()
        self.vbitrate_combo.addItems(['1M', '2M', '4M', '8M', '16M'])
        self.vbitrate_combo.setCurrentText('4M')
        opt_layout.addWidget(self.vbitrate_combo, 0, 3)

        opt_layout.addWidget(QLabel("输出路径："), 1, 0)
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("默认：原文件同目录")
        opt_layout.addWidget(self.output_path, 1, 1, 1, 2)
        self.btn_output = QPushButton("选择...")
        self.btn_output.clicked.connect(self._select_output)
        opt_layout.addWidget(self.btn_output, 1, 3)

        layout.addLayout(opt_layout)

        self.btn_convert = QPushButton("🔄 开始转换")
        self.btn_convert.setMinimumHeight(36)
        self.btn_convert.setStyleSheet("background: #4a9eff; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_convert.clicked.connect(self._start_convert)
        self.btn_convert.setEnabled(False)
        layout.addWidget(self.btn_convert)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        # 快捷键
        self.addAction(QAction("选择视频", self, shortcut="Ctrl+O", triggered=self._select_file))

        self.setLayout(layout)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "",
            "视频 (*.mp4 *.avi *.mkv *.mov *.wmv *.webm *.flv);;所有文件 (*.*)"
        )
        if path:
            self.file_path.setText(path)
            self.btn_convert.setEnabled(True)

    def _on_files_dropped(self, files):
        """拖拽视频文件"""
        if files:
            f = files[0]
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm', '.flv'):
                self.file_path.setText(f)
                self.btn_convert.setEnabled(True)

    def _select_output(self):
        fmt = self.format_combo.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", f"{fmt.upper()} (*.{fmt})"
        )
        if path:
            self.output_path.setText(path)

    def _start_convert(self):
        in_path = self.file_path.text().strip()
        if not in_path:
            return

        fmt = self.format_combo.currentText()
        out_path = self.output_path.text().strip()
        if not out_path:
            out_path = os.path.join(os.path.dirname(in_path), f"{Path(in_path).stem}.{fmt}")
        vbr = self.vbitrate_combo.currentText()

        self.btn_convert.setEnabled(False)
        self.btn_convert.setText("⏳ 转换中...")
        self.progress_bar.setVisible(True)

        self.worker = ConvertWorker(
            'video',
            input_path=in_path,
            output_path=out_path,
            video_bitrate=vbr,
            progress_callback=None,
        )
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(lambda msg: self._on_done(msg, out_path))
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_done(self, msg, out_path):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("🔄 开始转换")
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "完成", msg)
        out_dir = os.path.dirname(out_path)
        if os.path.exists(out_dir):
            os.startfile(out_dir)

    def _on_error(self, msg):
        self.btn_convert.setEnabled(True)
        self.btn_convert.setText("🔄 开始转换")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", msg)


# ── PDF 转换子标签页 ────────────────

class PDFConvertWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.image_files: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 上部：图片→PDF
        img_group = QGroupBox("🖼 图片 → PDF")
        img_layout = QVBoxLayout()

        self.img_drop_area = DropArea(
            hint="🖼 拖拽图片到这里，多张合成一个 PDF",
            min_height=60,
        )
        self.img_drop_area.files_dropped.connect(self._on_images_dropped)
        img_layout.addWidget(self.img_drop_area)

        btn_layout = QHBoxLayout()
        self.btn_add_images = QPushButton("选择图片")
        self.btn_add_images.clicked.connect(self._add_images)
        btn_layout.addWidget(self.btn_add_images)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._clear_images)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        img_layout.addLayout(btn_layout)

        self.img_list = QListWidget()
        self.img_list.setMaximumHeight(100)
        img_layout.addWidget(self.img_list)

        pdf_out_layout = QHBoxLayout()
        self.pdf_output = QLineEdit()
        self.pdf_output.setPlaceholderText("PDF 输出路径...")
        pdf_out_layout.addWidget(self.pdf_output, 1)
        self.btn_pdf_out = QPushButton("选择...")
        self.btn_pdf_out.clicked.connect(self._select_pdf_output)
        pdf_out_layout.addWidget(self.btn_pdf_out)
        img_layout.addLayout(pdf_out_layout)

        self.btn_to_pdf = QPushButton("📄 生成 PDF")
        self.btn_to_pdf.clicked.connect(self._start_images_to_pdf)
        self.btn_to_pdf.setEnabled(False)
        img_layout.addWidget(self.btn_to_pdf)
        img_group.setLayout(img_layout)
        layout.addWidget(img_group)

        # 中部：PDF→图片
        pdf_group = QGroupBox("📄 PDF → 图片")
        pdf_layout = QVBoxLayout()

        self.pdf_drop_area = DropArea(
            hint="📄 拖拽 PDF 到这里，每页导出为图片",
            min_height=60,
        )
        self.pdf_drop_area.files_dropped.connect(self._on_pdf_dropped)
        pdf_layout.addWidget(self.pdf_drop_area)

        pdf_file_layout = QHBoxLayout()
        self.btn_pdf_file = QPushButton("选择 PDF")
        self.btn_pdf_file.clicked.connect(self._select_pdf)
        pdf_file_layout.addWidget(self.btn_pdf_file)
        self.pdf_path = QLineEdit()
        self.pdf_path.setReadOnly(True)
        self.pdf_path.setPlaceholderText("未选择 PDF...")
        pdf_file_layout.addWidget(self.pdf_path, 1)
        pdf_layout.addLayout(pdf_file_layout)

        pdf_opt_layout = QHBoxLayout()
        pdf_opt_layout.addWidget(QLabel("图片格式："))
        self.pdf_img_format = QComboBox()
        self.pdf_img_format.addItems(['png', 'jpg', 'webp'])
        pdf_opt_layout.addWidget(self.pdf_img_format)
        pdf_opt_layout.addWidget(QLabel("DPI："))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(200)
        pdf_opt_layout.addWidget(self.dpi_spin)
        pdf_opt_layout.addStretch()
        pdf_layout.addLayout(pdf_opt_layout)

        self.btn_pdf_to_img = QPushButton("🖼 导出为图片")
        self.btn_pdf_to_img.clicked.connect(self._start_pdf_to_images)
        self.btn_pdf_to_img.setEnabled(False)
        pdf_layout.addWidget(self.btn_pdf_to_img)
        pdf_group.setLayout(pdf_layout)
        layout.addWidget(pdf_group)

        # 下部：PDF → Office 文档
        office_group = QGroupBox("📋 PDF → Office (Word / Excel / PPT)")
        office_layout = QVBoxLayout()

        self.office_drop_area = DropArea(
            hint="📄 拖拽 PDF 到这里，转 Word/Excel/PPT",
            min_height=60,
        )
        self.office_drop_area.files_dropped.connect(self._on_office_pdf_dropped)
        office_layout.addWidget(self.office_drop_area)

        office_file_layout = QHBoxLayout()
        self.btn_office_pdf = QPushButton("选择 PDF")
        self.btn_office_pdf.clicked.connect(self._select_office_pdf)
        office_file_layout.addWidget(self.btn_office_pdf)
        self.office_pdf_path = QLineEdit()
        self.office_pdf_path.setReadOnly(True)
        self.office_pdf_path.setPlaceholderText("未选择 PDF...")
        office_file_layout.addWidget(self.office_pdf_path, 1)
        office_layout.addLayout(office_file_layout)

        office_btn_layout = QHBoxLayout()
        office_btn_layout.setSpacing(10)

        self.btn_to_docx = QPushButton("📝 转 Word (.docx)")
        self.btn_to_docx.clicked.connect(lambda: self._start_pdf_to_office('docx'))
        self.btn_to_docx.setEnabled(False)
        self.btn_to_docx.setMinimumHeight(32)
        office_btn_layout.addWidget(self.btn_to_docx)

        self.btn_to_xlsx = QPushButton("📊 转 Excel (.xlsx)")
        self.btn_to_xlsx.clicked.connect(lambda: self._start_pdf_to_office('xlsx'))
        self.btn_to_xlsx.setEnabled(False)
        self.btn_to_xlsx.setMinimumHeight(32)
        office_btn_layout.addWidget(self.btn_to_xlsx)

        self.btn_to_pptx = QPushButton("📽 转 PPT (.pptx)")
        self.btn_to_pptx.clicked.connect(lambda: self._start_pdf_to_office('pptx'))
        self.btn_to_pptx.setEnabled(False)
        self.btn_to_pptx.setMinimumHeight(32)
        office_btn_layout.addWidget(self.btn_to_pptx)

        office_layout.addLayout(office_btn_layout)
        office_group.setLayout(office_layout)
        layout.addWidget(office_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        # 快捷键
        self.addAction(QAction("选择图片/PDF", self, shortcut="Ctrl+O", triggered=self._add_images))

        self.setLayout(layout)

    # ── 图片→PDF ──

    def _add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片 (*.jpg *.jpeg *.png *.webp *.bmp *.gif)"
        )
        for f in files:
            if f not in self.image_files:
                self.image_files.append(f)
                self.img_list.addItem(f"🖼 {Path(f).name}")
        self.btn_to_pdf.setEnabled(len(self.image_files) >= 1)

    def _on_images_dropped(self, files):
        """拖拽图片到图片→PDF"""
        for f in files:
            if f not in self.image_files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'):
                    self.image_files.append(f)
                    self.img_list.addItem(f"🖼 {Path(f).name}")
        self.btn_to_pdf.setEnabled(len(self.image_files) >= 1)

    def _clear_images(self):
        self.image_files.clear()
        self.img_list.clear()
        self.btn_to_pdf.setEnabled(False)

    def _select_pdf_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存 PDF", "", "PDF (*.pdf)"
        )
        if path:
            self.pdf_output.setText(path)

    def _select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF", "", "PDF (*.pdf)"
        )
        if path:
            self._set_pdf_path(path)

    def _on_pdf_dropped(self, files):
        """拖拽 PDF 到 PDF→图片 区"""
        if files:
            f = files[0]
            if f.lower().endswith('.pdf'):
                self._set_pdf_path(f)

    def _set_pdf_path(self, path):
        self.pdf_path.setText(path)
        self.btn_pdf_to_img.setEnabled(True)

    def _start_images_to_pdf(self):
        if len(self.image_files) < 1:
            QMessageBox.warning(self, "提示", "请至少选择一张图片")
            return

        out_path = self.pdf_output.text().strip()
        if not out_path:
            out_path = os.path.join(os.path.dirname(self.image_files[0]), "output.pdf")

        self.btn_to_pdf.setEnabled(False)
        self.btn_to_pdf.setText("⏳ 生成中...")
        self.progress_bar.setVisible(True)

        self.worker = ConvertWorker(
            'images_to_pdf',
            image_paths=self.image_files,
            output_path=out_path,
            progress_callback=None,
        )
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(lambda msg: self._on_pdf_done(msg, out_path))
        self.worker.error.connect(self._on_pdf_error)
        self.worker.start()

    def _on_pdf_done(self, msg, out_path):
        self.btn_to_pdf.setEnabled(True)
        self.btn_to_pdf.setText("📄 生成 PDF")
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "完成", msg)
        if os.path.isfile(out_path):
            out_path = os.path.dirname(out_path)
        if os.path.exists(out_path):
            os.startfile(out_path)

    def _on_pdf_error(self, msg):
        self.btn_to_pdf.setEnabled(True)
        self.btn_to_pdf.setText("📄 生成 PDF")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", msg)

    def _start_pdf_to_images(self):
        pdf_path = self.pdf_path.text().strip()
        if not pdf_path:
            return

        out_dir = os.path.join(os.path.dirname(pdf_path), Path(pdf_path).stem)
        img_fmt = self.pdf_img_format.currentText()
        dpi = self.dpi_spin.value()

        self.btn_pdf_to_img.setEnabled(False)
        self.btn_pdf_to_img.setText("⏳ 导出中...")
        self.progress_bar.setVisible(True)

        self.worker = ConvertWorker(
            'pdf_to_images',
            pdf_path=pdf_path,
            output_dir=out_dir,
            image_format=img_fmt,
            dpi=dpi,
            progress_callback=None,
        )
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(lambda msg: self._on_pdf_img_done(msg, out_dir))
        self.worker.error.connect(self._on_pdf_img_error)
        self.worker.start()

    def _on_pdf_img_done(self, msg, out_dir):
        self.btn_pdf_to_img.setEnabled(True)
        self.btn_pdf_to_img.setText("🖼 导出为图片")
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "完成", msg)
        if os.path.exists(out_dir):
            os.startfile(out_dir)

    def _on_pdf_img_error(self, msg):
        self.btn_pdf_to_img.setEnabled(True)
        self.btn_pdf_to_img.setText("🖼 导出为图片")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", msg)

    # ── PDF → Office ──

    def _select_office_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF", "", "PDF (*.pdf)"
        )
        if path:
            self._set_office_pdf(path)

    def _on_office_pdf_dropped(self, files):
        """拖拽 PDF 到 PDF→Office 区"""
        if files:
            f = files[0]
            if f.lower().endswith('.pdf'):
                self._set_office_pdf(f)

    def _set_office_pdf(self, path):
        self.office_pdf_path.setText(path)
        self.btn_to_docx.setEnabled(True)
        self.btn_to_xlsx.setEnabled(True)
        self.btn_to_pptx.setEnabled(True)

    def _start_pdf_to_office(self, target: str):
        pdf_path = self.office_pdf_path.text().strip()
        if not pdf_path:
            return

        stem = Path(pdf_path).stem
        default_dir = os.path.dirname(pdf_path)

        # 按目标格式弹保存对话框
        if target == 'docx':
            out_path, _ = QFileDialog.getSaveFileName(
                self, "保存 Word 文件", os.path.join(default_dir, f"{stem}.docx"),
                "Word (*.docx)"
            )
            if not out_path:
                return

            self.btn_to_docx.setEnabled(False)
            self.btn_to_docx.setText("⏳ 转换中...")

            self.worker = ConvertWorker(
                'pdf_to_docx',
                pdf_path=pdf_path,
                output_path=out_path,
                progress_callback=None,
            )

        elif target == 'xlsx':
            out_path, _ = QFileDialog.getSaveFileName(
                self, "保存 Excel 文件", os.path.join(default_dir, f"{stem}.xlsx"),
                "Excel (*.xlsx)"
            )
            if not out_path:
                return

            self.btn_to_xlsx.setEnabled(False)
            self.btn_to_xlsx.setText("⏳ 转换中...")

            self.worker = ConvertWorker(
                'pdf_to_excel',
                pdf_path=pdf_path,
                output_path=out_path,
                progress_callback=None,
            )

        elif target == 'pptx':
            out_path, _ = QFileDialog.getSaveFileName(
                self, "保存 PPT 文件", os.path.join(default_dir, f"{stem}.pptx"),
                "PPT (*.pptx)"
            )
            if not out_path:
                return

            self.btn_to_pptx.setEnabled(False)
            self.btn_to_pptx.setText("⏳ 转换中...")

            self.worker = ConvertWorker(
                'pdf_to_pptx',
                pdf_path=pdf_path,
                output_path=out_path,
                progress_callback=None,
            )
        else:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._last_office_output = out_path
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(lambda msg: self._on_office_done(msg, target))
        self.worker.error.connect(self._on_office_error)
        self.worker.start()

    def _on_office_done(self, msg, target):
        self._reset_office_buttons(target)
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "完成", msg)
        out_path = getattr(self, '_last_office_output', '')
        if out_path:
            out_dir = os.path.dirname(out_path)
            if os.path.exists(out_dir):
                os.startfile(out_dir)

    def _on_office_error(self, msg):
        self._reset_office_buttons()
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", msg)

    def _reset_office_buttons(self, target=None):
        texts = {'docx': '📝 转 Word (.docx)', 'xlsx': '📊 转 Excel (.xlsx)', 'pptx': '📽 转 PPT (.pptx)'}
        if target:
            btn = getattr(self, f'btn_to_{target}', None)
            if btn:
                btn.setEnabled(True)
                btn.setText(texts.get(target, ''))
        else:
            for t, text in texts.items():
                btn = getattr(self, f'btn_to_{t}', None)
                if btn:
                    btn.setEnabled(True)
                    btn.setText(text)

    def _update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)


# ── 主转换标签页 ─────────────────

class ConvertTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.addTab(ImageConvertWidget(), "🖼 图片转换")
        self.sub_tabs.addTab(AudioConvertWidget(), "🎵 音频转换")
        self.sub_tabs.addTab(VideoConvertWidget(), "🎬 视频转换")
        self.sub_tabs.addTab(PDFConvertWidget(), "📄 PDF 转换")

        layout.addWidget(self.sub_tabs)
        self.setLayout(layout)

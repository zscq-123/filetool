"""
共享 UI 组件
"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class DropArea(QFrame):
    """通用拖拽区域，支持自定义提示文字和文件类型过滤"""

    files_dropped = Signal(list)

    def __init__(
        self,
        hint: str = "📂 拖拽文件到这里",
        accept_paths: bool = True,
        min_height: int = 80,
        parent=None,
    ):
        super().__init__(parent)
        self._accept_paths = accept_paths
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(min_height)
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background: #f9f9f9;
            }
            DropArea:hover {
                border-color: #4a9eff;
                background: #f0f5ff;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.label = QLabel(hint)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self.label)
        self.setLayout(layout)

    def set_hint(self, text: str):
        self.label.setText(text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if self._accept_paths:
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            self.files_dropped.emit(files)

"""
主窗口 - 激活前显示引导页，激活后显示功能标签页
"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QStatusBar,
    QStackedWidget, QWidget, QVBoxLayout,
)
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction

from .extract_tab import ExtractTab
from .compress_tab import CompressTab
from .convert_tab import ConvertTab
from .activation_page import ActivationPage
from ..license.verify import LicenseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件工具箱")
        self.setMinimumSize(QSize(800, 600))
        self.resize(960, 680)

        self.license_mgr = LicenseManager()

        # 堆叠布局: 0 = 激活引导页, 1 = 功能页面
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 激活引导页
        self.activation_page = ActivationPage(self.license_mgr)
        self.activation_page.activated.connect(self._on_activated)
        self.stack.addWidget(self.activation_page)

        # 功能页面
        self._build_main_ui()

        self._setup_menu()

        # 判断显示哪个
        if self.license_mgr.is_activated():
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)

    def _build_main_ui(self):
        """构建主功能界面"""
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)

        self.tabs.addTab(ExtractTab(), "📦 文件解压")
        self.tabs.addTab(CompressTab(), "📁 文件压缩")
        self.tabs.addTab(ConvertTab(), "🔄 格式转换")

        layout.addWidget(self.tabs)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("✅ 已激活 · 所有功能可用")
        layout.addWidget(self.status_bar)

        self.stack.addWidget(self.main_widget)

    def _setup_menu(self):
        menubar = self.menuBar()

        about_action = QAction("关于文件工具箱", self)
        about_action.triggered.connect(self._show_about)
        menubar.addAction(about_action)

    def _on_activated(self):
        """激活成功后的回调"""
        self.stack.setCurrentIndex(1)

    def _show_about(self):
        QMessageBox.about(
            self,
            "关于文件工具箱",
            "📁 文件工具箱 v1.0.0\n\n"
            "一款简单易用的文件处理工具\n"
            "支持：文件解压/压缩 / 图片/音频/视频/PDF格式转换\n\n"
            "© 2025 FileTool"
        )

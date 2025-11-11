from enum import Enum
from pathlib import Path
from typing import Optional

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ThemeHelper:
    """集中管理浅/深/自动配色与样式表加载。"""

    def __init__(self, app: QApplication):
        self.app = app
        self.current_mode = ThemeMode.LIGHT

    def apply(self, mode: ThemeMode, stylesheet_path: Optional[Path] = None):
        """应用主题与样式"""
        if mode == ThemeMode.AUTO:
            # 简单实现：根据系统调色板的窗口背景亮度判断
            system_palette = self.app.palette()
            base_color = system_palette.color(QPalette.Window)
            lightness = base_color.lightness()
            mode = ThemeMode.DARK if lightness < 128 else ThemeMode.LIGHT

        self.current_mode = mode
        self._apply_palette(mode)

        if stylesheet_path:
            self._apply_stylesheet(stylesheet_path)

    def _apply_palette(self, mode: ThemeMode):
        palette = QPalette()
        if mode == ThemeMode.DARK:
            palette.setColor(QPalette.Window, QColor("#0B0F19"))
            palette.setColor(QPalette.WindowText, QColor("#E5E7EB"))
            palette.setColor(QPalette.Base, QColor("#161B26"))
            palette.setColor(QPalette.AlternateBase, QColor("#1F2937"))
            palette.setColor(QPalette.Text, QColor("#E5E7EB"))
            palette.setColor(QPalette.Button, QColor("#1E293B"))
            palette.setColor(QPalette.ButtonText, QColor("#F8FAFC"))
            palette.setColor(QPalette.Highlight, QColor("#3B82F6"))
            palette.setColor(QPalette.HighlightedText, QColor("#F8FAFC"))
            palette.setColor(QPalette.ToolTipBase, QColor("#1E293B"))
            palette.setColor(QPalette.ToolTipText, QColor("#F8FAFC"))
        else:
            palette.setColor(QPalette.Window, QColor("#F5F7FB"))
            palette.setColor(QPalette.WindowText, QColor("#1F2933"))
            palette.setColor(QPalette.Base, QColor("#FFFFFF"))
            palette.setColor(QPalette.AlternateBase, QColor("#F1F5F9"))
            palette.setColor(QPalette.Text, QColor("#1F2933"))
            palette.setColor(QPalette.Button, QColor("#FFFFFF"))
            palette.setColor(QPalette.ButtonText, QColor("#1F2933"))
            palette.setColor(QPalette.Highlight, QColor("#3B82F6"))
            palette.setColor(QPalette.HighlightedText, QColor("#F8FAFC"))
            palette.setColor(QPalette.ToolTipBase, QColor("#0F172A"))
            palette.setColor(QPalette.ToolTipText, QColor("#F8FAFC"))

        self.app.setPalette(palette)

    def _apply_stylesheet(self, stylesheet_path: Path):
        if not stylesheet_path.exists():
            raise FileNotFoundError(f"无法找到样式文件: {stylesheet_path}")
        qss = stylesheet_path.read_text(encoding="utf-8")
        base_dir = stylesheet_path.parent
        project_root = base_dir.parent
        qss = qss.replace('../resources/', f'{project_root.as_posix()}/resources/')
        self.app.setStyleSheet(qss)


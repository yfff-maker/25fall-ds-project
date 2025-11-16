from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
)
from PyQt5.QtCore import pyqtSignal, Qt


class OperationLogPanel(QFrame):
    """显示数据结构操作记录的面板"""

    clearRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("operationLogPanel")
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(
            """
            #operationLogPanel {
                background-color: #e8f2ff;
                border-left: 1px solid #c5d9f6;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        title = QLabel("操作记录")
        title.setStyleSheet("font-weight: bold; color: #1b4f72;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_clear = QPushButton("清空")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(
            "QPushButton {background:#ffffff;border:1px solid #bcd2f7;border-radius:4px;padding:4px 8px;}"
            "QPushButton:hover {background:#f5fbff;}"
        )
        btn_clear.clicked.connect(self.clearRequested.emit)
        header_layout.addWidget(btn_clear)
        layout.addLayout(header_layout)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet(
            "QListWidget {background: #fdfdff; border: 1px solid #d6e5fb;} QListWidget::item {padding:6px;}"
        )
        layout.addWidget(self.list_widget, 1)

    def append_record(self, text: str):
        if not text:
            return
        self.list_widget.addItem(text)
        self.list_widget.scrollToBottom()

    def set_records(self, records):
        self.list_widget.clear()
        for record in records or []:
            self.list_widget.addItem(record)
        if records:
            self.list_widget.scrollToBottom()

    def clear_records(self):
        self.list_widget.clear()


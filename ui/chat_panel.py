import os
from pathlib import Path
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QLabel,
    QFrame, QComboBox
)
from PyQt5.QtGui import QIcon


class ChatPanel(QWidget):
    """右侧常驻的 LLM 对话面板"""
    sendMessage = pyqtSignal(str)
    modelChanged = pyqtSignal(str)
    _DEFAULT_MODELS = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        # 初始触发一次当前模型，确保外部状态同步
        self.modelChanged.emit(self.current_model())

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 顶部：新对话 / 清空会话
        top_bar = QHBoxLayout()
        self.btn_new = QPushButton("新对话")
        self.btn_clear = QPushButton("清空会话")
        self.btn_new.setProperty("buttonType", "secondary")
        self.btn_clear.setProperty("buttonType", "secondary")
        self.btn_new.clicked.connect(self.clear_history)
        self.btn_clear.clicked.connect(self.clear_history)
        top_bar.addWidget(self.btn_new)
        top_bar.addWidget(self.btn_clear)
        top_bar.addStretch(1)
        layout.addLayout(top_bar)

        # 消息列表
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ChatPanelList")
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(self.list_widget.NoSelection)
        layout.addWidget(self.list_widget, 1)

        # 输入区
        input_bar = QHBoxLayout()
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入自然语言描述，回车发送（Ctrl+Enter换行）")
        self.input_edit.installEventFilter(self)
        self.input_edit.setAcceptRichText(False)
        self.input_edit.setObjectName("ChatPanelInput")
        self.btn_send = QPushButton("发送")
        self.btn_send.clicked.connect(self._on_send_clicked)
        self.btn_send.setObjectName("ChatPanelSend")
        icons_dir = Path(__file__).resolve().parents[1] / "resources" / "icons"
        send_icon = icons_dir / "send.svg"
        if send_icon.exists():
            self.btn_send.setIcon(QIcon(str(send_icon)))
            self.btn_send.setIconSize(QSize(18, 18))
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("ChatPanelModelCombo")
        self._init_model_combo()
        self.model_combo.currentTextChanged.connect(self.modelChanged.emit)
        input_bar.addWidget(self.input_edit, 1)
        input_bar.addWidget(self.model_combo)
        input_bar.addWidget(self.btn_send)
        layout.addLayout(input_bar)

        self.setLayout(layout)

    def eventFilter(self, obj, event):
        # Enter 发送，Ctrl+Enter 换行
        if obj is self.input_edit and event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ControlModifier:
                    # 插入换行
                    cursor = self.input_edit.textCursor()
                    cursor.insertText("\n")
                    return True
                else:
                    self._on_send_clicked()
                    return True
        return super().eventFilter(obj, event)

    def _on_send_clicked(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        self.sendMessage.emit(text)
        self.input_edit.clear()

    def append_user(self, text: str):
        self._add_message(text, role="user")

    def append_assistant(self, text: str):
        self._add_message(text, role="assistant")

    def clear_history(self):
        self.list_widget.clear()

    def current_model(self) -> str:
        """获取当前选择的模型名称"""
        if hasattr(self, "model_combo"):
            return self.model_combo.currentText().strip()
        return ""

    def set_model(self, model_name: str):
        """外部设置模型，保持下拉框同步"""
        if not model_name:
            return
        if self.model_combo.findText(model_name) == -1:
            self.model_combo.addItem(model_name)
        self.model_combo.setCurrentText(model_name)

    def _add_message(self, text: str, role: str):
        item = QListWidgetItem()
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 4, 0, 4)

        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble_layout.addWidget(label)

        if role == "user":
            bubble.setObjectName("ChatBubbleUser")
            container_layout.addWidget(bubble, alignment=Qt.AlignRight)
        else:
            bubble.setObjectName("ChatBubbleAssistant")
            container_layout.addWidget(bubble, alignment=Qt.AlignLeft)

        item.setSizeHint(container.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, container)
        self.list_widget.scrollToBottom()

    def _init_model_combo(self):
        """初始化模型选项"""
        default_model = "openai/gpt-3.5-turbo"  # 默认固定为 gpt-3.5
        env_model = os.getenv("OPENROUTER_MODEL")
        models = list(dict.fromkeys([default_model, env_model] + self._DEFAULT_MODELS)) if env_model else self._DEFAULT_MODELS
        self.model_combo.addItems(models)
        self.model_combo.setCurrentText(default_model)


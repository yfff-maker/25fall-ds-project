# -*- coding: utf-8 -*-
from pathlib import Path
from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon

class ControlPanel(QDockWidget):
    playClicked = pyqtSignal()
    pauseClicked = pyqtSignal()
    stepClicked = pyqtSignal()
    # 倍速变更：0.5/1.0/1.5/2.0
    speedChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__("算法控制", parent)
        w = QWidget()
        lay = QHBoxLayout(w)
        self.btn_play = QPushButton("播放")
        self.btn_pause = QPushButton("暂停")
        self.slider = QSlider(Qt.Horizontal)
        # 四档倍速：0=0.5x,1=1x,2=1.5x,3=2x
        self.slider.setRange(0, 3)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(1)
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setValue(1)  # 默认 1.0x
        self.speed_label = QLabel("1.0x")
        self.speed_label.setFixedWidth(48)
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.btn_pause.setProperty("buttonType", "secondary")
        self.slider.setObjectName("ControlSpeedSlider")

        icons_dir = Path(__file__).resolve().parents[1] / "resources" / "icons"
        icon_size = QSize(18, 18)
        self.btn_play.setIcon(QIcon(str(icons_dir / "play.svg")))
        self.btn_play.setIconSize(icon_size)
        self.btn_pause.setIcon(QIcon(str(icons_dir / "pause.svg")))
        self.btn_pause.setIconSize(icon_size)

        lay.addWidget(self.btn_play)
        lay.addWidget(self.btn_pause)
        lay.addWidget(self.slider, 1)
        lay.addWidget(self.speed_label)
        self.setWidget(w)

        self.btn_play.clicked.connect(self.playClicked.emit)
        self.btn_pause.clicked.connect(self.pauseClicked.emit)
        self.slider.valueChanged.connect(self._on_speed_changed)

    def _on_speed_changed(self, idx: int):
        multiplier = self._index_to_multiplier(idx)
        self.speed_label.setText(f"{multiplier}x")
        self.speedChanged.emit(multiplier)

    @staticmethod
    def _index_to_multiplier(idx: int) -> float:
        mapping = [0.5, 1.0, 1.5, 2.0]
        if 0 <= idx < len(mapping):
            return mapping[idx]
        return 1.0

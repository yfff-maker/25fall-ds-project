# -*- coding: utf-8 -*-
from pathlib import Path
from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QPushButton, QSlider
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon

class ControlPanel(QDockWidget):
    playClicked = pyqtSignal()
    pauseClicked = pyqtSignal()
    stepClicked = pyqtSignal()
    speedChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("算法控制", parent)
        w = QWidget()
        lay = QHBoxLayout(w)
        self.btn_play = QPushButton("播放")
        self.btn_pause = QPushButton("暂停")
        self.btn_step = QPushButton("下一步")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(50)
        self.btn_pause.setProperty("buttonType", "secondary")
        self.btn_step.setProperty("buttonType", "secondary")
        self.slider.setObjectName("ControlSpeedSlider")

        icons_dir = Path(__file__).resolve().parents[1] / "resources" / "icons"
        icon_size = QSize(18, 18)
        self.btn_play.setIcon(QIcon(str(icons_dir / "play.svg")))
        self.btn_play.setIconSize(icon_size)
        self.btn_pause.setIcon(QIcon(str(icons_dir / "pause.svg")))
        self.btn_pause.setIconSize(icon_size)
        self.btn_step.setIcon(QIcon(str(icons_dir / "step.svg")))
        self.btn_step.setIconSize(icon_size)

        lay.addWidget(self.btn_play)
        lay.addWidget(self.btn_pause)
        lay.addWidget(self.btn_step)
        lay.addWidget(self.slider, 1)
        self.setWidget(w)

        self.btn_play.clicked.connect(self.playClicked.emit)
        self.btn_pause.clicked.connect(self.pauseClicked.emit)
        self.btn_step.clicked.connect(self.stepClicked.emit)
        self.slider.valueChanged.connect(self.speedChanged.emit)

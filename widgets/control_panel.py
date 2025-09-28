# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QPushButton, QSlider
from PyQt5.QtCore import Qt, pyqtSignal

class ControlPanel(QDockWidget):
    playClicked = pyqtSignal()
    pauseClicked = pyqtSignal()
    stepClicked = pyqtSignal()
    speedChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("算法控制", parent)
        w = QWidget()
        lay = QHBoxLayout(w)
        self.btn_play = QPushButton("▶ 播放")
        self.btn_pause = QPushButton("⏸ 暂停")
        self.btn_step = QPushButton("➤ 下一步")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(50)
        lay.addWidget(self.btn_play)
        lay.addWidget(self.btn_pause)
        lay.addWidget(self.btn_step)
        lay.addWidget(self.slider, 1)
        self.setWidget(w)

        self.btn_play.clicked.connect(self.playClicked.emit)
        self.btn_pause.clicked.connect(self.pauseClicked.emit)
        self.btn_step.clicked.connect(self.stepClicked.emit)
        self.slider.valueChanged.connect(self.speedChanged.emit)

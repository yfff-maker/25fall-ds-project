# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsRectItem
from PyQt5.QtGui import QBrush, QPen, QColor, QFont, QPainter
from PyQt5.QtCore import Qt, QPointF, QTimer, QObject

NODE_RADIUS = 22
BOX_NODE_WIDTH = 60
BOX_NODE_HEIGHT = 40
DEFAULT_NODE_COLOR = QColor("#4C78A8")
DEFAULT_TEXT_COLOR = Qt.white

class Animator(QObject):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.queue = []
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.playing = False
        self.interval_ms = 500

    def add_step(self, func):
        self.queue.append(func)

    def clear(self):
        self.queue.clear()

    def set_speed(self, speed: int):
        speed = max(1, min(100, speed))
        self.interval_ms = int(1050 - speed * 10)
        if self.playing and self.timer.isActive():
            self.timer.setInterval(self.interval_ms)

    def play(self):
        if not self.queue:
            return
        self.playing = True
        if not self.timer.isActive():
            self.timer.start(self.interval_ms)

    def pause(self):
        self.playing = False
        self.timer.stop()

    def step(self):
        if self.queue:
            func = self.queue.pop(0)
            func()

    def _tick(self):
        if not self.playing or not self.queue:
            self.pause()
            return
        self.step()

class Canvas(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setRenderHint(QPainter.TextAntialiasing, True)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.view.setStyleSheet(
            """
            QGraphicsView {
                background: #f7f9fc;
                border: 0px;
            }
            """
        )
        base_font = QFont("Segoe UI", 11)
        base_font.setWeight(QFont.Medium)
        self.view.setFont(base_font)

        self.hint_label = QGraphicsTextItem("")
        hint_font = QFont(base_font)
        hint_font.setPointSize(12)
        hint_font.setWeight(QFont.DemiBold)
        self.hint_label.setFont(hint_font)
        self.hint_label.setDefaultTextColor(QColor("#4B5563"))
        self.hint_label.setPos(14, 14)
        self.scene.addItem(self.hint_label)
        
        # 比较信息标签（右下角）
        self.comparison_label = QGraphicsTextItem("")
        self.comparison_label.setDefaultTextColor(QColor("#2563EB"))
        font = QFont(base_font)
        font.setPointSize(13)
        font.setWeight(QFont.DemiBold)
        self.comparison_label.setFont(font)
        self.scene.addItem(self.comparison_label)
        
        # 步骤说明标签（右下角）
        self.step_details_label = QGraphicsTextItem("")
        self.step_details_label.setDefaultTextColor(QColor("#0F766E"))
        font = QFont(base_font)
        font.setPointSize(11)
        self.step_details_label.setFont(font)
        self.scene.addItem(self.step_details_label)
        
        # 操作历史记录标签（左侧）
        self.operation_history_label = QGraphicsTextItem("")
        self.operation_history_label.setDefaultTextColor(QColor("#1D4ED8"))
        font = QFont(base_font)
        font.setPointSize(10)
        self.operation_history_label.setFont(font)
        self.scene.addItem(self.operation_history_label)

        self.animator = Animator(self.scene)
        
        # 存储当前快照
        self.current_snapshot = None

    # animator proxies
    def animator_play(self): self.animator.play()
    def animator_pause(self): self.animator.pause()
    def animator_step(self): self.animator.step()
    def animator_speed(self, v: int): self.animator.set_speed(v)

    def set_hint(self, text: str):
        self.hint_label.setPlainText(text)
    
    def set_comparison_info(self, text: str):
        """设置比较信息（右下角显示）"""
        self.comparison_label.setPlainText(text)
        # 计算右下角位置
        if text:
            rect = self.comparison_label.boundingRect()
            x = self.view.width() - rect.width() - 20
            y = self.view.height() - rect.height() - 20
            self.comparison_label.setPos(x, y)
        else:
            self.comparison_label.setPos(0, 0)
    
    def set_step_details(self, details: list):
        """设置步骤说明（右下角显示）"""
        if details:
            # 将步骤说明列表转换为多行文本
            text = "\n".join(details)
            self.step_details_label.setPlainText(text)
            # 计算右下角位置
            rect = self.step_details_label.boundingRect()
            x = self.view.width() - rect.width() - 20
            y = self.view.height() - rect.height() - 20
            self.step_details_label.setPos(x, y)
        else:
            self.step_details_label.setPlainText("")
            self.step_details_label.setPos(0, 0)
    
    def set_operation_history(self, history: list):
        """设置操作历史记录（左侧显示）"""
        if history:
            # 将操作历史列表转换为多行文本
            text = "\n".join(history)
            self.operation_history_label.setPlainText(text)
            # 设置左侧位置
            self.operation_history_label.setPos(10, 60)  # 在提示文本下方
        else:
            self.operation_history_label.setPlainText("")
            self.operation_history_label.setPos(0, 0)

    def render_snapshot(self, snapshot):
        """根据快照渲染数据结构"""
        if not snapshot:
            return
        
        # 清除现有内容
        self.clear_scene()
        
        # 更新提示文本
        if snapshot.hint_text:
            self.set_hint(snapshot.hint_text)
        
        # 更新比较信息
        if hasattr(snapshot, 'comparison_text') and snapshot.comparison_text:
            self.set_comparison_info(snapshot.comparison_text)
        else:
            self.set_comparison_info("")
        
        # 更新步骤说明
        if hasattr(snapshot, 'step_details') and snapshot.step_details:
            self.set_step_details(snapshot.step_details)
        else:
            self.set_step_details([])
        
        # 更新操作历史记录
        if hasattr(snapshot, 'operation_history') and snapshot.operation_history:
            self.set_operation_history(snapshot.operation_history)
        else:
            self.set_operation_history([])
        
        # 渲染方框（用于数组等）
        for box in snapshot.boxes:
            self._render_box(box)
        
        # 渲染节点
        for node in snapshot.nodes:
            self._render_node(node)
        
        # 渲染边
        for edge in snapshot.edges:
            self._render_edge(edge)
        
        # 存储当前快照
        self.current_snapshot = snapshot

    def _render_box(self, box):
        """渲染方框"""
        # 创建方框
        rect = QGraphicsRectItem(0, 0, box.width, box.height)
        rect.setBrush(QBrush(QColor(box.color)))
        rect.setPen(QPen(Qt.black, 1))
        rect.setPos(box.x, box.y)
        
        # 创建文本标签
        label = QGraphicsTextItem(box.value)
        # 使用text_color参数，如果没有则使用默认颜色
        text_color = getattr(box, 'text_color', '#000000')
        label.setDefaultTextColor(QColor(text_color))
        # 下标（index_）字号更小：约为原来的 1/2；其它保持不变
        font = QFont("Segoe UI", 11)
        if getattr(box, "id", "").startswith("index_"):
            font.setPointSize(6)
        font.setWeight(QFont.Medium)
        label.setFont(font)
        # 居中显示文本
        label_width = label.boundingRect().width()
        label_height = label.boundingRect().height()
        label.setPos(box.x + (box.width - label_width)/2, 
                    box.y + (box.height - label_height)/2)
        
        # 添加到场景
        self.scene.addItem(rect)
        self.scene.addItem(label)

    def _render_node(self, node):
        """渲染节点"""
        if node.node_type == "box":
            self._render_box_node(node)
        else:
            self._render_circle_node(node)

    def _render_circle_node(self, node):
        """渲染圆形节点"""
        diameter = node.width or NODE_RADIUS * 2
        radius = diameter / 2
        circle = QGraphicsEllipseItem(0, 0, diameter, diameter)
        circle.setBrush(QBrush(QColor(node.color)))
        border_color = getattr(node, 'border_color', None)
        border_width = getattr(node, 'border_width', 0)
        if border_color:
            circle.setPen(QPen(QColor(border_color), border_width or 2))
        else:
            pen = QPen(Qt.transparent, 0)
            circle.setPen(pen)
        circle.setPos(node.x - radius, node.y - radius)
        
        label = QGraphicsTextItem(node.value)
        font = QFont("Segoe UI", 12)
        font.setWeight(QFont.DemiBold)
        label.setFont(font)
        value_color = getattr(node, 'text_color', '#FFFFFF')
        label.setDefaultTextColor(QColor(value_color))
        label_width = label.boundingRect().width()
        label_height = label.boundingRect().height()
        label.setPos(node.x - label_width/2, node.y - label_height/2)
        
        self.scene.addItem(circle)
        self.scene.addItem(label)
        
        sub_label = getattr(node, 'sub_label', None)
        if sub_label:
            sub_item = QGraphicsTextItem(sub_label)
            sub_font = QFont("Segoe UI", 10)
            sub_font.setWeight(QFont.Medium)
            sub_item.setFont(sub_font)
            sub_color = getattr(node, 'sub_label_color', '#1f4e79')
            sub_item.setDefaultTextColor(QColor(sub_color))
            sub_width = sub_item.boundingRect().width()
            sub_item.setPos(node.x - sub_width/2, node.y + radius - 2)
            self.scene.addItem(sub_item)

    def _render_box_node(self, node):
        """渲染方框节点（用于二叉树）"""
        # 主方框
        main_box = QGraphicsRectItem(0, 0, node.width or BOX_NODE_WIDTH, node.height or BOX_NODE_HEIGHT)
        main_box.setBrush(QBrush(QColor(node.color)))
        
        # 支持边框颜色（用于失衡节点高亮）
        border_color = getattr(node, 'border_color', None)
        border_width = getattr(node, 'border_width', 2)
        if border_color:
            main_box.setPen(QPen(QColor(border_color), border_width))
        else:
            main_box.setPen(QPen(Qt.black, border_width))
        
        main_box.setPos(node.x - (node.width or BOX_NODE_WIDTH)/2, node.y - (node.height or BOX_NODE_HEIGHT)/2)
        
        # 左连接点
        left_box = QGraphicsRectItem(0, 0, 20, 20)
        left_box.setBrush(QBrush(QColor("#FF6B6B")))
        left_box.setPen(QPen(Qt.black, 1))
        left_box.setPos(node.x - (node.width or BOX_NODE_WIDTH)/2 - 10, node.y - 10)
        
        # 右连接点
        right_box = QGraphicsRectItem(0, 0, 20, 20)
        right_box.setBrush(QBrush(QColor("#4ECDC4")))
        right_box.setPen(QPen(Qt.black, 1))
        right_box.setPos(node.x + (node.width or BOX_NODE_WIDTH)/2 - 10, node.y - 10)
        
        # 文本标签
        label = QGraphicsTextItem(node.value)
        font = QFont("Segoe UI", 12)
        font.setWeight(QFont.DemiBold)
        label.setFont(font)
        label.setDefaultTextColor(DEFAULT_TEXT_COLOR)
        label_width = label.boundingRect().width()
        label_height = label.boundingRect().height()
        label.setPos(node.x - label_width/2, node.y - label_height/2)
        
        # 添加到场景
        self.scene.addItem(main_box)
        self.scene.addItem(left_box)
        self.scene.addItem(right_box)
        self.scene.addItem(label)

    def _render_edge(self, edge):
        """渲染边"""
        # 这里需要根据节点ID找到实际的坐标
        # 简化实现，假设边包含坐标信息
        if hasattr(edge, 'from_x') and hasattr(edge, 'from_y') and hasattr(edge, 'to_x') and hasattr(edge, 'to_y'):
            line = QGraphicsLineItem(edge.from_x, edge.from_y, edge.to_x, edge.to_y)
            line.setPen(QPen(QColor(edge.color), 2))
            self.scene.addItem(line)

    def clear_scene(self):
        """清除场景中的所有项目（除了提示标签、比较信息标签、步骤说明标签和操作历史标签）"""
        items = self.scene.items()
        for item in items:
            if item != self.hint_label and item != self.comparison_label and item != self.step_details_label and item != self.operation_history_label:
                self.scene.removeItem(item)

    # 保留原有的工具方法，用于向后兼容
    def add_node(self, text: str, pos: QPointF, color=DEFAULT_NODE_COLOR):
        circle = QGraphicsEllipseItem(0, 0, NODE_RADIUS*2, NODE_RADIUS*2)
        circle.setBrush(QBrush(color))
        circle.setPen(QPen(Qt.black, 1))
        circle.setPos(pos - QPointF(NODE_RADIUS, NODE_RADIUS))
        label = QGraphicsTextItem(text)
        font = QFont(); font.setPointSize(10)
        label.setFont(font)
        label.setDefaultTextColor(DEFAULT_TEXT_COLOR)
        label.setPos(circle.pos().x()+8, circle.pos().y()+4)
        self.scene.addItem(circle)
        self.scene.addItem(label)
        return circle, label

    def add_box_node(self, text: str, pos: QPointF, color=DEFAULT_NODE_COLOR):
        """添加方框节点，用于二叉树显示"""
        # 主方框
        main_box = QGraphicsRectItem(0, 0, BOX_NODE_WIDTH, BOX_NODE_HEIGHT)
        main_box.setBrush(QBrush(color))
        main_box.setPen(QPen(Qt.black, 2))
        main_box.setPos(pos - QPointF(BOX_NODE_WIDTH/2, BOX_NODE_HEIGHT/2))
        
        # 左连接点
        left_box = QGraphicsRectItem(0, 0, 20, 20)
        left_box.setBrush(QBrush(QColor("#FF6B6B")))
        left_box.setPen(QPen(Qt.black, 1))
        left_box.setPos(pos.x() - BOX_NODE_WIDTH/2 - 10, pos.y() - 10)
        
        # 右连接点
        right_box = QGraphicsRectItem(0, 0, 20, 20)
        right_box.setBrush(QBrush(QColor("#4ECDC4")))
        right_box.setPen(QPen(Qt.black, 1))
        right_box.setPos(pos.x() + BOX_NODE_WIDTH/2 - 10, pos.y() - 10)
        
        # 文本标签
        label = QGraphicsTextItem(text)
        font = QFont(); font.setPointSize(12)
        label.setFont(font)
        label.setDefaultTextColor(DEFAULT_TEXT_COLOR)
        label_width = label.boundingRect().width()
        label_height = label.boundingRect().height()
        label.setPos(pos.x() - label_width/2, pos.y() - label_height/2)
        
        # 添加到场景
        self.scene.addItem(main_box)
        self.scene.addItem(left_box)
        self.scene.addItem(right_box)
        self.scene.addItem(label)
        
        return main_box, left_box, right_box, label

    def remove_items(self, items):
        for it in items:
            self.scene.removeItem(it)

    def add_arrow(self, p1: QPointF, p2: QPointF, color=Qt.black):
        line = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y())
        line.setPen(QPen(QColor(color), 2))
        self.scene.addItem(line)
        return line

    # color helpers
    def set_item_color_now(self, item, color=DEFAULT_NODE_COLOR):
        if hasattr(item, "setBrush"):
            item.setBrush(QBrush(QColor(color)))
        elif hasattr(item, "setDefaultTextColor"):
            item.setDefaultTextColor(QColor(color))

    def queue_set_item_color(self, item, color):
        def f(): self.set_item_color_now(item, color)
        self.animator.add_step(f)

    def highlight_item_step(self, item, color=QColor("#F58518")):
        self.queue_set_item_color(item, color)
# -*- coding: utf-8 -*-
"""
数据适配器：将数据结构状态转换为可视化快照
"""
import copy
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# 简单的Node类用于适配器
class Node:
    def __init__(self, freq, char=None, left=None, right=None):
        try:
            self.freq = int(freq) if freq is not None else 0  # 确保freq是整数
        except (ValueError, TypeError):
            print(f"警告: 无法转换频率值 '{freq}' 为整数，使用默认值 0")
            self.freq = 0
        self.char = char
        self.left = left
        self.right = right

@dataclass
class NodeSnapshot:
    """节点快照"""
    id: str
    value: str
    x: float
    y: float
    color: str = "#4C78A8"
    node_type: str = "circle"  # "circle" 或 "box"
    width: Optional[float] = None
    height: Optional[float] = None
    text_color: str = "#FFFFFF"
    border_color: Optional[str] = None
    border_width: int = 2
    sub_label: Optional[str] = None
    sub_label_color: str = "#1f4e79"

@dataclass
class EdgeSnapshot:
    """边快照"""
    from_id: str
    to_id: str
    color: str = "#000000"
    arrow_type: str = "line"  # "line" 或 "arrow"

@dataclass
class BoxSnapshot:
    """方框快照（用于数组等）"""
    id: str
    value: str
    x: float
    y: float
    width: float
    height: float
    color: str = "#4C78A8"
    text_color: str = "#000000"  # 文字颜色，默认为黑色

@dataclass
class StructureSnapshot:
    """数据结构快照"""
    nodes: List[NodeSnapshot] = None
    edges: List[EdgeSnapshot] = None
    boxes: List[BoxSnapshot] = None
    hint_text: str = ""
    step_details: List[str] = None  # 添加详细步骤说明
    operation_history: List[str] = None  # 添加操作历史记录
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
        if self.edges is None:
            self.edges = []
        if self.boxes is None:
            self.boxes = []
        if self.step_details is None:
            self.step_details = []
        if self.operation_history is None:
            self.operation_history = []


def center_snapshot(snapshot: StructureSnapshot,
                    canvas_width: float = 1280,
                    canvas_height: float = 720,
                    margin: float = 40) -> StructureSnapshot:
    """
    调整快照内所有元素的位置，使其在指定画布范围内居中显示。
    仅修改传入的 snapshot 并返回引用，方便链式调用。
    """
    if snapshot is None:
        return snapshot

    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    def _include_rect(x0: float, y0: float, w: float, h: float):
        nonlocal min_x, min_y, max_x, max_y
        min_x = min(min_x, x0)
        min_y = min(min_y, y0)
        max_x = max(max_x, x0 + w)
        max_y = max(max_y, y0 + h)

    def _include_point(x: Optional[float], y: Optional[float]):
        if x is None or y is None:
            return
        _include_rect(x, y, 0, 0)

    # 记录节点和方框的范围
    for node in snapshot.nodes:
        width = node.width if node.width is not None else (60 if node.node_type == "box" else 40)
        height = node.height if node.height is not None else (40 if node.node_type == "box" else 40)
        if node.node_type == "circle":
            _include_rect(node.x - width / 2, node.y - height / 2, width, height)
        else:
            _include_rect(node.x, node.y, width, height)

    for box in snapshot.boxes:
        _include_rect(box.x, box.y, box.width, box.height)

    # 边只包含线段坐标，按端点纳入边界
    for edge in snapshot.edges:
        _include_point(getattr(edge, "from_x", None), getattr(edge, "from_y", None))
        _include_point(getattr(edge, "to_x", None), getattr(edge, "to_y", None))

    if min_x == float('inf') or min_y == float('inf'):
        # 没有任何可视元素，直接返回
        return snapshot

    content_width = max_x - min_x
    content_height = max_y - min_y
    if content_width == 0 and content_height == 0:
        return snapshot

    canvas_center_x = canvas_width / 2.0
    canvas_center_y = canvas_height / 2.0
    content_center_x = min_x + content_width / 2.0
    content_center_y = min_y + content_height / 2.0

    offset_x = canvas_center_x - content_center_x
    offset_y = canvas_center_y - content_center_y

    # 保证内容不会越过边缘（在可行的情况下保留 margin）
    def _clamp_offset(offset, min_coord, max_coord, limit_min, limit_max):
        after_min = min_coord + offset
        after_max = max_coord + offset
        if after_min < limit_min:
            offset += limit_min - after_min
            after_max = max_coord + offset
        if after_max > limit_max:
            offset -= after_max - limit_max
        return offset

    offset_x = _clamp_offset(offset_x, min_x, max_x, margin, canvas_width - margin)
    offset_y = _clamp_offset(offset_y, min_y, max_y, margin, canvas_height - margin)

    for node in snapshot.nodes:
        node.x += offset_x
        node.y += offset_y

    for box in snapshot.boxes:
        box.x += offset_x
        box.y += offset_y

    for edge in snapshot.edges:
        if hasattr(edge, "from_x") and edge.from_x is not None:
            edge.from_x += offset_x
        if hasattr(edge, "to_x") and edge.to_x is not None:
            edge.to_x += offset_x
        if hasattr(edge, "from_y") and edge.from_y is not None:
            edge.from_y += offset_y
        if hasattr(edge, "to_y") and edge.to_y is not None:
            edge.to_y += offset_y

    return snapshot

class SequentialListAdapter:
    """顺序表适配器"""
    
    @staticmethod
    def to_snapshot(sequential_list, start_x=100, y=200, box_width=60, box_height=40) -> StructureSnapshot:
        """将顺序表转换为快照"""
        snapshot = StructureSnapshot() # ← 创建：创建 StructureSnapshot 实例
        list_size = sequential_list.length()
        snapshot.hint_text = f"顺序表 (长度: {list_size}, 容量: {sequential_list.get_capacity()})"
        
        # 动态数量绘制：根据实际元素数量绘制
        array_start_x = start_x
        array_start_y = y + 100  # 数组在标题下方
        
        # 获取顺序表内容
        list_data = list(sequential_list.to_list())  # 转换为列表用于索引
        
        # 检查是否在动画中
        animation_state = getattr(sequential_list, '_animation_state', None)
        insert_position = getattr(sequential_list, '_insert_position', 0) if animation_state == 'inserting' else -1
        delete_position = getattr(sequential_list, '_delete_position', 0) if animation_state == 'deleting' else -1
        
        # 自动换行布局参数
        canvas_width = 1200  # 画布宽度
        elements_per_row = max(1, canvas_width // box_width)  # 每行最多元素数量
        
        # 动态绘制元素（只绘制实际存在的元素）
        for i in range(list_size):
            # 计算元素位置（自动换行）
            row = i // elements_per_row
            col = i % elements_per_row
            
            element_x = array_start_x + col * box_width
            element_y = array_start_y + row * (box_height + 30)  # 行间距30像素
            
            # 确定方框的值和颜色
            value = str(list_data[i])  # 顺序表按索引顺序显示
            
            # 如果在插入动画中，且该位置需要后移，则隐藏原位置
            if animation_state == 'inserting' and i >= insert_position:
                # 隐藏需要后移的元素（在原位置显示为空白）
                value = ""
                color = "#E0E0E0"  # 浅灰色
            # 如果在删除动画中，且该位置需要前移，则隐藏原位置
            elif animation_state == 'deleting' and i > delete_position:
                # 隐藏需要前移的元素（在原位置显示为空白）
                value = ""
                color = "#E0E0E0"  # 浅灰色
            else:
                color = "#4C78A8"  # 蓝色
            
            box = BoxSnapshot(
                id=f"array_box_{i}",
                value=value,
                x=element_x,
                y=element_y,
                width=box_width,
                height=box_height,
                color=color
            )
            snapshot.boxes.append(box)
        
        # 添加位置索引标签（只显示实际元素的索引）
        for i in range(list_size):
            row = i // elements_per_row
            col = i % elements_per_row
            
            element_x = array_start_x + col * box_width
            element_y = array_start_y + row * (box_height + 30)
            
            index_label = BoxSnapshot(
                id=f"index_{i}",
                value=str(i),
                x=element_x,
                y=element_y + box_height + 5,
                width=box_width,
                height=20,
                color="#F0F0F0"
            )
            snapshot.boxes.append(index_label)
        
        # 添加当前长度指示器
        if list_size > 0:
            # 计算最后一个元素的位置（适应换行布局）
            last_element_index = list_size - 1
            last_row = last_element_index // elements_per_row
            last_col = last_element_index % elements_per_row
            
            last_element_x = array_start_x + last_col * box_width
            last_element_y = array_start_y + last_row * (box_height + 30)
            
            # 高亮当前最后一个元素位置
            length_box = BoxSnapshot(
                id="length_indicator",
                value="LEN",
                x=last_element_x,
                y=last_element_y + box_height + 5,
                width=box_width,
                height=25,
                color="#FF6B6B"  # 红色
            )
            snapshot.boxes.append(length_box)
        
        # 如果正在插入动画，显示新节点平滑移动到目标位置和元素后移效果
        animation_state = getattr(sequential_list, '_animation_state', None)
        if animation_state == 'inserting':
            new_value = getattr(sequential_list, '_new_value', None)
            animation_progress = getattr(sequential_list, '_animation_progress', 0.0)
            insert_position = getattr(sequential_list, '_insert_position', 0)
            if new_value is not None:
                # 计算目标位置（插入位置）- 适应换行布局
                target_row = insert_position // elements_per_row
                target_col = insert_position % elements_per_row
                target_x = array_start_x + target_col * box_width
                target_y = array_start_y + target_row * (box_height + 30)
                
                # 设置目标位置到顺序表对象
                sequential_list.set_animation_target(target_x, target_y)
                
                # 计算起始位置（屏幕正上方）
                start_x = target_x
                start_y = 50  # 屏幕正上方
                
                # 使用线性插值计算当前位置
                current_x = start_x + (target_x - start_x) * animation_progress
                current_y = start_y + (target_y - start_y) * animation_progress
                
                # 显示新节点
                new_node = BoxSnapshot(
                    id="new_node",
                    value=str(new_value),
                    x=current_x,
                    y=current_y,
                    width=box_width,
                    height=box_height,
                    color="#FF6B6B"  # 红色表示正在移动的节点
                )
                snapshot.boxes.append(new_node)
                
                # 显示需要后移的元素（插入位置及之后的元素）
                for i in range(insert_position, list_size):
                    if i < len(list_data):
                        # 计算后移后的位置（适应换行布局）
                        original_row = i // elements_per_row
                        original_col = i % elements_per_row
                        original_x = array_start_x + original_col * box_width
                        original_y = array_start_y + original_row * (box_height + 30)
                        
                        # 计算后移后的位置
                        next_row = (i + 1) // elements_per_row
                        next_col = (i + 1) % elements_per_row
                        next_x = array_start_x + next_col * box_width
                        next_y = array_start_y + next_row * (box_height + 30)
                        
                        # 使用线性插值计算当前位置
                        shifted_x = original_x + (next_x - original_x) * animation_progress
                        shifted_y = original_y + (next_y - original_y) * animation_progress
                        
                        # 创建后移的元素
                        shifted_box = BoxSnapshot(
                            id=f"shifted_box_{i}",
                            value=str(list_data[i]),
                            x=shifted_x,
                            y=shifted_y,
                            width=box_width,
                            height=box_height,
                            color="#FFA500"  # 橙色表示正在后移的元素
                        )
                        snapshot.boxes.append(shifted_box)
                        
                        # 添加移动箭头（只在动画进行中显示）
                        if animation_progress < 0.8:  # 动画快结束时隐藏箭头
                            arrow_x = original_x + box_width // 2
                            arrow_y = original_y + box_height + 10
                            arrow_box = BoxSnapshot(
                                id=f"arrow_{i}",
                                value="→",
                                x=arrow_x,
                                y=arrow_y,
                                width=20,
                                height=20,
                                color="#FFA500"
                            )
                            snapshot.boxes.append(arrow_box)
                
                # 添加插入位置指示器
                insert_indicator = BoxSnapshot(
                    id="insert_indicator",
                    value="INSERT",
                    x=target_x,
                    y=target_y - 60,
                    width=box_width,
                    height=25,
                    color="#00FF00"  # 绿色表示插入位置
                )
                snapshot.boxes.append(insert_indicator)
        
        # 如果正在删除动画，显示元素向前移动效果
        elif animation_state == 'deleting':
            delete_position = getattr(sequential_list, '_delete_position', 0)
            deleted_value = getattr(sequential_list, '_deleted_value', None)
            animation_progress = getattr(sequential_list, '_animation_progress', 0.0)
            
            if deleted_value is not None:
                # 计算删除位置（适应换行布局）
                delete_row = delete_position // elements_per_row
                delete_col = delete_position % elements_per_row
                delete_x = array_start_x + delete_col * box_width
                delete_y = array_start_y + delete_row * (box_height + 30)
                
                # 显示被删除的元素（逐渐消失）
                # 根据动画进度调整透明度效果（通过颜色变化模拟）
                if animation_progress < 0.7:  # 动画前70%显示被删除元素
                    delete_box = BoxSnapshot(
                        id="deleted_element",
                        value=str(deleted_value),
                        x=delete_x,
                        y=delete_y,
                        width=box_width,
                        height=box_height,
                        color="#FF0000"  # 红色表示被删除的元素
                    )
                    snapshot.boxes.append(delete_box)
                
                # 显示需要前移的元素（删除位置之后的元素）
                for i in range(delete_position + 1, list_size):
                    if i < len(list_data):
                        # 计算前移后的位置（适应换行布局）
                        # 元素从位置i移动到位置i-1
                        original_row = i // elements_per_row
                        original_col = i % elements_per_row
                        original_x = array_start_x + original_col * box_width
                        original_y = array_start_y + original_row * (box_height + 30)
                        
                        # 计算目标位置（i-1的位置）
                        target_row = (i - 1) // elements_per_row
                        target_col = (i - 1) % elements_per_row
                        target_x = array_start_x + target_col * box_width
                        target_y = array_start_y + target_row * (box_height + 30)
                        
                        # 使用线性插值计算当前位置
                        shifted_x = original_x + (target_x - original_x) * animation_progress
                        shifted_y = original_y + (target_y - original_y) * animation_progress
                        
                        # 创建前移的元素
                        shifted_box = BoxSnapshot(
                            id=f"shifted_box_{i}",
                            value=str(list_data[i]),
                            x=shifted_x,
                            y=shifted_y,
                            width=box_width,
                            height=box_height,
                            color="#FFA500"  # 橙色表示正在前移的元素
                        )
                        snapshot.boxes.append(shifted_box)
                        
                        # 添加移动箭头（只在动画进行中显示）
                        if animation_progress < 0.8:  # 动画快结束时隐藏箭头
                            arrow_x = original_x - box_width // 2
                            arrow_y = original_y + box_height + 10
                            arrow_box = BoxSnapshot(
                                id=f"arrow_{i}",
                                value="←",
                                x=arrow_x,
                                y=arrow_y,
                                width=20,
                                height=20,
                                color="#FFA500"
                            )
                            snapshot.boxes.append(arrow_box)
                
                # 添加删除位置指示器
                delete_indicator = BoxSnapshot(
                    id="delete_indicator",
                    value="DELETE",
                    x=delete_x,
                    y=delete_y - 60,
                    width=box_width,
                    height=25,
                    color="#FF0000"  # 红色表示删除位置
                )
                snapshot.boxes.append(delete_indicator)
        
        return snapshot

class LinkedListAdapter:
    """链表适配器"""
    
    @staticmethod
    def to_snapshot(linked_list, start_x=100, y=200, node_spacing=120) -> StructureSnapshot:
        """将链表转换为快照"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"链表 (长度: {linked_list.size()})"
        
        # 获取动画状态
        animation_state = getattr(linked_list, '_animation_state', None)
        animation_progress = getattr(linked_list, '_animation_progress', 0.0)
        
        # 补充取删除参数
        delete_position = getattr(linked_list, '_delete_position', -1) if animation_state == 'deleting' else -1
        is_deleting = animation_state == 'deleting'
        
        # 生成节点和边快照
        current = linked_list.data.head  # 访问CustomList的head
        i = 0
        prev_node_id = None
        
        # 检查是否在插入动画中，需要调整后续节点位置
        insert_position = getattr(linked_list, '_insert_position', -1)
        is_inserting = animation_state == 'inserting'
        
        # 定义删除场景的 X 计算（前移）
        def _node_x_delete(idx: int) -> float:
            base_x = start_x + idx * node_spacing
            if is_deleting and delete_position >= 0 and idx > delete_position:
                # 0.4~0.8 匀速左移一个间距
                t = 0.0
                if animation_progress > 0.4:
                    t = min((animation_progress - 0.4) / 0.4, 1.0)
                return base_x - t * node_spacing
            return base_x
        
        # 为插入动画添加最终阶段的右移插值
        def _node_x(idx: int) -> float:
            base_x = start_x + idx * node_spacing
            if is_inserting and idx > insert_position:
                if animation_progress < 0.8:
                    return base_x
                t = (animation_progress - 0.8) / 0.2
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
                return base_x + t * node_spacing
            return base_x
        
        while current:
            # 跳过绘制 q（>=0.4 阶段）
            if is_deleting and delete_position == i and animation_progress >= 0.4:
                # 跳过绘制要删除的节点 q
                current = current.next
                i += 1
                continue
            
            node_id = f"node_{i}"
            
            # 计算节点位置
            if is_deleting:
                node_x = _node_x_delete(i)
            else:
                node_x = _node_x(i)
            node_width = 80  # 节点宽度
            node_height = 40  # 节点高度
            
            # 创建节点方框（分为左右两个区域）
            node_box = BoxSnapshot(
                id=f"{node_id}_box",
                value="",  # 方框本身不显示值
                x=node_x,
                y=y,
                width=node_width,
                height=node_height,
                color="#E8F4FD"  # 浅蓝色背景
            )
            snapshot.boxes.append(node_box)
            
            # 添加分隔线（左右区域分界线）
            separator_x = node_x + node_width * 0.7  # 左边占70%，右边占30%
            separator = BoxSnapshot(
                id=f"{node_id}_separator",
                value="",  # 分隔线不显示值
                x=separator_x,
                y=y,
                width=2,
                height=node_height,
                color="#000000"  # 黑色分隔线
            )
            snapshot.boxes.append(separator)
            
            # 左边区域：显示数据值
            data_box = BoxSnapshot(
                id=f"{node_id}_data",
                value=str(current.val),  # CustomList使用val属性
                x=node_x + 5,  # 左边距
                y=y + 5,  # 上边距
                width=separator_x - node_x - 10,  # 左边区域宽度
                height=node_height - 10,  # 高度
                color="#FFFFFF",  # 白色背景
                text_color="#000000"  # 黑色文字
            )
            snapshot.boxes.append(data_box)
            
            # 右边区域：显示箭头或NULL
            if current.next:
                # 有下一个节点，显示箭头
                arrow_box = BoxSnapshot(
                    id=f"{node_id}_arrow",
                    value="→",  # 箭头符号
                    x=separator_x + 5,
                    y=y + 5,
                    width=node_width - (separator_x - node_x) - 10,
                    height=node_height - 10,
                    color="#FFFFFF"  # 白色背景
                )
                snapshot.boxes.append(arrow_box)
                
            else:
                # 没有下一个节点，显示NULL
                null_box = BoxSnapshot(
                    id=f"{node_id}_null",
                    value="NULL",
                    x=separator_x + 5,
                    y=y + 5,
                    width=node_width - (separator_x - node_x) - 10,
                    height=node_height - 10,
                    color="#FFE6E6"  # 浅红色背景
                )
                snapshot.boxes.append(null_box)
            
            
            # 添加箭头到下一个节点（连接线）
            if prev_node_id:
                if is_deleting:
                    # 抹去 p→q：当前 i==delete_position 时不画这条直线
                    if i == delete_position:
                        pass  # 不生成 edge
                    # 抹去弧线阶段的直线 p→succ（0.2~0.8 用弧线替代）
                    elif i == delete_position + 1 and 0.2 <= animation_progress < 0.8:
                        pass  # 不生成 edge
                    else:
                        # 正常生成直线
                        edge = EdgeSnapshot(
                            from_id=f"{prev_node_id}_box",
                            to_id=f"{node_id}_box",
                            arrow_type="arrow"
                        )
                        prev_x = _node_x_delete(i - 1)
                        edge.from_x = prev_x + node_width
                        edge.from_y = y + node_height // 2
                        edge.to_x = node_x
                        edge.to_y = y + node_height // 2
                        snapshot.edges.append(edge)
                else:
                    # 非删除动画，按原逻辑生成
                    edge = EdgeSnapshot(
                        from_id=f"{prev_node_id}_box",
                        to_id=f"{node_id}_box",
                        arrow_type="arrow"
                    )
                    # 覆盖from_x以在末段插值移动前驱位置
                    if is_inserting and i - 1 > insert_position:
                        prev_x_interp = _node_x(i - 1)
                        edge.from_x = prev_x_interp + node_width
                    else:
                        prev_x = _node_x(i - 1) if is_inserting else start_x + (i - 1) * node_spacing
                        edge.from_x = prev_x + node_width
                    edge.from_y = y + node_height // 2
                    edge.to_x = node_x
                    edge.to_y = y + node_height // 2
                    snapshot.edges.append(edge)
                    # 在"断开原连接"阶段之后，移除刚刚添加的前驱→后继边
                    if is_inserting and i == insert_position and animation_progress > 0.4:
                        if snapshot.edges:
                            snapshot.edges.pop()
            
            prev_node_id = node_id
            current = current.next  # CustomList使用next属性
            i += 1
        
        # 在循环之后，专门"画出弧线/最后的直线替换"
        if is_deleting:
            p_idx = delete_position - 1
            succ_idx = delete_position + 1
            # 确保 p 与 succ 存在（succ 可能不存在于尾删）
            list_len = linked_list.size()
            if p_idx >= 0 and succ_idx < list_len:
                node_width = 80
                node_height = 40
                # 端点（与直线一致）：p 的右侧中心 -> succ 的左侧中心
                p_right_x = _node_x_delete(p_idx) + node_width
                succ_left_x = _node_x_delete(succ_idx)
                p_center_y = y + node_height // 2
                succ_center_y = y + node_height // 2
                
                if animation_progress >= 0.8:
                    # 阶段 4：弧线改回直线
                    edge = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    edge.from_x = p_right_x
                    edge.from_y = p_center_y
                    edge.to_x = succ_left_x
                    edge.to_y = succ_center_y
                    edge.color = "#000000"
                    snapshot.edges.append(edge)
                elif animation_progress >= 0.2:
                    # 阶段 2-3：用两段折线模拟弧线 p→mid→succ（mid 在节点上方）
                    mid_x = (p_right_x + succ_left_x) / 2
                    mid_y = y - 60  # 弧线高度，可按需微调
                    e1 = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    e1.from_x = p_right_x
                    e1.from_y = p_center_y
                    e1.to_x = mid_x
                    e1.to_y = mid_y
                    e1.color = "#FF8C00"  # 橙色，表示过渡
                    snapshot.edges.append(e1)
                    e2 = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    e2.from_x = mid_x
                    e2.from_y = mid_y
                    e2.to_x = succ_left_x
                    e2.to_y = succ_center_y
                    e2.color = "#FF8C00"
                    snapshot.edges.append(e2)
        
        # 处理构建动画
        if animation_state == 'building':
            build_values = getattr(linked_list, '_build_values', [])
            build_index = getattr(linked_list, '_build_index', 0)
            
            # 显示已经构建完成的节点
            for i in range(build_index):
                if i < len(build_values):
                    value = build_values[i]
                    node_x = start_x + i * node_spacing
                    node_width = 80
                    node_height = 40
                    
                    # 创建已构建节点的方框
                    node_box = BoxSnapshot(
                        id=f"built_node_{i}_box",
                        value="",
                        x=node_x,
                        y=y,
                        width=node_width,
                        height=node_height,
                        color="#E8F4FD"
                    )
                    snapshot.boxes.append(node_box)
                    
                    # 添加分隔线
                    separator_x = node_x + node_width * 0.7
                    separator = BoxSnapshot(
                        id=f"built_node_{i}_separator",
                        value="",
                        x=separator_x,
                        y=y,
                        width=2,
                        height=node_height,
                        color="#000000"
                    )
                    snapshot.boxes.append(separator)
                    
                    # 左边区域：显示数据值
                    data_box = BoxSnapshot(
                        id=f"built_node_{i}_data",
                        value=str(value),
                        x=node_x + 5,
                        y=y + 5,
                        width=separator_x - node_x - 10,
                        height=node_height - 10,
                        color="#FFFFFF",
                        text_color="#000000"
                    )
                    snapshot.boxes.append(data_box)
                    
                    # 右边区域：显示箭头
                    arrow_box = BoxSnapshot(
                        id=f"built_node_{i}_arrow",
                        value="→",
                        x=separator_x + 5,
                        y=y + 5,
                        width=node_width - (separator_x - node_x) - 10,
                        height=node_height - 10,
                        color="#FFFFFF"
                    )
                    snapshot.boxes.append(arrow_box)
                    
                    # 添加连接线
                    if i > 0:
                        edge = EdgeSnapshot(
                            from_id=f"built_node_{i - 1}_box",
                            to_id=f"built_node_{i}_box",
                            arrow_type="arrow"
                        )
                        edge.from_x = start_x + (i - 1) * node_spacing + node_width
                        edge.from_y = y + node_height // 2
                        edge.to_x = node_x
                        edge.to_y = y + node_height // 2
                        snapshot.edges.append(edge)
            
            # 显示正在构建的节点
            if build_index < len(build_values):
                new_value = build_values[build_index]
                # 计算新节点的位置（从屏幕上方移动下来）
                new_x = start_x + build_index * node_spacing
                new_y = y - 100 + (100 * animation_progress)  # 从上方移动到目标位置
                node_width = 80
                node_height = 40
                
                # 创建新节点的方框
                new_node_box = BoxSnapshot(
                    id=f"building_node_{build_index}_box",
                    value="",
                    x=new_x,
                    y=new_y,
                    width=node_width,
                    height=node_height,
                    color="#E8F4FD"
                )
                snapshot.boxes.append(new_node_box)
                
                # 添加分隔线
                separator_x = new_x + node_width * 0.7
                separator = BoxSnapshot(
                    id=f"building_node_{build_index}_separator",
                    value="",
                    x=separator_x,
                    y=new_y,
                    width=2,
                    height=node_height,
                    color="#000000"
                )
                snapshot.boxes.append(separator)
                
                # 左边区域：显示数据值
                data_box = BoxSnapshot(
                    id=f"building_node_{build_index}_data",
                    value=str(new_value),
                    x=new_x + 5,
                    y=new_y + 5,
                    width=separator_x - new_x - 10,
                    height=node_height - 10,
                    color="#FFFFFF",  # 白色背景
                    text_color="#000000"  # 黑色文字
                )
                snapshot.boxes.append(data_box)
                
                # 右边区域：显示箭头
                arrow_box = BoxSnapshot(
                    id=f"building_node_{build_index}_arrow",
                    value="→",
                    x=separator_x + 5,
                    y=new_y + 5,
                    width=node_width - (separator_x - new_x) - 10,
                    height=node_height - 10,
                    color="#FFFFFF"
                )
                snapshot.boxes.append(arrow_box)
                
                # 如果动画进度足够，显示连接线
                if animation_progress > 0.5 and build_index > 0:
                    edge = EdgeSnapshot(
                        from_id=f"built_node_{build_index - 1}_box",
                        to_id=f"building_node_{build_index}_box",
                        arrow_type="arrow"
                    )
                    edge.from_x = start_x + (build_index - 1) * node_spacing + node_width
                    edge.from_y = y + node_height // 2
                    edge.to_x = new_x
                    edge.to_y = new_y + node_height // 2
                    snapshot.edges.append(edge)
        
        # 处理插入动画
        elif animation_state == 'inserting':
            new_value = getattr(linked_list, '_new_value', None)
            insert_position = getattr(linked_list, '_insert_position', 0)
            
            if new_value is not None:
                # 计算新节点的位置（先在上方，然后移动到目标位置）
                node_width = 80
                node_height = 40
                new_x = start_x + insert_position * node_spacing
                
                # 调整新节点Y坐标：浮入悬停→末段下落归位
                hover_offset = max(80, int(node_height * 2))
                hover_y = y - hover_offset
                
                if animation_progress < 0.2:
                    # 从更高处先落到"悬浮位"
                    start_y = hover_y - 60
                    k = animation_progress / 0.2
                    new_y = start_y + (hover_y - start_y) * k
                elif animation_progress < 0.8:
                    # 悬浮于链表上方
                    new_y = hover_y
                else:
                    # 末段再落回链表行内
                    k = (animation_progress - 0.8) / 0.2
                    if k < 0.0:
                        k = 0.0
                    elif k > 1.0:
                        k = 1.0
                    new_y = hover_y + (y - hover_y) * k
                
                # 创建新节点的方框
                new_node_box = BoxSnapshot(
                    id="inserting_node_box",
                    value="",
                    x=new_x,
                    y=new_y,
                    width=node_width,
                    height=node_height,
                    color="#E8F4FD"
                )
                snapshot.boxes.append(new_node_box)
                
                # 添加分隔线
                separator_x = new_x + node_width * 0.7
                separator = BoxSnapshot(
                    id="inserting_node_separator",
                    value="",
                    x=separator_x,
                    y=new_y,
                    width=2,
                    height=node_height,
                    color="#000000"
                )
                snapshot.boxes.append(separator)
                
                # 左边区域：显示数据值
                data_box = BoxSnapshot(
                    id="inserting_node_data",
                    value=str(new_value),
                    x=new_x + 5,
                    y=new_y + 5,
                    width=separator_x - new_x - 10,
                    height=node_height - 10,
                    color="#FFFFFF",  # 白色背景
                    text_color="#000000"  # 黑色文字
                )
                snapshot.boxes.append(data_box)
                
                # 右边区域：显示箭头
                arrow_box = BoxSnapshot(
                    id="inserting_node_arrow",
                    value="→",
                    x=separator_x + 5,
                    y=new_y + 5,
                    width=node_width - (separator_x - new_x) - 10,
                    height=node_height - 10,
                    color="#FFFFFF"
                )
                snapshot.boxes.append(arrow_box)
                
                # 显示插入指示器
                if animation_progress < 0.2:
                    indicator_text = f"新节点出现"
                elif animation_progress < 0.4:
                    indicator_text = "连接后继节点"
                elif animation_progress < 0.6:
                    indicator_text = "断开原连接"
                elif animation_progress < 0.8:
                    indicator_text = "连接前驱节点"
                else:
                    indicator_text = "整体后移"
                
                insert_indicator = BoxSnapshot(
                    id="insert_indicator",
                    value=indicator_text,
                    x=new_x - 20,
                    y=new_y - 30,
                    width=120,
                    height=20,
                    color="#FF6B6B"
                )
                snapshot.boxes.append(insert_indicator)
                
                # 分阶段显示箭头连接和节点移动
                if animation_progress > 0.2:
                    # 第一阶段：新节点连接到后继节点
                    if insert_position < len(linked_list.data):
                        edge = EdgeSnapshot(
                            from_id="inserting_node_box",
                            to_id=f"node_{insert_position}_box",
                            arrow_type="arrow"
                        )
                        edge.from_x = new_x + node_width
                        edge.from_y = new_y + node_height // 2
                        # 后继节点在末段右移，按进度插值其X坐标
                        base_succ_x = start_x + insert_position * node_spacing
                        if animation_progress < 0.8:
                            succ_x = base_succ_x
                        else:
                            t = (animation_progress - 0.8) / 0.2
                            if t < 0.0:
                                t = 0.0
                            elif t > 1.0:
                                t = 1.0
                            succ_x = base_succ_x + t * node_spacing
                        edge.to_x = succ_x
                        edge.to_y = y + node_height // 2
                        snapshot.edges.append(edge)
                
                if animation_progress >= 0.4:
                    # 第三阶段：前驱节点连接到新节点
                    if insert_position > 0:
                        edge = EdgeSnapshot(
                            from_id=f"node_{insert_position - 1}_box",
                            to_id="inserting_node_box",
                            arrow_type="arrow"
                        )
                        edge.from_x = start_x + (insert_position - 1) * node_spacing + node_width
                        edge.from_y = y + node_height // 2
                        edge.to_x = new_x
                        edge.to_y = new_y + node_height // 2
                        snapshot.edges.append(edge)
                
                if animation_progress > 0.8:
                    # 第四阶段：新节点后面的所有节点整体向后移动
                    # 这里需要重新计算所有后续节点的位置
                    for i in range(insert_position + 1, len(linked_list.data)):
                        # 后续节点向右移动一个位置
                        shifted_x = start_x + (i + 1) * node_spacing
                        # 这里可以添加移动动画效果
                        pass
        
        return snapshot

class StackAdapter:
    """栈适配器"""
    
    @staticmethod
    def to_snapshot(stack, start_x=100, y=200, box_width=60, box_height=40) -> StructureSnapshot:
        """将栈转换为快照"""
        snapshot = StructureSnapshot()
        stack_size = stack.size()
        
        # 检查是否有动画状态
        animation_state = getattr(stack, '_animation_state', None)
        if animation_state == 'building':
            build_values = getattr(stack, '_build_values', [])
            snapshot.hint_text = f"栈 (正在构建... 进度: {len(build_values)} 个元素)"
        elif animation_state == 'pushing':
            snapshot.hint_text = f"栈 (正在入栈... top = {stack_size}, 长度: {stack_size})"
        elif animation_state == 'popping':
            snapshot.hint_text = f"栈 (正在出栈... top = {stack_size}, 长度: {stack_size})"
        else:
            snapshot.hint_text = f"栈 (top = {stack_size}, 长度: {stack_size})"
        
        # 显示垂直栈（竖着显示）
        stack_start_x = start_x + 200  # 栈在右侧
        stack_start_y = y + 100  # 栈的起始位置（给栈底留空间）
        
        # 动态绘制：只绘制实际存在的元素
        if stack_size > 0:
            # 获取栈内容并转换为列表（从栈底到栈顶的顺序）
            stack_list = stack.data.to_array()  # 使用to_array方法获取正确的顺序
            
            # 显示栈中的元素（从下往上堆叠）
            # stack_list是从栈底到栈顶的顺序
            # stack_list[0]是栈底，应该显示在最下面
            # stack_list[-1]是栈顶，应该显示在最上面
            for i, value in enumerate(stack_list):
                # 计算元素在栈中的位置（从下往上）
                # 栈底元素（i=0）应该在最下面
                # 栈顶元素（i=len-1）应该在最上面
                stack_position = stack_size - 1 - i
                stack_box = BoxSnapshot(
                    id=f"stack_box_{i}",
                    value=str(value),
                    x=stack_start_x,
                    y=stack_start_y + stack_position * (box_height + 2),
                    width=box_width,
                    height=box_height,
                    color="#4C78A8"  # 蓝色
                )
                snapshot.boxes.append(stack_box)
        
        # 添加栈底指示器（动态位置）
        if stack_size > 0:
            # 栈底位置在最后一个元素下方
            bottom_y = stack_start_y + stack_size * (box_height + 2) + 5
        else:
            # 栈空时，栈底在起始位置下方
            bottom_y = stack_start_y + 5
            
        bottom_box = BoxSnapshot(
            id="bottom_indicator",
            value="栈底",
            x=stack_start_x - 20,
            y=bottom_y,
            width=box_width + 40,
            height=25,
            color="#90EE90"  # 绿色
        )
        snapshot.boxes.append(bottom_box)
        
        # 添加top指针指示器（指向当前栈顶位置）
        # 在动画过程中，top指针需要跟随栈顶元素移动
        if stack_size > 0:
            # top指向栈顶元素的位置
            # 栈顶元素的位置是 stack_start_y + 0 * (box_height + 2)
            top_y = stack_start_y + box_height // 2
        else:
            # 栈空时，top指向栈底
            top_y = bottom_y
        
        # 如果在入栈动画中，top指针在新元素到达栈顶之前待在原来的栈顶
        if animation_state == 'pushing':
            new_value = getattr(stack, '_new_value', None)
            animation_progress = getattr(stack, '_animation_progress', 0.0)
            if new_value is not None:
                # 计算新元素的目标位置（栈顶位置）
                target_y = stack_start_y + box_height // 2
                
                # 计算起始位置（屏幕正上方）
                start_y = 50 + box_height // 2  # 屏幕正上方
                
                # 计算新元素的当前位置
                new_element_y = start_y + (target_y - start_y) * animation_progress
                
                # 如果新元素还没到达栈顶（距离栈顶还有一定距离），top指针待在原来的栈顶
                if new_element_y > target_y + 20:  # 20像素的容差
                    # top指针待在原来的栈顶位置（不移动）
                    # top_y 保持之前计算的值，即原来的栈顶位置
                    pass
                else:
                    # 新元素已经接近或到达栈顶，top指针移动到新的栈顶位置
                    # 新的栈顶位置就是新元素到达的位置
                    top_y = target_y
        
        top_box = BoxSnapshot(
            id="top_indicator",
            value="top",
            x=stack_start_x + box_width + 10,
            y=top_y,
            width=box_width,
            height=25,
            color="#FF6B6B"  # 红色
        )
        snapshot.boxes.append(top_box)
        
        # 如果正在构建动画，显示逐步构建过程
        if animation_state == 'building':
            build_values = getattr(stack, '_build_values', [])
            build_index = getattr(stack, '_build_index', 0)
            animation_progress = getattr(stack, '_animation_progress', 0.0)
            
            # 显示已经构建完成的元素
            for i in range(build_index):
                if i < len(build_values):
                    value = build_values[i]
                    # 计算元素在栈中的位置（从下往上）
                    stack_position = build_index - 1 - i
                    stack_box = BoxSnapshot(
                        id=f"built_stack_box_{i}",
                        value=str(value),
                        x=stack_start_x,
                        y=stack_start_y + stack_position * (box_height + 2),
                        width=box_width,
                        height=box_height,
                        color="#4C78A8"  # 蓝色
                    )
                    snapshot.boxes.append(stack_box)
            
            # 显示正在构建的元素（从上方掉下来）
            if build_index < len(build_values):
                new_value = build_values[build_index]
                # 计算目标位置（栈顶位置）
                target_position = build_index
                target_x = stack_start_x
                target_y = stack_start_y + target_position * (box_height + 2)
                
                # 计算起始位置（屏幕正上方）
                start_x_pos = target_x
                start_y_pos = 50  # 屏幕正上方
                
                # 使用线性插值计算当前位置
                current_x = start_x_pos + (target_x - start_x_pos) * animation_progress
                current_y = start_y_pos + (target_y - start_y_pos) * animation_progress
                
                new_node = BoxSnapshot(
                    id="building_node",
                    value=str(new_value),
                    x=current_x,
                    y=current_y,
                    width=box_width,
                    height=box_height,
                    color="#FF6B6B"  # 红色表示正在移动的节点
                )
                snapshot.boxes.append(new_node)
        
        # 如果正在入栈动画，显示新节点从外部掉入栈顶
        elif animation_state == 'pushing':
            new_value = getattr(stack, '_new_value', None)
            animation_progress = getattr(stack, '_animation_progress', 0.0)
            if new_value is not None:
                # 计算目标位置（栈顶位置）
                target_x = stack_start_x
                target_y = stack_start_y
                
                # 设置目标位置到栈对象
                stack.set_animation_target(target_x, target_y)
                
                # 计算起始位置（屏幕正上方）
                start_x = stack_start_x
                start_y = 50  # 屏幕正上方
                
                # 使用线性插值计算当前位置
                current_x = start_x + (target_x - start_x) * animation_progress
                current_y = start_y + (target_y - start_y) * animation_progress
                
                new_node = BoxSnapshot(
                    id="new_node",
                    value=str(new_value),
                    x=current_x,
                    y=current_y,
                    width=box_width,
                    height=box_height,
                    color="#FF6B6B"  # 红色表示正在移动的节点
                )
                snapshot.boxes.append(new_node)
        
        # 如果正在出栈动画，显示栈顶元素向上弹出
        elif animation_state == 'popping':
            pop_value = getattr(stack, '_pop_value', None)
            animation_progress = getattr(stack, '_animation_progress', 0.0)
            if pop_value is not None:
                # 计算起始位置（栈顶位置）
                start_position = stack_size - 1
                start_x = stack_start_x
                start_y = stack_start_y + start_position * (box_height + 2)
                
                # 计算目标位置（向上弹出）
                target_x = stack_start_x
                target_y = 50  # 屏幕正上方
                
                # 使用线性插值计算当前位置
                current_x = start_x + (target_x - start_x) * animation_progress
                current_y = start_y + (target_y - start_y) * animation_progress
                
                pop_node = BoxSnapshot(
                    id="pop_node",
                    value=str(pop_value),
                    x=current_x,
                    y=current_y,
                    width=box_width,
                    height=box_height,
                    color="#FF6B6B"  # 红色
                )
                snapshot.boxes.append(pop_node)
        
        # 添加状态提示
        if stack_size == 0:
            # 栈空提示
            empty_indicator = BoxSnapshot(
                id="stack_empty_indicator",
                value="栈空！",
                x=stack_start_x - 50,
                y=stack_start_y - 30,
                width=box_width + 100,
                height=25,
                color="#90EE90"  # 绿色
            )
            snapshot.boxes.append(empty_indicator)
        
        return snapshot

class BinaryTreeAdapter:
    """改进的二叉树适配器 - 使用递归子树宽度计算"""
    
    @staticmethod
    def _calculate_subtree_width(node, node_width=60, min_spacing=100):
        """递归计算子树所需的最小宽度"""
        if not node:
            return 0
        
        if not node.left and not node.right:
            # 叶子节点只需要自身宽度
            return node_width
        
        # 计算左右子树宽度
        left_width = BinaryTreeAdapter._calculate_subtree_width(
            node.left, node_width, min_spacing)
        right_width = BinaryTreeAdapter._calculate_subtree_width(
            node.right, node_width, min_spacing)
        
        # 当前节点需要的总宽度 = max(自身宽度, 左子树宽度 + 右子树宽度 + 间距)
        subtree_total_width = left_width + right_width
        if left_width > 0 and right_width > 0:
            subtree_total_width += min_spacing
        
        return max(node_width, subtree_total_width)
    
    @staticmethod
    def _layout_tree(node, center_x, y, level_height=80, node_width=60, min_spacing=100):
        """递归布局二叉树，确保子树不重叠"""
        if not node:
            return {}
        
        positions = {}
        
        # 当前节点位置
        positions[node] = (center_x, y)
        
        if not node.left and not node.right:
            # 叶子节点，直接返回
            return positions
        
        # 计算左右子树需要的宽度
        left_width = BinaryTreeAdapter._calculate_subtree_width(
            node.left, node_width, min_spacing)
        right_width = BinaryTreeAdapter._calculate_subtree_width(
            node.right, node_width, min_spacing)
        
        # 计算子节点位置
        if node.left and node.right:
            # 两个子节点
            total_child_width = left_width + right_width + min_spacing
            left_center = center_x - total_child_width / 2 + left_width / 2
            right_center = center_x + total_child_width / 2 - right_width / 2
            
            # 递归布局子树
            left_positions = BinaryTreeAdapter._layout_tree(
                node.left, left_center, y + level_height, level_height, node_width, min_spacing)
            right_positions = BinaryTreeAdapter._layout_tree(
                node.right, right_center, y + level_height, level_height, node_width, min_spacing)
            
            positions.update(left_positions)
            positions.update(right_positions)
            
        elif node.left:
            # 只有左子节点
            left_center = center_x - min_spacing / 2
            left_positions = BinaryTreeAdapter._layout_tree(
                node.left, left_center, y + level_height, level_height, node_width, min_spacing)
            positions.update(left_positions)
            
        elif node.right:
            # 只有右子节点
            right_center = center_x + min_spacing / 2
            right_positions = BinaryTreeAdapter._layout_tree(
                node.right, right_center, y + level_height, level_height, node_width, min_spacing)
            positions.update(right_positions)
        
        return positions
    
    @staticmethod
    def _add_edges(node, positions, snapshot):
        """添加树的边连接"""
        if not node:
            return
        
        node_x, node_y = positions[node]
        node_id = f"node_{id(node)}"
        radius = AVLAdapter.NODE_RADIUS
        radius = BSTAdapter.NODE_RADIUS
        
        # 添加到左子节点的边
        if node.left:
            left_x, left_y = positions[node.left]
            left_id = f"node_{id(node.left)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=left_id,
                color="#2E86AB",
                arrow_type="line"
            )
            # 设置连线坐标 - 从红色左指针方框出发，连接到子节点中心
            edge.from_x = node_x - 60  # 左指针方框位置
            edge.from_y = node_y - 30  # 左指针方框位置（稍微偏下）
            edge.to_x = left_x- 40  # 子节点中心x坐标
            edge.to_y = left_y - 10  # 子节点中心y坐标（稍微偏上）
            
            snapshot.edges.append(edge)
            
            # 递归处理左子树
            BinaryTreeAdapter._add_edges(node.left, positions, snapshot)
        
        # 添加到右子节点的边
        if node.right:
            right_x, right_y = positions[node.right]
            right_id = f"node_{id(node.right)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=right_id,
                color="#2E86AB",
                arrow_type="line"
            )
            # 设置连线坐标 - 从绿色右指针方框出发，连接到子节点中心
            edge.from_x = node_x   # 右指针方框位置
            edge.from_y = node_y - 30  # 右指针方框位置
            edge.to_x = right_x-40  # 子节点中心x坐标
            edge.to_y = right_y -10  # 子节点中心y坐标（稍微偏下）
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            BinaryTreeAdapter._add_edges(node.right, positions, snapshot)
    
    @staticmethod
    def to_snapshot(binary_tree, start_x=640, y=200, level_height=80, node_width=60, min_spacing=100) -> StructureSnapshot:
        """将二叉树转换为快照 - 使用改进的布局算法"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"二叉树 (节点数: {len(binary_tree.get_all_node_values())})"
        
        # 获取动画状态
        animation_state = getattr(binary_tree, '_animation_state', None)
        animation_progress = getattr(binary_tree, '_animation_progress', 0.0)
        
        if not binary_tree.root:
            return snapshot
        
        # 使用改进的布局算法
        positions = BinaryTreeAdapter._layout_tree(
            binary_tree.root, start_x, y, level_height, node_width, min_spacing)
        
        # 生成节点快照
        for node, (x, y_pos) in positions.items():
            node_id = f"node_{id(node)}"
            
            # 检查是否是动画中的新节点
            is_new_node = (animation_state == 'inserting' and 
                          hasattr(binary_tree, '_new_value') and 
                          str(binary_tree._new_value) == str(node.value))
            
            if is_new_node:
                target_x, target_y = x, y_pos
                start_x_anim = x
                start_y_anim = 50
                current_x = start_x_anim + (target_x - start_x_anim) * animation_progress
                current_y = start_y_anim + (target_y - start_y_anim) * animation_progress
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), current_x, current_y, "#FF6B6B"
                )
            else:
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#1f4e79"  # 深蓝色
                )
            
            snapshot.nodes.append(node_snapshot)
        
        # 生成边快照
        BinaryTreeAdapter._add_edges(binary_tree.root, positions, snapshot)
        
        # 显示根指针 - 放在根节点上方
        root_pointer_x = start_x - 30  # 与根节点中心对齐
        root_pointer_y = y - 50  # 在根节点上方
        root_pointer_box = BoxSnapshot(
            id="root_pointer",
            value="root",
            x=root_pointer_x,
            y=root_pointer_y,
            width=60,
            height=30,
            color="#FFD700"  # 金色
        )
        snapshot.boxes.append(root_pointer_box)
        
        # 添加根指针到根节点的连接
        if binary_tree.root:
            root_edge = EdgeSnapshot(
                from_id="root_pointer",
                to_id=f"node_{id(binary_tree.root)}",
                arrow_type="arrow"
            )
            root_edge.from_x = root_pointer_x + 30  # 从root标签中心
            root_edge.from_y = root_pointer_y + 30  # 从root标签底部
            root_edge.to_x = start_x  # 到根节点中心
            root_edge.to_y = y - 20  # 到根节点顶部
            snapshot.edges.append(root_edge)
        
        # 处理创建根节点动画
        if animation_state == 'creating_root':
            new_value = getattr(binary_tree, '_new_value', None)
            if new_value is not None:
                # 计算目标位置（根节点位置）
                target_x = start_x
                target_y = y
                
                # 计算起始位置（屏幕正上方）
                start_x_pos = target_x
                start_y_pos = 50  # 屏幕正上方
                
                # 使用线性插值计算当前位置
                current_x = start_x_pos + (target_x - start_x_pos) * animation_progress
                current_y = start_y_pos + (target_y - start_y_pos) * animation_progress
                
                # 创建动画中的根节点
                node_snapshot = NodeSnapshot(
                    id="animating_root",
                    value=str(new_value),
                    x=current_x - 30,
                    y=current_y - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#FF6B6B"  # 红色表示正在移动
                )
                snapshot.nodes.append(node_snapshot)
        
        # 处理插入节点动画
        elif animation_state == 'inserting':
            new_value = getattr(binary_tree, '_new_value', None)
            parent_value = getattr(binary_tree, '_parent_value', None)
            insert_position = getattr(binary_tree, '_insert_position', None)
            
            if new_value is not None and parent_value is not None:
                # 找到父节点位置
                parent_node = binary_tree.find_node_by_value(parent_value)
                if parent_node and parent_node in positions:
                    # 计算父节点的实际位置
                    parent_x, parent_y = positions[parent_node]
                    
                    # 计算目标位置（子节点位置）
                    if insert_position == 'left':
                        target_x = parent_x - 100
                    else:  # right
                        target_x = parent_x + 100
                    target_y = parent_y + level_height
                    
                    # 计算起始位置（屏幕正上方）
                    start_x_pos = target_x
                    start_y_pos = 50  # 屏幕正上方
                    
                    # 使用线性插值计算当前位置
                    current_x = start_x_pos + (target_x - start_x_pos) * animation_progress
                    current_y = start_y_pos + (target_y - start_y_pos) * animation_progress
                    
                    # 创建动画中的新节点
                    node_snapshot = NodeSnapshot(
                        id="animating_insert",
                        value=str(new_value),
                        x=current_x - 30,
                        y=current_y - 20,
                        node_type="box",
                        width=60,
                        height=40,
                        color="#FF6B6B"  # 红色表示正在移动
                    )
                    snapshot.nodes.append(node_snapshot)
        
        return snapshot
    

class BSTAdapter:
    """二叉搜索树适配器 - 使用与链式二叉树相同的布局算法"""
    NODE_DIAMETER = 60
    NODE_RADIUS = NODE_DIAMETER / 2
    
    @staticmethod
    def _circle_snapshot(node_id, value, center_x, center_y, color, text_color="#FFFFFF"):
        return NodeSnapshot(
            id=node_id,
            value=value,
            x=center_x,
            y=center_y,
            node_type="circle",
            width=BSTAdapter.NODE_DIAMETER,
            height=BSTAdapter.NODE_DIAMETER,
            color=color,
            text_color=text_color
        )
    
    @staticmethod
    def _calculate_subtree_width(node, node_width=60, min_spacing=100):
        """递归计算子树所需的最小宽度"""
        if not node:
            return 0
        
        if not node.left and not node.right:
            # 叶子节点只需要自身宽度
            return node_width
        
        # 计算左右子树宽度
        left_width = BSTAdapter._calculate_subtree_width(
            node.left, node_width, min_spacing)
        right_width = BSTAdapter._calculate_subtree_width(
            node.right, node_width, min_spacing)
        
        # 当前节点需要的总宽度 = max(自身宽度, 左子树宽度 + 右子树宽度 + 间距)
        subtree_total_width = left_width + right_width
        if left_width > 0 and right_width > 0:
            subtree_total_width += min_spacing*1.5
        
        return max(node_width, subtree_total_width)
    
    @staticmethod
    def _layout_tree(node, center_x, y, level_height=80, node_width=60, min_spacing=100):
        """递归布局二叉树，确保子树不重叠"""
        if not node:
            return {}
        
        positions = {}
        
        # 当前节点位置
        positions[node] = (center_x, y)
        
        if not node.left and not node.right:
            # 叶子节点，直接返回
            return positions
        
        # 计算左右子树需要的宽度
        left_width = BSTAdapter._calculate_subtree_width(
            node.left, node_width, min_spacing)
        right_width = BSTAdapter._calculate_subtree_width(
            node.right, node_width, min_spacing)
        
        # 计算子节点位置
        if node.left and node.right:
            # 两个子节点
            total_child_width = left_width + right_width + min_spacing * 1.5
            left_center = center_x - total_child_width / 2 + left_width / 2
            right_center = center_x + total_child_width / 2 - right_width / 2
            
            # 递归布局子树
            left_positions = BSTAdapter._layout_tree(
                node.left, left_center, y + level_height, level_height, node_width, min_spacing)
            right_positions = BSTAdapter._layout_tree(
                node.right, right_center, y + level_height, level_height, node_width, min_spacing)
            
            positions.update(left_positions)
            positions.update(right_positions)
            
        elif node.left:
            # 只有左子节点
            left_center = center_x - min_spacing / 2
            left_positions = BSTAdapter._layout_tree(
                node.left, left_center, y + level_height, level_height, node_width, min_spacing)
            positions.update(left_positions)
            
        elif node.right:
            # 只有右子节点
            right_center = center_x + min_spacing / 2
            right_positions = BSTAdapter._layout_tree(
                node.right, right_center, y + level_height, level_height, node_width, min_spacing)
            positions.update(right_positions)
        
        return positions
    
    @staticmethod
    def _add_edges(node, positions, snapshot):
        """添加树的边连接"""
        if not node:
            return
        
        node_x, node_y = positions[node]
        node_id = f"node_{id(node)}"
        
        # 添加到左子节点的边
        if node.left:
            left_x, left_y = positions[node.left]
            left_id = f"node_{id(node.left)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=left_id,
                color="#2E86AB",
                arrow_type="line"
            )
            edge.from_x = node_x
            edge.from_y = node_y + BSTAdapter.NODE_RADIUS
            edge.to_x = left_x
            edge.to_y = left_y - BSTAdapter.NODE_RADIUS
            
            snapshot.edges.append(edge)
            
            # 递归处理左子树
            BSTAdapter._add_edges(node.left, positions, snapshot)
        
        # 添加到右子节点的边
        if node.right:
            right_x, right_y = positions[node.right]
            right_id = f"node_{id(node.right)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=right_id,
                color="#2E86AB",
                arrow_type="line"
            )
            edge.from_x = node_x
            edge.from_y = node_y + BSTAdapter.NODE_RADIUS
            edge.to_x = right_x
            edge.to_y = right_y - BSTAdapter.NODE_RADIUS
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            BSTAdapter._add_edges(node.right, positions, snapshot)
    
    @staticmethod
    def to_snapshot(bst, start_x=640, y=200, level_height=120, node_width=60, min_spacing=100) -> StructureSnapshot:
        """将BST转换为快照 - 使用与链式二叉树相同的布局算法"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"二叉搜索树 (节点数: {len(bst.traverse_inorder())})"
        
        # 获取动画状态
        animation_state = getattr(bst, '_animation_state', None)
        animation_progress = getattr(bst, '_animation_progress', 0.0)
        traversal_current_node = getattr(bst, '_traversal_current_node', None)
        traversal_visited_nodes = set(getattr(bst, '_traversal_visited_nodes', set()) or [])
        traversal_order = getattr(bst, '_traversal_order', None)
        
        # 添加删除动画的步骤说明
        if animation_state == 'deleting':
            step_details = BSTAdapter._get_delete_step_details(bst, animation_progress)
            snapshot.step_details = step_details
        
        # 添加比较信息
        if animation_state == 'inserting' and hasattr(bst, '_insert_comparison_result') and bst._insert_comparison_result:
            if bst._insert_comparison_result == 'less':
                snapshot.comparison_text = f"新值 {bst._insert_value} < 当前值 {bst._current_search_node_value} → 左"
            elif bst._insert_comparison_result == 'greater':
                snapshot.comparison_text = f"新值 {bst._insert_value} > 当前值 {bst._current_search_node_value} → 右"
            else:
                snapshot.comparison_text = f"新值 {bst._insert_value} = 当前值 {bst._current_search_node_value} → 已存在"
        elif animation_state == 'searching' and hasattr(bst, '_comparison_result') and bst._comparison_result:
            if bst._comparison_result == 'less':
                snapshot.comparison_text = f"查找值 {bst._search_value} < 当前值 {bst._current_search_node_value} → 左"
            elif bst._comparison_result == 'greater':
                snapshot.comparison_text = f"查找值 {bst._search_value} > 当前值 {bst._current_search_node_value} → 右"
            else:
                snapshot.comparison_text = f"查找值 {bst._search_value} = 当前值 {bst._current_search_node_value} → 找到！"
        elif animation_state == 'search_found':
            snapshot.comparison_text = f"找到目标值: {bst._search_value}"
        elif animation_state == 'search_not_found':
            snapshot.comparison_text = f"未找到目标值: {bst._search_value}"
        elif animation_state == 'deleting' and hasattr(bst, '_delete_comparison_result') and bst._delete_comparison_result:
            if bst._delete_comparison_result == 'less':
                snapshot.comparison_text = f"删除值 {bst._delete_value} < 当前值 {bst._current_search_node_value} → 左"
            elif bst._delete_comparison_result == 'greater':
                snapshot.comparison_text = f"删除值 {bst._delete_value} > 当前值 {bst._current_search_node_value} → 右"
            else:
                snapshot.comparison_text = f"删除值 {bst._delete_value} = 当前值 {bst._current_search_node_value} → 找到要删除的节点"
        elif animation_state == 'delete_not_found':
            snapshot.comparison_text = f"未找到要删除的值: {bst._delete_value}"
        else:
            snapshot.comparison_text = ""

        if traversal_order and (traversal_current_node or traversal_visited_nodes):
            order_map = {
                'preorder': '前序',
                'inorder': '中序',
                'postorder': '后序',
                'levelorder': '层序'
            }
            order_text = order_map.get(traversal_order, '遍历')
            if traversal_current_node:
                detail_line = f"{order_text}遍历：访问 {traversal_current_node.value}"
            else:
                detail_line = f"{order_text}遍历：已完成"
            existing_details = snapshot.step_details
            if existing_details is None:
                snapshot.step_details = [detail_line]
            elif isinstance(existing_details, list):
                snapshot.step_details.append(detail_line)
            else:
                snapshot.step_details = [existing_details, detail_line]
        
        # 处理创建根节点动画（必须在检查root之前，因为树为空时也需要显示动画）
        if animation_state == 'creating_root':
            new_value = getattr(bst, '_new_value', None)
            if new_value is not None:
                # 计算目标位置（根节点位置）
                target_x = start_x
                target_y = y
                
                # 计算起始位置（屏幕正上方）
                start_x_pos = target_x
                start_y_pos = 50  # 屏幕正上方
                
                # 使用线性插值计算当前位置
                current_x = start_x_pos + (target_x - start_x_pos) * animation_progress
                current_y = start_y_pos + (target_y - start_y_pos) * animation_progress
                
                # 创建动画中的根节点
                node_snapshot = BSTAdapter._circle_snapshot(
                    "animating_root", str(new_value), current_x, current_y, "#FF6B6B"
                )
                snapshot.nodes.append(node_snapshot)
                
                # 显示根指针（即使树为空，动画时也要显示）
                root_pointer_x = start_x - 30
                root_pointer_y = y - 50
                root_pointer_box = BoxSnapshot(
                    id="root_pointer",
                    value="root",
                    x=root_pointer_x,
                    y=root_pointer_y,
                    width=60,
                    height=30,
                    color="#FFD700"  # 金色
                )
                snapshot.boxes.append(root_pointer_box)
                
                # 添加根指针到动画节点的连接
                root_edge = EdgeSnapshot(
                    from_id="root_pointer",
                    to_id="animating_root",
                    arrow_type="arrow"
                )
                root_edge.from_x = root_pointer_x + 30
                root_edge.from_y = root_pointer_y + 30
                root_edge.to_x = current_x
                root_edge.to_y = current_y - BSTAdapter.NODE_RADIUS
                snapshot.edges.append(root_edge)
        
        if not bst.root:
            return snapshot
        
        # 使用改进的布局算法
        positions = BSTAdapter._layout_tree(
            bst.root, start_x, y, level_height, node_width, min_spacing)
        
        # 生成节点快照
        for node, (x, y_pos) in positions.items():
            node_id = f"node_{id(node)}"
            
            # 检查是否是动画中的新节点
            is_new_node = (animation_state == 'inserting' and 
                          hasattr(bst, '_new_value') and 
                          str(bst._new_value) == str(node.value))
            
            # 检查是否是查找动画中的节点
            is_searching_node = (animation_state == 'searching' and 
                               hasattr(bst, '_current_search_node_value') and 
                               str(bst._current_search_node_value) == str(node.value))
            is_found_node = (animation_state == 'search_found' and 
                           hasattr(bst, '_search_result_node_value') and 
                           str(bst._search_result_node_value) == str(node.value))
            is_last_searched_node = (animation_state == 'search_not_found' and 
                                   hasattr(bst, '_last_search_node_value') and 
                                   str(bst._last_search_node_value) == str(node.value))
            
            # 检查是否是插入比较动画中的节点
            is_insert_comparing_node = (animation_state == 'inserting' and 
                                      hasattr(bst, '_current_search_node_value') and 
                                      str(bst._current_search_node_value) == str(node.value))
            
            # 检查是否是删除动画中的节点
            is_deleting_node = (animation_state == 'deleting' and 
                              hasattr(bst, '_current_search_node_value') and 
                              str(bst._current_search_node_value) == str(node.value))
            is_delete_target_node = (animation_state == 'deleting' and 
                                   hasattr(bst, '_delete_target_node') and 
                                   str(bst._delete_target_node) == str(node.value))
            is_delete_replacement_node = (animation_state == 'deleting' and 
                                        hasattr(bst, '_delete_replacement_node') and 
                                        str(bst._delete_replacement_node) == str(node.value))
            is_traversal_current = (traversal_current_node is not None and node is traversal_current_node)
            is_traversal_visited = (not is_traversal_current and node in traversal_visited_nodes)
            
            if is_new_node:
                # 新节点动画效果
                target_x, target_y = x, y_pos
                start_x_anim = x
                start_y_anim = 50  # 从屏幕上方开始
                
                # 使用动画进度插值
                current_x = start_x_anim + (target_x - start_x_anim) * animation_progress
                current_y = start_y_anim + (target_y - start_y_anim) * animation_progress
                
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=current_x - 30,  # 节点中心对齐
                    y=current_y - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#FF6B6B"  # 红色表示正在插入的节点
                )
            elif is_traversal_current:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#FFD700"
                )
            elif is_traversal_visited:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#FFA500"
                )
            elif is_searching_node or is_insert_comparing_node:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#FFD700"
                )
            elif is_found_node:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#00FF00"
                )
            elif is_last_searched_node:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#FFA500"
                )
            elif is_deleting_node:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#FFD700"
                )
            elif is_delete_target_node:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#FF0000"
                )
            elif is_delete_replacement_node:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#0000FF"
                )
            else:
                node_snapshot = BSTAdapter._circle_snapshot(
                    node_id, str(node.value), x, y_pos, "#1f4e79"
                )
            
            snapshot.nodes.append(node_snapshot)
        
        # 生成边快照
        BSTAdapter._add_edges(bst.root, positions, snapshot)
        
        # 显示根指针 - 放在根节点上方
        root_pointer_x = start_x - 30  # 与根节点中心对齐
        root_pointer_y = y - 50  # 在根节点上方
        root_pointer_box = BoxSnapshot(
            id="root_pointer",
            value="root",
            x=root_pointer_x,
            y=root_pointer_y,
            width=60,
            height=30,
            color="#FFD700"  # 金色
        )
        snapshot.boxes.append(root_pointer_box)
        
        # 添加根指针到根节点的连接（只有在不是creating_root动画时才添加，避免重复）
        if bst.root and animation_state != 'creating_root':
            root_edge = EdgeSnapshot(
                from_id="root_pointer",
                to_id=f"node_{id(bst.root)}",
                arrow_type="arrow"
            )
            root_edge.from_x = root_pointer_x + 30  # 从root标签中心
            root_edge.from_y = root_pointer_y + 30  # 从root标签底部
            root_edge.to_x = start_x  # 到根节点中心
            root_edge.to_y = y - BSTAdapter.NODE_RADIUS  # 到根节点顶部
            snapshot.edges.append(root_edge)
        
        # 处理插入节点动画
        elif animation_state == 'inserting':
            new_value = getattr(bst, '_new_value', None)
            parent_value = getattr(bst, '_parent_value', None)
            insert_position = getattr(bst, '_insert_position', None)
            
            if new_value is not None and parent_value is not None:
                # 找到父节点位置
                parent_node = bst.find_node_by_value(parent_value)
                if parent_node and parent_node in positions:
                    # 计算父节点的实际位置
                    parent_x, parent_y = positions[parent_node]
                    
                    # 计算目标位置（子节点位置）
                    if insert_position == 'left':
                        target_x = parent_x - 100
                    else:  # right
                        target_x = parent_x + 100
                    target_y = parent_y + level_height
                    
                    # 计算起始位置（屏幕正上方）
                    start_x_pos = target_x
                    start_y_pos = 50  # 屏幕正上方
                    
                    # 使用线性插值计算当前位置
                    current_x = start_x_pos + (target_x - start_x_pos) * animation_progress
                    current_y = start_y_pos + (target_y - start_y_pos) * animation_progress
                    
                    # 创建动画中的新节点
                    node_snapshot = NodeSnapshot(
                        id="animating_insert",
                        value=str(new_value),
                        x=current_x,
                        y=current_y,
                        node_type="circle",
                        width=BSTAdapter.NODE_DIAMETER,
                        height=BSTAdapter.NODE_DIAMETER,
                        color="#FF6B6B"
                    )
                    snapshot.nodes.append(node_snapshot)
        
        # 处理查找动画提示信息
        if animation_state == 'searching':
            search_value = getattr(bst, '_search_value', None)
            current_node_value = getattr(bst, '_current_search_node_value', None)
            comparison_result = getattr(bst, '_comparison_result', None)
            
            if search_value is not None and current_node_value is not None and comparison_result is not None:
                # 找到当前比较的节点位置
                current_node = bst.find_node_by_value(current_node_value)
                if current_node and current_node in positions:
                    current_x, current_y = positions[current_node]
                    
                    # 创建比较信息提示框
                    if comparison_result == 'less':
                        hint_text = f"{search_value} < {current_node_value} → 左"
                        hint_color = "#FFD700"  # 黄色
                    elif comparison_result == 'greater':
                        hint_text = f"{search_value} > {current_node_value} → 右"
                        hint_color = "#FFD700"  # 黄色
                    else:  # equal
                        hint_text = f"{search_value} = {current_node_value} ✓"
                        hint_color = "#00FF00"  # 绿色
                    
                    # 在节点上方显示提示信息
                    hint_box = BoxSnapshot(
                        id="search_hint",
                        value=hint_text,
                        x=current_x - 60,
                        y=current_y - 60,
                        width=120,
                        height=30,
                        color=hint_color
                    )
                    snapshot.boxes.append(hint_box)
        
        elif animation_state == 'search_found':
            search_value = getattr(bst, '_search_value', None)
            found_node_value = getattr(bst, '_search_result_node_value', None)
            
            if search_value is not None and found_node_value is not None:
                # 找到目标节点位置
                found_node = bst.find_node_by_value(found_node_value)
                if found_node and found_node in positions:
                    found_x, found_y = positions[found_node]
                    
                    # 在节点下方显示成功信息
                    success_box = BoxSnapshot(
                        id="search_success",
                        value=f"找到 {search_value}!",
                        x=found_x - 40,
                        y=found_y + 30,
                        width=80,
                        height=25,
                        color="#00FF00"  # 绿色
                    )
                    snapshot.boxes.append(success_box)
        
        elif animation_state == 'search_not_found':
            search_value = getattr(bst, '_search_value', None)
            last_node_value = getattr(bst, '_last_search_node_value', None)
            
            if search_value is not None and last_node_value is not None:
                # 找到最后搜索的节点位置
                last_node = bst.find_node_by_value(last_node_value)
                if last_node and last_node in positions:
                    last_x, last_y = positions[last_node]
                    
                    # 在节点下方显示未找到信息
                    not_found_box = BoxSnapshot(
                        id="search_not_found",
                        value=f"未找到 {search_value}",
                        x=last_x - 50,
                        y=last_y + 30,
                        width=100,
                        height=25,
                        color="#FFA500"  # 橙色
                    )
                    snapshot.boxes.append(not_found_box)
        
        return snapshot
    
    @staticmethod
    def _get_delete_step_details(bst, progress):
        """生成删除动画的步骤说明"""
        details = []
        delete_value = getattr(bst, '_delete_value', None)
        current_node = getattr(bst, '_current_search_node_value', None)
        comparison_result = getattr(bst, '_delete_comparison_result', None)
        delete_case = getattr(bst, '_delete_case', None)
        target_node = getattr(bst, '_delete_target_node', None)
        replacement_node = getattr(bst, '_delete_replacement_node', None)
        
        if not delete_value:
            return details
        
        if comparison_result == 'less':
            details = [
                f"删除值 {delete_value} < 当前节点 {current_node}",
                "→ 继续在左子树中查找",
                f"进度: {int(progress * 100)}%"
            ]
        elif comparison_result == 'greater':
            details = [
                f"删除值 {delete_value} > 当前节点 {current_node}",
                "→ 继续在右子树中查找",
                f"进度: {int(progress * 100)}%"
            ]
        elif comparison_result == 'equal':
            details = [
                f"找到要删除的节点: {target_node}",
                f"分析删除情况: {delete_case}",
                f"进度: {int(progress * 100)}%"
            ]
            
            if delete_case == 'no_children':
                details.extend([
                    "• 该节点没有子节点",
                    "• 直接删除即可"
                ])
            elif delete_case == 'one_child':
                details.extend([
                    "• 该节点有一个子节点",
                    "• 用子节点替换该节点"
                ])
            elif delete_case == 'two_children':
                details.extend([
                    "• 该节点有两个子节点",
                    f"• 找到右子树最小值: {replacement_node}",
                    "• 用最小值替换该节点",
                    "• 删除原最小值节点"
                ])
        
        return details

class HuffmanTreeAdapter:
    """哈夫曼树适配器 - 支持构建动画"""
    
    @staticmethod
    def _append_circle_node(
        snapshot: StructureSnapshot,
        node_id: str,
        freq,
        x: float,
        y: float,
        label: str,
        color: str = "#1f4e79",
        text_color: str = "#FF3333",
        sub_label_color: str = "#1f4e79",
        scale: float = 1.0,
    ) -> NodeSnapshot:
        """创建并添加圆形节点，数值在圆内，标签显示在圆下方"""
        try:
            freq_value = int(freq)
        except (ValueError, TypeError):
            freq_value = freq
        diameter = max(20, int(72 * scale))
        node_snapshot = NodeSnapshot(
            id=node_id,
            value=str(freq_value),
            x=x,
            y=y,
            node_type="circle",
            width=diameter,
            height=diameter,
            color=color,
            text_color=text_color,
            sub_label=label,
            sub_label_color=sub_label_color,
        )
        node_snapshot.border_color = "#0B1D40"
        node_snapshot.border_width = 3
        snapshot.nodes.append(node_snapshot)
        return node_snapshot
    
    @staticmethod
    def to_snapshot(huffman, start_x=100, y=220, spacing=130,
                    merge_cx=600, merge_cy=180,
                    box_w=90, box_h=46) -> StructureSnapshot:
        """将哈夫曼树转换为快照 - 横向队列布局 + 合并动画"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = "哈夫曼树（横向队列 + 合并动画）"
        
        # 取动画状态
        state = getattr(huffman, '_animation_state', None)
        progress = getattr(huffman, '_animation_progress', 0.0)
        current_merge = getattr(huffman, '_current_merge_nodes', []) or []
        merged_nodes = set(getattr(huffman, '_merged_nodes', []) or [])
        highlight_nodes = getattr(huffman, '_highlight_nodes', []) or []
        
        # 取队列（优先用 queue/_queue；否则用 leaves 兜底）
        queue = None
        for name in ('queue', '_queue', '_current_queue'):
            if hasattr(huffman, name):
                q = getattr(huffman, name)
                if q:
                    queue = list(q)
                    break
        
        if queue is None:
            leaves = []
            if hasattr(huffman, 'leaves') and huffman.leaves:
                leaves = list(huffman.leaves)
            elif hasattr(huffman, 'get_leaves'):
                try:
                    leaves = list(huffman.get_leaves())
                except Exception:
                    leaves = []
            if leaves:
                queue = leaves
        
        if not queue:
            snapshot.hint_text = "哈夫曼树：请输入频率映射并开始构建"
            return snapshot
        
        # 辅助：获取 id、字符与频率、是否子树
        def get_char(item):
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                return str(item[0])
            return getattr(item, 'char', None)
        
        def get_freq(item):
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                return item[1]
            return getattr(item, 'freq', 0)
        
        def is_tree(item):
            return hasattr(item, 'left') or hasattr(item, 'right')
        
        def item_id(item):
            ch = get_char(item)
            if ch not in (None, "", "*"):
                return f"leaf_{ch}"
            return f"node_{id(item)}"
        
        base_blue = "#1f4e79"

        # 选中集合（当前合并或高亮的两项，可能是叶子也可能是子树）
        def add_selected(items, bucket: set):
            for it in items:
                if isinstance(it, (tuple, list)) or hasattr(it, 'freq'):
                    bucket.add(item_id(it))
                else:
                    bucket.add(f"leaf_{it}")  # 假定字符

        selected_ids = set()
        add_selected(current_merge, selected_ids)
        add_selected(highlight_nodes, selected_ids)
        
        # 队列横向排布
        def queue_pos(i):
            return start_x + i * spacing, y
        
        def draw_circle_node(
            id_key,
            freq,
            label,
            x,
            yy,
            color=None,
            text_color="#FFFFFF",
            sub_label_color="#1f4e79",
            scale=1.0,
        ):
            return HuffmanTreeAdapter._append_circle_node(
                snapshot,
                f"hf_{id_key}",
                freq,
                x,
                yy,
                label or "*",
                color=color or "#1f4e79",
                text_color=text_color,
                sub_label_color=sub_label_color,
                scale=scale,
            )
        
        # 画折线模拟弧线（p->mid->q）
        def draw_arc(x1, y1, x2, y2, color="#2E86AB", lift=60):
            mid_x = (x1 + x2) / 2
            mid_y = min(y1, y2) - abs(lift)
            e1 = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
            e1.from_x, e1.from_y = x1, y1
            e1.to_x,   e1.to_y   = mid_x, mid_y
            e1.color = color
            snapshot.edges.append(e1)
            e2 = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
            e2.from_x, e2.from_y = mid_x, mid_y
            e2.to_x,   e2.to_y   = x2, y2
            e2.color = color
            snapshot.edges.append(e2)
        
        # 为子树分配紧凑坐标（中序+层级）
        def assign_positions_compact(node):
            positions = {}  # node -> (xIndex, level)
            x_counter = 0
            def dfs(nd, lv):
                nonlocal x_counter
                if not nd:
                    return
                dfs(getattr(nd, 'left', None), lv+1)
                positions[nd] = (x_counter, lv)
                x_counter += 1
                dfs(getattr(nd, 'right', None), lv+1)
            dfs(node, 0)
            return positions
        
        # 将一棵子树以紧凑树形绘制在 (cx, cy) 附近（小比例）
        def draw_compact_tree(node, cx, cy, scale=0.8, x_step=44, y_step=50):
            if not node:
                return
            pos = assign_positions_compact(node)
            # 计算像素点
            def pix(nd):
                xi, lv = pos[nd]
                x = cx + int((xi - len(pos)/2) * x_step * scale)
                y = cy + int(lv * y_step * scale)
                return x, y
            # 先画边
            for nd in pos.keys():
                x0, y0 = pix(nd)
                if getattr(nd, 'left', None):
                    xl, yl = pix(nd.left)
                    e = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    e.from_x, e.from_y = x0, y0
                    e.to_x,   e.to_y   = xl, yl
                    e.color = "#2E86AB"
                    snapshot.edges.append(e)
                if getattr(nd, 'right', None):
                    xr, yr = pix(nd.right)
                    e = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    e.from_x, e.from_y = x0, y0
                    e.to_x,   e.to_y   = xr, yr
                    e.color = "#2E86AB"
                    snapshot.edges.append(e)
            for nd in pos.keys():
                x0, y0 = pix(nd)
                nid = f"mini_{id(nd)}"
                val = getattr(nd, 'char', None) or "*"
                freq = getattr(nd, 'freq', 0)
                # 叶子节点=黄色字体，内部节点=白色字体
                node_text_color = "#FFD700" if getattr(nd, 'char', None) else "#FFFFFF"
                HuffmanTreeAdapter._append_circle_node(
                    snapshot,
                    f"{nid}_node",
                    freq,
                    x0,
                    y0,
                    val,
                    color="#1f4e79",
                    text_color=node_text_color,
                    scale=0.6 * scale,
                )
        
        def lerp(a, b, t):
            return a + (b - a) * t
        
        # 预计算队列排布
        layout = []  # [(it, id, label, freq, qx, qy), ...]
        layout_by_id = {}
        for i, it in enumerate(queue):
            iid = item_id(it)
            ch = get_char(it)
            freq = get_freq(it)
            label = ch if ch not in (None, "", "*") else "*"
            qx, qy = queue_pos(i)
            entry = (it, iid, label, freq, qx, qy)
            layout.append(entry)
            layout_by_id[iid] = entry
        
        # 找到被选中两项（按频率排序，决定回队列的中间位置）
        selected = [t for t in layout if t[1] in selected_ids]
        selected = sorted(selected, key=lambda x: x[3])[:2] if selected else []

        highlight_selected = []
        if state == "huffman_highlight" and highlight_nodes:
            used_ids = set()
            for node in highlight_nodes:
                entry = None
                try:
                    nid = item_id(node)
                    entry = layout_by_id.get(nid)
                except Exception:
                    entry = None
                if not entry:
                    node_label = get_char(node) or "*"
                    node_freq = get_freq(node)
                    for candidate in layout:
                        if candidate[1] in used_ids:
                            continue
                        _, _, cand_label, cand_freq, _, _ = candidate
                        if cand_label == node_label and cand_freq == node_freq:
                            entry = candidate
                            break
                if entry:
                    highlight_selected.append(entry)
                    used_ids.add(entry[1])
            selected = highlight_selected[:2] if highlight_selected else selected
        
        # 默认回队列位置：两者中点
        mid_x = None
        if len(selected) == 2:
            ax0, ay0 = selected[0][4], selected[0][5]
            bx0, by0 = selected[1][4], selected[1][5]
            mid_x = (ax0 + bx0) / 2
        
        # 1) 先画队列中所有未选中的项
        for it, iid, label, freq, qx, qy in layout:
            if iid in selected_ids:
                continue
            # 被合并过的旧项（如果结构标记了 merged_nodes）显示淡灰
            if is_tree(it):
                # 子树以紧凑树形显示
                draw_compact_tree(it, qx, qy - 6, scale=0.85)
            else:
                if hasattr(huffman, '_merged_nodes') and iid in merged_nodes:
                    draw_circle_node(iid, freq, label, qx, qy, color="#3A3A3A", text_color="#C0C0C0")
                else:
                    # 叶子节点=黄色字体，内部节点=白色字体
                    item_char = get_char(it)
                    node_text_color = "#FFD700" if item_char and item_char not in (None, "", "*") else "#FFFFFF"
                    draw_circle_node(iid, freq, label, qx, qy, text_color=node_text_color)
        
        # 2) 对被选中两项做动画
        if len(selected) == 2:
            if state == "huffman_highlight":
                highlight_color = "#FF4C4C"
                for it, iid, label, freq, qx, qy in selected:
                    if is_tree(it):
                        draw_compact_tree(it, qx, qy - 6, scale=0.85)
                    else:
                        char_val = get_char(it)
                        text_color = "#FFD700" if char_val and char_val not in (None, "", "*") else "#FFFFFF"
                        draw_circle_node(iid, freq, label, qx, qy, color=highlight_color, text_color=text_color)
                if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                    snapshot.step_details = []
                snapshot.step_details.append("选中最小两个节点（红色填充 2 秒）")
            else:
                (itA, idA, labelA, freqA, ax0, ay0), (itB, idB, labelB, freqB, bx0, by0) = selected
                
                # 0.00–0.20 高亮队列中的两个
                if progress < 0.20:
                    # A
                    if is_tree(itA):
                        draw_compact_tree(itA, ax0, ay0 - 6, scale=0.85)
                    else:
                        charA = get_char(itA)
                        text_colorA = "#FFD700" if charA and charA not in (None, "", "*") else "#FFFFFF"
                        draw_circle_node(idA, freqA, labelA, ax0, ay0, color=base_blue, text_color=text_colorA)
                    # B
                    if is_tree(itB):
                        draw_compact_tree(itB, bx0, by0 - 6, scale=0.85)
                    else:
                        charB = get_char(itB)
                        text_colorB = "#FFD700" if charB and charB not in (None, "", "*") else "#FFFFFF"
                        draw_circle_node(idB, freqB, labelB, bx0, by0, color=base_blue, text_color=text_colorB)
                    if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                        snapshot.step_details = []
                    snapshot.step_details.append("选择最小两个节点（高亮）")
                
                # 0.20–0.45 漂移到合并区
                elif progress < 0.45:
                    t = (progress - 0.20) / 0.25
                    ax = lerp(ax0, merge_cx - 70, t); ay = lerp(ay0, merge_cy, t)
                    bx = lerp(bx0, merge_cx + 70, t); by = lerp(by0, merge_cy, t)
                    # A
                    if is_tree(itA):
                        draw_compact_tree(itA, ax, ay, scale=0.9)
                    else:
                        charA = get_char(itA)
                        text_colorA = "#FFD700" if charA and charA not in (None, "", "*") else "#FFFFFF"
                        draw_circle_node(idA, freqA, labelA, ax, ay, color=base_blue, text_color=text_colorA)
                    # B
                    if is_tree(itB):
                        draw_compact_tree(itB, bx, by, scale=0.9)
                    else:
                        charB = get_char(itB)
                        text_colorB = "#FFD700" if charB and charB not in (None, "", "*") else "#FFFFFF"
                        draw_circle_node(idB, freqB, labelB, bx, by, color=base_blue, text_color=text_colorB)
                    if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                        snapshot.step_details = []
                    snapshot.step_details.append("漂移到合并区域")
                
                # 0.45–0.60 融合 + 父节点出现（绿色）+ 父→子连线
                elif progress < 0.60:
                    t = (progress - 0.45) / 0.15
                    ax = merge_cx - 70; ay = merge_cy
                    bx = merge_cx + 70; by = merge_cy
                    scale = max(0.5, 1.0 - 0.6 * t)
                    # 两子树在中心缩小
                    if is_tree(itA):
                        draw_compact_tree(itA, ax, ay, scale=scale)
                    else:
                        charA = get_char(itA)
                        text_colorA = "#FFD700" if charA and charA not in (None, "", "*") else "#FFFFFF"
                        draw_circle_node(idA, freqA, labelA, ax, ay, color=base_blue, text_color=text_colorA, scale=scale)
                    if is_tree(itB):
                        draw_compact_tree(itB, bx, by, scale=scale)
                    else:
                        charB = get_char(itB)
                        text_colorB = "#FFD700" if charB and charB not in (None, "", "*") else "#FFFFFF"
                        draw_circle_node(idB, freqB, labelB, bx, by, color=base_blue, text_color=text_colorB, scale=scale)
                    
                    # 父节点（仅渲染用）
                    try:
                        pfreq = (int(freqA) if str(freqA).isdigit() else freqA) + \
                                (int(freqB) if str(freqB).isdigit() else freqB)
                    except (ValueError, TypeError):
                        pfreq = freqA + freqB
                    # 父->子连线（连接到两棵子树的根）
                    # 父节点是新生成的内部节点，使用白色字体
                    draw_circle_node("par_tmp", pfreq, "*", merge_cx, merge_cy, color="#1f4e79", text_color="#FFFFFF")
                    # 父→A根
                    eL = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    eL.from_x, eL.from_y = merge_cx, merge_cy
                    eL.to_x,   eL.to_y   = ax, ay
                    eL.color = "#2E86AB"
                    snapshot.edges.append(eL)
                    # 父→B根
                    eR = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    eR.from_x, eR.from_y = merge_cx, merge_cy
                    eR.to_x,   eR.to_y   = bx, by
                    eR.color = "#2E86AB"
                    snapshot.edges.append(eR)
                    
                    if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                        snapshot.step_details = []
                    snapshot.step_details.append("融合生成新节点")
                
                # 0.60–0.80 父节点回到队列中点，旧两项淡出
                elif progress < 0.80:
                    t = (progress - 0.60) / 0.20
                    # 父节点作为"新树根"回队列中点
                    offset_x = 180
                    offset_y = 120
                    rx = lerp(merge_cx + offset_x, mid_x if mid_x is not None else merge_cx, t)
                    ry = lerp(merge_cy + offset_y, y, t)
                    # 将两棵子树作为左右孩子临时绘制成一棵新小树（仅渲染不改结构）
                    class _Pair(object):
                        pass
                    parent = _Pair()
                    parent.char = "*"
                    try:
                        parent.freq = (int(freqA) if str(freqA).isdigit() else freqA) + \
                                      (int(freqB) if str(freqB).isdigit() else freqB)
                    except (ValueError, TypeError):
                        parent.freq = freqA + freqB
                    parent.left = itA
                    parent.right = itB
                    draw_compact_tree(parent, rx, ry, scale=0.9)
                    
                    # 旧位置两项可淡灰（历史痕迹）
                    if not is_tree(itA):
                        draw_circle_node(idA, freqA, labelA, ax0, ay0, color="#3a3a3a", text_color="#c0c0c0", sub_label_color="#c0c0c0")
                    if not is_tree(itB):
                        draw_circle_node(idB, freqB, labelB, bx0, by0, color="#3a3a3a", text_color="#c0c0c0", sub_label_color="#c0c0c0")
                    
                    if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                        snapshot.step_details = []
                    snapshot.step_details.append("新节点回到队列")
                
                # 0.80–1.00 等下一轮（队列静态，父节点已就位）
                else:
                    if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                        snapshot.step_details = []
                    snapshot.step_details.append("等待下一轮合并")
        
        # 禁用：接近完成时在右侧绘制整棵树
        
        # 操作历史
        if hasattr(huffman, '_operation_history') and huffman._operation_history:
            snapshot.operation_history = list(huffman._operation_history)
        
        return snapshot
    
    @staticmethod
    def _draw_final_tree(node, snapshot, x, yy, dx=150, dy=80, root_node=None):
        """绘制最终树结构"""
        if not node:
            return
        
        # 第一次调用时，root_node 就是传入的 node
        if root_node is None:
            root_node = node
        
        nid = f"t_{id(node)}"
        val = getattr(node, 'char', None) or "*"
        freq = getattr(node, 'freq', 0)
        fill_color = "#90EE90" if node == root_node else "#1f4e79"
        # 根据节点类型设置字体颜色：叶子=黄色，内部=白色
        node_char = getattr(node, 'char', None)
        if node == root_node:
            text_color = "#1f4e79"  # 根节点特殊颜色
        else:
            text_color = "#FFD700" if node_char else "#FFFFFF"
        HuffmanTreeAdapter._append_circle_node(
            snapshot,
            f"{nid}_node",
            freq,
            x,
            yy,
            val,
            color=fill_color,
            text_color=text_color,
            sub_label_color="#1f4e79"
        )
        
        if getattr(node, 'left', None):
            lx, ly = x - dx, yy + dy
            e = EdgeSnapshot(from_id=f"{nid}_node", to_id=f"t_{id(node.left)}_node", arrow_type="arrow")
            e.from_x, e.from_y = x, yy; e.to_x, e.to_y = lx, ly; e.color = "#2E86AB"
            snapshot.edges.append(e)
            HuffmanTreeAdapter._draw_final_tree(node.left, snapshot, lx, ly, dx=int(dx*0.75), dy=dy, root_node=root_node)
        
        if getattr(node, 'right', None):
            rx, ry = x + dx, yy + dy
            e = EdgeSnapshot(from_id=f"{nid}_node", to_id=f"t_{id(node.right)}_node", arrow_type="arrow")
            e.from_x, e.from_y = x, yy; e.to_x, e.to_y = rx, ry; e.color = "#2E86AB"
            snapshot.edges.append(e)
            HuffmanTreeAdapter._draw_final_tree(node.right, snapshot, rx, ry, dx=int(dx*0.75), dy=dy, root_node=root_node)
    
    @staticmethod
    def _create_building_animation_snapshot(huffman_tree, freq_map, build_step, progress, start_x, y, level_height):
        """创建构建动画快照"""
        snapshot = StructureSnapshot()
        
        # 根据构建步骤显示不同的提示信息
        total_nodes = len(freq_map)
        current_round = getattr(huffman_tree, '_current_round', 0)
        total_rounds = getattr(huffman_tree, '_total_rounds', total_nodes - 1)
        
        # 生成详细的步骤说明
        step_details = HuffmanTreeAdapter._get_step_details(
            build_step, current_round, total_rounds, total_nodes, freq_map, progress
        )
        
        snapshot.hint_text = step_details['main_text']
        snapshot.step_details = step_details['details']  # 添加详细步骤说明
        
        # 添加操作历史记录
        snapshot.operation_history = HuffmanTreeAdapter._get_operation_history(
            huffman_tree, current_round, total_rounds, build_step, progress
        )
        
        freq_signature = tuple(sorted(freq_map.items()))
        if not freq_signature:
            setattr(huffman_tree, "_last_tree_snapshot", None)
            setattr(huffman_tree, "_last_tree_signature", None)
        cached_tree = getattr(huffman_tree, "_last_tree_snapshot", None)
        cached_signature = getattr(huffman_tree, "_last_tree_signature", None)

        # 在屏幕上方显示队列中的节点/子树（水平排列）
        top_start_x = 100
        top_y = y - 100
        
        # 确保所有频率值都是整数，添加错误处理
        safe_freq_map = {}
        for k, v in freq_map.items():
            try:
                safe_freq_map[k] = int(v)
            except (ValueError, TypeError):
                print(f"警告: 无法转换频率值 '{v}' 为整数，跳过字符 '{k}'")
                continue
        freq_map = safe_freq_map
        sorted_items = sorted(freq_map.items(), key=lambda x: int(x[1]))
        
        # 在新的选择阶段（build_step==0）显示缓存的已建树
        if build_step == 0 and cached_tree and cached_signature == freq_signature:
            snapshot.nodes.extend(copy.deepcopy(cached_tree.get("nodes", [])))
            snapshot.edges.extend(copy.deepcopy(cached_tree.get("edges", [])))

        # 获取当前队列状态
        if hasattr(huffman_tree, '_current_queue') and hasattr(huffman_tree, '_queue_trees'):
            current_queue = huffman_tree._current_queue
            queue_trees = huffman_tree._queue_trees
        else:
            # 回退到原始频率映射
            current_queue = [(char, freq) for char, freq in sorted_items]
            queue_trees = [Node(char, freq) for char, freq in sorted_items]
        
        # 根据队列元素数量调整间距
        total_items = len(current_queue)
        if total_items <= 3:
            node_spacing = 120
        elif total_items <= 6:
            node_spacing = 100
        else:
            node_spacing = 80
        
        # 显示队列中的所有元素（水平排列）
        for i, ((char, freq), tree) in enumerate(zip(current_queue, queue_trees)):
            node_x = top_start_x + i * node_spacing
            node_y = top_y
            
            # 检查是否是当前步骤被选中的节点
            is_selected = HuffmanTreeAdapter._is_node_selected_in_step(i, build_step, sorted_items)
            is_moving = HuffmanTreeAdapter._is_node_moving_in_step(i, build_step, progress)
            is_merging = HuffmanTreeAdapter._is_node_merging_in_step(i, build_step, progress)
            is_returning = HuffmanTreeAdapter._is_node_returning_in_step(i, build_step, progress)
            
            base_blue = "#1f4e79"
            highlight_green = "#2ECC71"

            if is_merging:
                # 节点正在合并
                target_x = start_x  # 合并区域
                target_y = y + 200
                current_x = target_x
                current_y = target_y
                color = highlight_green
                scale = 0.8 + 0.4 * progress  # 逐渐变大
            elif is_moving:
                # 节点正在移动
                target_x = start_x  # 合并区域
                target_y = y + 200
                current_x = node_x + (target_x - node_x) * progress
                current_y = node_y + (target_y - node_y) * progress
                color = highlight_green
                scale = 1.2
            elif is_returning:
                # 节点正在返回
                target_x = top_start_x + i * node_spacing
                target_y = top_y
                current_x = start_x + (target_x - start_x) * progress
                current_y = y + 200 + (target_y - (y + 200)) * progress
                color = highlight_green
                scale = 1.1
            elif build_step >= 2 and i < 2:
                # 已合并的节点淡出
                fade_alpha = max(0.1, 1.0 - (build_step - 2) * 0.5)
                color = f"rgba(31, 78, 121, {fade_alpha})"  # 淡出效果
                scale = 0.8
            elif is_selected:
                # 被选中的节点
                color = highlight_green
                scale = 1.1
            else:
                # 普通节点
                color = base_blue
                scale = 1.0
            
            # 确定最终位置
            final_x = current_x if (is_moving or is_merging or is_returning) else node_x
            final_y = current_y if (is_moving or is_merging or is_returning) else node_y
            
            char_label = tree.char if tree.char not in (None, "") else "*"
            # 根据节点类型设置字体颜色：叶子=黄色，内部=白色
            node_text_color = "#FFD700" if tree.char else "#FFFFFF"
            parent_node = HuffmanTreeAdapter._append_circle_node(
                snapshot,
                f"queue_{id(tree)}",
                freq,
                final_x,
                final_y,
                char_label,
                color=color,
                text_color=node_text_color,
                scale=scale,
            )
            
            # 如果是子树且不在移动/合并/返回状态，显示子树结构
            # 当显示子树结构时使用字母，数值来自子树
            if tree.char is None and not (is_moving or is_merging or is_returning):
                HuffmanTreeAdapter._add_subtree_visualization(
                    tree,
                    snapshot,
                    final_x,
                    final_y,
                    node_spacing,
                    parent_id=parent_node.id,
                )
            
            # 移除移动路径指示线（黄色线）
        
        # 显示合并区域
        merge_box = BoxSnapshot(
            id="merge_area",
            value="合并区域",
            x=start_x - 50,
            y=y + 150,
            width=100,
            height=100,
            color="#E0E0E0"
        )
        snapshot.boxes.append(merge_box)
        
        # 显示合并后的新节点
        if build_step >= 2:
            # 计算合并后的频率
            if len(sorted_items) >= 2:
                merged_freq = sorted_items[0][1] + sorted_items[1][1]
                merged_char = f"{sorted_items[0][0]}{sorted_items[1][0]}"
                
                # 在合并区域显示新节点
                new_node_x = start_x
                new_node_y = y + 200
                
                if build_step == 2:
                    # 合并阶段：节点在合并区域
                    scale = 0.5 + 0.5 * progress
                    color = "#00FF00"  # 绿色表示新节点
                elif build_step == 3:
                    # 返回阶段：节点正在返回上方
                    target_x = top_start_x
                    target_y = top_y
                    new_node_x = start_x + (target_x - start_x) * progress
                    new_node_y = y + 200 + (target_y - (y + 200)) * progress
                    scale = 1.0
                    color = "#00FF00"
                else:
                    # 完成阶段：节点在上方
                    new_node_x = top_start_x
                    new_node_y = top_y
                    scale = 1.0
                    color = "#00FF00"
                
                # 合并后的新节点是内部节点，使用白色字体
                HuffmanTreeAdapter._append_circle_node(
                    snapshot,
                    "merged_node",
                    merged_freq,
                    new_node_x,
                    new_node_y,
                    merged_char or "*",
                    color=color,
                    text_color="#FFFFFF",
                    scale=scale,
                )
        
        # 显示已构建的树结构
        if build_step > 0:
            HuffmanTreeAdapter._add_built_tree_nodes(huffman_tree, snapshot, start_x + 200, y, level_height, build_step, progress)
            built_nodes = [
                copy.deepcopy(node)
                for node in snapshot.nodes
                if isinstance(node.id, str) and node.id.startswith("tree_node_")
            ]
            built_edges = [
                copy.deepcopy(edge)
                for edge in snapshot.edges
                if (
                    (isinstance(getattr(edge, "from_id", ""), str) and getattr(edge, "from_id").startswith("tree_node_"))
                    or (isinstance(getattr(edge, "to_id", ""), str) and getattr(edge, "to_id").startswith("tree_node_"))
                )
            ]
            if built_nodes or built_edges:
                setattr(huffman_tree, "_last_tree_snapshot", {"nodes": built_nodes, "edges": built_edges})
                setattr(huffman_tree, "_last_tree_signature", freq_signature)
        
        return snapshot
    
    @staticmethod
    def _get_step_details(build_step, current_round, total_rounds, total_nodes, freq_map, progress):
        """生成详细的步骤说明"""
        details = []
        
        # 确保所有频率值都是整数，添加错误处理
        safe_freq_map = {}
        for k, v in freq_map.items():
            try:
                safe_freq_map[k] = int(v)
            except (ValueError, TypeError):
                print(f"警告: 无法转换频率值 '{v}' 为整数，跳过字符 '{k}'")
                continue
        freq_map = safe_freq_map
        sorted_items = sorted(freq_map.items(), key=lambda x: int(x[1]))
        
        if build_step == 0:
            # 选择最小权值的两个节点
            if len(sorted_items) >= 2:
                min1_char, min1_freq = sorted_items[0]
                min2_char, min2_freq = sorted_items[1]
                details = [
                    f"第{current_round + 1}轮 - 步骤1: 选择最小权值的两个节点",
                    f"• 找到最小权值节点: {min1_char}({min1_freq})",
                    f"• 找到次小权值节点: {min2_char}({min2_freq})",
                    f"• 准备合并这两个节点",
                    f"• 当前队列中还有 {len(sorted_items)} 个节点"
                ]
            main_text = f"哈夫曼树构建中... 第{current_round + 1}轮: 选择最小权值的两个节点"
            
        elif build_step == 1:
            # 节点移动到合并区域
            details = [
                f"第{current_round + 1}轮 - 步骤2: 节点移动到合并区域",
                f"• 将选中的两个最小权值节点移动到合并区域",
                f"• 节点在移动过程中会高亮显示",
                f"• 移动完成后将进行合并操作",
                f"• 进度: {int(progress * 100)}%"
            ]
            main_text = f"哈夫曼树构建中... 第{current_round + 1}轮: 节点移动到合并区域"
            
        elif build_step == 2:
            # 合并节点创建新节点
            if len(sorted_items) >= 2:
                min1_char, min1_freq = sorted_items[0]
                min2_char, min2_freq = sorted_items[1]
                merged_freq = min1_freq + min2_freq
                details = [
                    f"第{current_round + 1}轮 - 步骤3: 合并节点创建新节点",
                    f"• 合并节点: {min1_char}({min1_freq}) + {min2_char}({min2_freq})",
                    f"• 创建新节点: {min1_char}{min2_char}({merged_freq})",
                    f"• 新节点将作为父节点",
                    f"• 原节点成为子节点",
                    f"• 进度: {int(progress * 100)}%"
                ]
            main_text = f"哈夫曼树构建中... 第{current_round + 1}轮: 合并节点创建新节点"
            
        elif build_step == 3:
            # 新节点返回队列
            details = [
                f"第{current_round + 1}轮 - 步骤4: 新节点返回队列",
                f"• 将合并后的新节点放回队列",
                f"• 新节点按权值大小插入到合适位置",
                f"• 准备进行下一轮合并",
                f"• 进度: {int(progress * 100)}%"
            ]
            main_text = f"哈夫曼树构建中... 第{current_round + 1}轮: 新节点返回队列"
            
        else:
            # 完成当前轮次
            details = [
                f"第{current_round + 1}轮 - 步骤5: 完成当前轮次",
                f"• 当前轮次合并完成",
                f"• 队列中剩余节点数: {total_nodes - current_round - 1}",
                f"• 准备开始下一轮合并",
                f"• 总进度: {int((current_round + 1) / total_rounds * 100)}%"
            ]
            main_text = f"哈夫曼树构建中... 第{current_round + 1}轮: 完成当前轮次"
        
        return {
            'main_text': main_text,
            'details': details
        }
    
    @staticmethod
    def _get_operation_history(huffman_tree, current_round, total_rounds, build_step, progress):
        """生成操作历史记录"""
        history = []
        
        # 获取当前状态信息
        freq_map = getattr(huffman_tree, '_original_freq_map', {})
        # 确保所有频率值都是整数，添加错误处理
        safe_freq_map = {}
        for k, v in freq_map.items():
            try:
                safe_freq_map[k] = int(v)
            except (ValueError, TypeError):
                print(f"警告: 无法转换频率值 '{v}' 为整数，跳过字符 '{k}'")
                continue
        freq_map = safe_freq_map
        sorted_items = sorted(freq_map.items(), key=lambda x: int(x[1]))
        
        # 添加初始状态
        history.append("=== 哈夫曼树构建开始 ===")
        history.append(f"初始节点: {[item[1] for item in sorted_items]}")
        history.append("")
        
        # 模拟构建过程，显示所有已完成的轮次
        current_queue = sorted_items.copy()
        queue_trees = [Node(char, freq) for char, freq in sorted_items]
        
        for round_num in range(min(current_round + 1, total_rounds)):
            if len(current_queue) >= 2:
                # 选择最小权值的两个节点
                min1_char, min1_freq = current_queue[0]
                min2_char, min2_freq = current_queue[1]
                history.append(f"第{round_num + 1}轮 - 选择最小权值节点: {min1_freq} 和 {min2_freq}")
                
                # 移动节点
                history.append(f"第{round_num + 1}轮 - 移动节点到合并区域")
                
                # 合并节点
                merged_freq = min1_freq + min2_freq
                history.append(f"第{round_num + 1}轮 - 合并节点: {min1_freq} + {min2_freq} = {merged_freq}")
                
                # 创建新的子树
                new_tree = Node(merged_freq)
                new_tree.left = queue_trees[0]
                new_tree.right = queue_trees[1]
                
                # 新节点返回队列
                history.append(f"第{round_num + 1}轮 - 新子树 {merged_freq} 返回队列")
                
                # 更新队列
                new_queue = [item for item in current_queue[2:]] + [(f"{min1_char}{min2_char}", merged_freq)]
                new_queue.sort(key=lambda x: int(x[1]))
                current_queue = new_queue
                
                # 更新队列中的树结构
                new_trees = queue_trees[2:] + [new_tree]
                new_trees.sort(key=lambda x: int(x.freq))
                queue_trees = new_trees
                
                # 显示队列中的树结构
                tree_info = []
                for i, (item, tree) in enumerate(zip(current_queue, queue_trees)):
                    if tree.char is not None:
                        tree_info.append(f"{item[1]}(叶)")
                    else:
                        tree_info.append(f"{item[1]}(树)")
                
                history.append(f"第{round_num + 1}轮 - 完成，新队列: {tree_info}")
                history.append("")
        
        # 如果构建完成
        if current_round >= total_rounds:
            history.append("=== 哈夫曼树构建完成 ===")
            history.append("所有节点已合并，形成完整的哈夫曼树")
        
        return history
    
    @staticmethod
    def _add_subtree_visualization(tree, snapshot, center_x, center_y, spacing, parent_id=None):
        """添加子树的可视化表示"""
        if tree.char is not None:
            return  # 叶子节点不需要子树可视化
        
        # 计算子树的位置
        left_x = center_x - spacing * 0.3
        right_x = center_x + spacing * 0.3
        child_y = center_y + 40
        
        # 添加子节点
        base_blue = "#1f4e79"
        label_color = "#1f4e79"
        
        if tree.left:
            left_label = tree.left.char or "*"
            # 根据节点类型设置字体颜色：叶子=黄色，内部=白色
            left_text_color = "#FFD700" if tree.left.char else "#FFFFFF"
            left_node = HuffmanTreeAdapter._append_circle_node(
                snapshot,
                f"subtree_left_{id(tree)}",
                tree.left.freq,
                left_x,
                child_y,
                left_label,
                color=base_blue,
                text_color=left_text_color,
                sub_label_color=label_color,
                scale=0.75,
            )
            
            edge = EdgeSnapshot(
                from_id=parent_id or "",
                to_id=left_node.id,
                arrow_type="line"
            )
            edge.from_x = center_x
            edge.from_y = center_y
            edge.to_x = left_x
            edge.to_y = child_y
            edge.color = "#2E86AB"
            snapshot.edges.append(edge)
        
        if tree.right:
            right_label = tree.right.char or "*"
            # 根据节点类型设置字体颜色：叶子=黄色，内部=白色
            right_text_color = "#FFD700" if tree.right.char else "#FFFFFF"
            right_node = HuffmanTreeAdapter._append_circle_node(
                snapshot,
                f"subtree_right_{id(tree)}",
                tree.right.freq,
                right_x,
                child_y,
                right_label,
                color=base_blue,
                text_color=right_text_color,
                sub_label_color=label_color,
                scale=0.75,
            )
            
            edge = EdgeSnapshot(
                from_id=parent_id or "",
                to_id=right_node.id,
                arrow_type="line"
            )
            edge.from_x = center_x
            edge.from_y = center_y
            edge.to_x = right_x
            edge.to_y = child_y
            edge.color = "#2E86AB"
            snapshot.edges.append(edge)
    
    @staticmethod
    def _is_node_selected_in_step(node_index, build_step, sorted_items):
        """检查节点是否在当前步骤被选中"""
        # 每轮合并都选择前两个最小节点
        if build_step == 0:
            return node_index < 2  # 第一步选择前两个最小节点
        elif build_step == 1:
            return node_index < 2  # 第二步继续高亮选中的节点
        return False
    
    @staticmethod
    def _is_node_moving_in_step(node_index, build_step, progress):
        """检查节点是否在当前步骤正在移动"""
        if build_step == 1 and node_index < 2:
            return progress > 0.1 and progress < 0.9
        return False
    
    @staticmethod
    def _is_node_merging_in_step(node_index, build_step, progress):
        """检查节点是否在当前步骤正在合并"""
        if build_step == 2 and node_index < 2:
            return progress > 0.2 and progress < 0.8
        return False
    
    @staticmethod
    def _is_node_returning_in_step(node_index, build_step, progress):
        """检查节点是否在当前步骤正在返回"""
        if build_step == 3 and node_index < 2:
            return progress > 0.1 and progress < 0.9
        return False
    
    @staticmethod
    def _layout_huffman_tree_horizontal(node, center_x, y, level_height=80, node_width=60, min_spacing=100):
        """水平布局哈夫曼树，类似BST的布局算法"""
        if not node:
            return {}
        
        positions = {}
        
        # 当前节点位置
        positions[node] = (center_x, y)
        
        if not node.left and not node.right:
            # 叶子节点，直接返回
            return positions
        
        # 计算左右子树需要的宽度
        left_width = HuffmanTreeAdapter._calculate_subtree_width_horizontal(
            node.left, node_width, min_spacing)
        right_width = HuffmanTreeAdapter._calculate_subtree_width_horizontal(
            node.right, node_width, min_spacing)
        
        # 计算子节点位置
        if node.left and node.right:
            # 两个子节点
            total_child_width = left_width + right_width + min_spacing * 1.5
            left_center = center_x - total_child_width / 2 + left_width / 2
            right_center = center_x + total_child_width / 2 - right_width / 2
            
            # 递归布局子树
            left_positions = HuffmanTreeAdapter._layout_huffman_tree_horizontal(
                node.left, left_center, y + level_height, level_height, node_width, min_spacing)
            right_positions = HuffmanTreeAdapter._layout_huffman_tree_horizontal(
                node.right, right_center, y + level_height, level_height, node_width, min_spacing)
            
            positions.update(left_positions)
            positions.update(right_positions)
            
        elif node.left:
            # 只有左子节点
            left_center = center_x - min_spacing / 2
            left_positions = HuffmanTreeAdapter._layout_huffman_tree_horizontal(
                node.left, left_center, y + level_height, level_height, node_width, min_spacing)
            positions.update(left_positions)
            
        elif node.right:
            # 只有右子节点
            right_center = center_x + min_spacing / 2
            right_positions = HuffmanTreeAdapter._layout_huffman_tree_horizontal(
                node.right, right_center, y + level_height, level_height, node_width, min_spacing)
            positions.update(right_positions)
        
        return positions
    
    @staticmethod
    def _calculate_subtree_width_horizontal(node, node_width=60, min_spacing=100):
        """递归计算子树所需的最小宽度"""
        if not node:
            return 0
        
        if not node.left and not node.right:
            # 叶子节点只需要自身宽度
            return node_width
        
        # 计算左右子树宽度
        left_width = HuffmanTreeAdapter._calculate_subtree_width_horizontal(
            node.left, node_width, min_spacing)
        right_width = HuffmanTreeAdapter._calculate_subtree_width_horizontal(
            node.right, node_width, min_spacing)
        
        # 当前节点需要的总宽度 = max(自身宽度, 左子树宽度 + 右子树宽度 + 间距)
        subtree_total_width = left_width + right_width
        if left_width > 0 and right_width > 0:
            subtree_total_width += min_spacing
        
        return max(node_width, subtree_total_width)
    
    @staticmethod
    def _add_horizontal_tree_edges(node, positions, snapshot):
        """添加水平布局树的边连接"""
        if not node:
            return
        
        node_x, node_y = positions[node]
        node_id = f"final_node_{id(node)}"
        
        # 添加到左子节点的边
        if node.left:
            left_x, left_y = positions[node.left]
            left_id = f"final_node_{id(node.left)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=left_id,
                color="#2E86AB",
                arrow_type="line"
            )
            # 设置连线坐标
            edge.from_x = node_x
            edge.from_y = node_y
            edge.to_x = left_x
            edge.to_y = left_y
            
            # 添加"0"标签
            label_x = (edge.from_x + edge.to_x) / 2
            label_y = (edge.from_y + edge.to_y) / 2
            label = BoxSnapshot(
                id=f"label_0_{id(node)}",
                value="0",
                x=label_x - 10,
                y=label_y - 10,
                width=20,
                height=20,
                color="#FFD700"
            )
            snapshot.boxes.append(label)
            
            snapshot.edges.append(edge)
            
            # 递归处理左子树
            HuffmanTreeAdapter._add_horizontal_tree_edges(node.left, positions, snapshot)
        
        # 添加到右子节点的边
        if node.right:
            right_x, right_y = positions[node.right]
            right_id = f"final_node_{id(node.right)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=right_id,
                color="#2E86AB",
                arrow_type="line"
            )
            # 设置连线坐标
            edge.from_x = node_x
            edge.from_y = node_y
            edge.to_x = right_x
            edge.to_y = right_y
            
            # 添加"1"标签
            label_x = (edge.from_x + edge.to_x) / 2
            label_y = (edge.from_y + edge.to_y) / 2
            label = BoxSnapshot(
                id=f"label_1_{id(node)}",
                value="1",
                x=label_x - 10,
                y=label_y - 10,
                width=20,
                height=20,
                color="#FFD700"
            )
            snapshot.boxes.append(label)
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            HuffmanTreeAdapter._add_horizontal_tree_edges(node.right, positions, snapshot)
    
    @staticmethod
    def _add_final_tree_edges(node, snapshot, start_x, y, level_height, level=0):
        """添加最终树的边连接"""
        if not node:
            return
        
        node_id = f"final_node_{id(node)}"
        
        # 添加左子节点边
        if node.left:
            left_id = f"final_node_{id(node.left)}"
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=left_id,
                arrow_type="line"
            )
            
            # 计算边的位置
            level_width = 200 * (2 ** level)
            edge.from_x = start_x
            edge.from_y = y + level * level_height
            edge.to_x = start_x - level_width/2
            edge.to_y = y + (level + 1) * level_height
            edge.color = "#4C78A8"
            
            # 添加"0"标签
            label_x = (edge.from_x + edge.to_x) / 2
            label_y = (edge.from_y + edge.to_y) / 2
            label = BoxSnapshot(
                id=f"label_0_{id(node)}",
                value="0",
                x=label_x - 10,
                y=label_y - 10,
                width=20,
                height=20,
                color="#FFD700"
            )
            snapshot.boxes.append(label)
            
            snapshot.edges.append(edge)
            
            # 递归处理左子树
            HuffmanTreeAdapter._add_final_tree_edges(node.left, snapshot, start_x - level_width/2, y, level_height, level + 1)
        
        # 添加右子节点边
        if node.right:
            right_id = f"final_node_{id(node.right)}"
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=right_id,
                arrow_type="line"
            )
            
            # 计算边的位置
            level_width = 200 * (2 ** level)
            edge.from_x = start_x
            edge.from_y = y + level * level_height
            edge.to_x = start_x + level_width/2
            edge.to_y = y + (level + 1) * level_height
            edge.color = "#4C78A8"
            
            # 添加"1"标签
            label_x = (edge.from_x + edge.to_x) / 2
            label_y = (edge.from_y + edge.to_y) / 2
            label = BoxSnapshot(
                id=f"label_1_{id(node)}",
                value="1",
                x=label_x - 10,
                y=label_y - 10,
                width=20,
                height=20,
                color="#FFD700"
            )
            snapshot.boxes.append(label)
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            HuffmanTreeAdapter._add_final_tree_edges(node.right, snapshot, start_x + level_width/2, y, level_height, level + 1)
    
    @staticmethod
    def _add_built_tree_nodes(huffman_tree, snapshot, start_x, y, level_height, build_step, progress):
        """添加已构建的树节点"""
        if not huffman_tree.root:
            return
        
        # 使用层序遍历显示已构建的节点
        queue = [(huffman_tree.root, start_x, y)]
        level = 0
        
        while queue and level < build_step + 1:
            next_queue = []
            level_width = 200 * (2 ** level)
            
            for i, (node, x, current_y) in enumerate(queue):
                node_id = f"tree_node_{id(node)}"
                
                # 计算节点位置
                if len(queue) > 1:
                    node_x = x - level_width/2 + i * (level_width / (len(queue) - 1))
                else:
                    node_x = x
                
                # 动画效果
                if level == build_step:
                    # 当前步骤的节点有动画效果
                    target_y = current_y
                    start_y = y + 200
                    node_y = start_y + (target_y - start_y) * progress
                    scale = 0.5 + 0.5 * progress
                else:
                    node_y = current_y
                    scale = 1.0
                
                label_text = node.char or "*"
                node_color = "#1f4e79"
                # 根据节点类型设置字体颜色：叶子=黄色，内部=白色
                node_text_color = "#FFD700" if node.char else "#FFFFFF"
                HuffmanTreeAdapter._append_circle_node(
                    snapshot,
                    node_id,
                    node.freq,
                    node_x,
                    node_y,
                    label_text,
                    color=node_color,
                    text_color=node_text_color,
                    scale=scale,
                )
                
                # 添加子节点到下一层
                if node.left:
                    next_queue.append((node.left, node_x, current_y + level_height))
                if node.right:
                    next_queue.append((node.right, node_x, current_y + level_height))
            
            queue = next_queue
            level += 1
        
        # 添加边（带动画效果）
        HuffmanTreeAdapter._add_animated_edges(huffman_tree.root, snapshot, start_x, y, level_height, build_step, progress)
    
    @staticmethod
    def _add_animated_edges(node, snapshot, start_x, y, level_height, build_step, progress, level=0):
        """添加带动画效果的边"""
        if not node or level >= build_step:
            return
        
        node_id = f"tree_node_{id(node)}"
        
        # 添加左子节点边
        if node.left:
            left_id = f"tree_node_{id(node.left)}"
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=left_id,
                arrow_type="line"
            )
            
            # 计算边的位置
            level_width = 200 * (2 ** level)
            edge.from_x = start_x
            edge.from_y = y + level * level_height
            edge.to_x = start_x - level_width/2
            edge.to_y = y + (level + 1) * level_height
            
            # 动画效果：边从淡入到清晰
            if level == build_step - 1:
                edge.color = f"rgba(76, 120, 168, {progress})"  # 透明度动画
            else:
                edge.color = "#4C78A8"
            
            snapshot.edges.append(edge)
            
            # 递归添加左子树的边
            HuffmanTreeAdapter._add_animated_edges(node.left, snapshot, start_x - level_width/2, y, level_height, build_step, progress, level + 1)
        
        # 添加右子节点边
        if node.right:
            right_id = f"tree_node_{id(node.right)}"
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=right_id,
                arrow_type="line"
            )
            
            # 计算边的位置
            level_width = 200 * (2 ** level)
            edge.from_x = start_x
            edge.from_y = y + level * level_height
            edge.to_x = start_x + level_width/2
            edge.to_y = y + (level + 1) * level_height
            
            # 动画效果：边从淡入到清晰
            if level == build_step - 1:
                edge.color = f"rgba(76, 120, 168, {progress})"  # 透明度动画
            else:
                edge.color = "#4C78A8"
            
            snapshot.edges.append(edge)
            
            # 递归添加右子树的边
            HuffmanTreeAdapter._add_animated_edges(node.right, snapshot, start_x + level_width/2, y, level_height, build_step, progress, level + 1)
    
    @staticmethod
    def _create_complete_tree_snapshot(huffman_tree, start_x, y, level_height, node_spacing):
        """创建完整树的快照 - 使用水平布局"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"哈夫曼树 (编码数: {len(huffman_tree.get_codes())})"
        
        # 使用水平布局算法
        positions = HuffmanTreeAdapter._layout_huffman_tree_horizontal(huffman_tree.root, start_x, y, level_height)
        
        # 生成节点快照
        for node, (x, y_pos) in positions.items():
            node_id = f"node_{id(node)}"
            
            label_text = node.char or "*"
            node_color = "#1f4e79"
            # 根据节点类型设置字体颜色：叶子=黄色，内部=白色
            node_text_color = "#FFD700" if node.char else "#FFFFFF"
            HuffmanTreeAdapter._append_circle_node(
                snapshot,
                node_id,
                node.freq,
                x,
                y_pos,
                label_text,
                color=node_color,
                text_color=node_text_color,
            )
        
        # 添加边
        HuffmanTreeAdapter._add_horizontal_tree_edges(huffman_tree.root, positions, snapshot)
        
        return snapshot
    
    @staticmethod
    def _add_edges(node, snapshot, start_x, y, level_height, node_spacing, level=0):
        """递归添加边"""
        if not node:
            return
        
        node_id = f"node_{id(node)}"
        
        # 添加左子节点边
        if node.left:
            left_id = f"node_{id(node.left)}"
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=left_id,
                arrow_type="line"
            )
            edge.from_x = start_x
            edge.from_y = y + level * level_height
            edge.to_x = start_x - node_spacing * (2 ** level) / 2
            edge.to_y = y + (level + 1) * level_height
            edge.color = "#4C78A8"
            snapshot.edges.append(edge)
            
            # 递归添加左子树的边
            HuffmanTreeAdapter._add_edges(node.left, snapshot, start_x - node_spacing * (2 ** level) / 2, y, level_height, node_spacing, level + 1)
        
        # 添加右子节点边
        if node.right:
            right_id = f"node_{id(node.right)}"
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=right_id,
                arrow_type="line"
            )
            edge.from_x = start_x
            edge.from_y = y + level * level_height
            edge.to_x = start_x + node_spacing * (2 ** level) / 2
            edge.to_y = y + (level + 1) * level_height
            edge.color = "#4C78A8"
            snapshot.edges.append(edge)
            
            # 递归添加右子树的边
            HuffmanTreeAdapter._add_edges(node.right, snapshot, start_x + node_spacing * (2 ** level) / 2, y, level_height, node_spacing, level + 1)


class AVLAdapter:
    """AVL树适配器 - 支持平衡因子显示和旋转动画"""
    NODE_DIAMETER = 60
    NODE_RADIUS = NODE_DIAMETER / 2
    
    @staticmethod
    def _circle_snapshot(node_id, value, center_x, center_y, color, text_color="#FFFFFF"):
        return NodeSnapshot(
            id=node_id,
            value=value,
            x=center_x,
            y=center_y,
            node_type="circle",
            width=AVLAdapter.NODE_DIAMETER,
            height=AVLAdapter.NODE_DIAMETER,
            color=color,
            text_color=text_color
        )
    
    @staticmethod
    def _rotate_point(cx, cy, x, y, theta_rad):
        """以 (cx,cy) 为圆心，将点 (x,y) 逆时针旋转 theta_rad 弧度"""
        import math
        dx, dy = x - cx, y - cy
        ct, st = math.cos(theta_rad), math.sin(theta_rad)
        return cx + dx * ct - dy * st, cy + dx * st + dy * ct
    
    @staticmethod
    def _find_node_by_value(node, value):
        """根据值查找节点对象"""
        if not node:
            return None
        if node.value == value:
            return node
        left_result = AVLAdapter._find_node_by_value(node.left, value)
        if left_result:
            return left_result
        return AVLAdapter._find_node_by_value(node.right, value)
    
    @staticmethod
    def _rotate_subtree(subtree_root, positions, center_x, center_y, theta):
        """递归旋转子树中的所有节点，所有节点都围绕同一个中心点旋转"""
        import math
        if not subtree_root:
            return
        
        # 递归处理左子树
        if subtree_root.left and subtree_root.left in positions:
            left_x, left_y = positions[subtree_root.left]
            # 左子节点围绕中心点旋转
            new_left_x, new_left_y = AVLAdapter._rotate_point(center_x, center_y, left_x, left_y, theta)
            positions[subtree_root.left] = (new_left_x, new_left_y)
            # 递归处理左子树
            AVLAdapter._rotate_subtree(subtree_root.left, positions, center_x, center_y, theta)
        
        # 递归处理右子树
        if subtree_root.right and subtree_root.right in positions:
            right_x, right_y = positions[subtree_root.right]
            # 右子节点围绕中心点旋转
            new_right_x, new_right_y = AVLAdapter._rotate_point(center_x, center_y, right_x, right_y, theta)
            positions[subtree_root.right] = (new_right_x, new_right_y)
            # 递归处理右子树
            AVLAdapter._rotate_subtree(subtree_root.right, positions, center_x, center_y, theta)
    
    @staticmethod
    def _layout_tree(node, start_x, y, level_height, node_width, min_spacing):
        """计算AVL树节点位置 - 使用与BST相同的布局算法"""
        if not node:
            return {}
        
        positions = {}
        
        def calculate_positions(current_node, x, y_pos, level):
            if not current_node:
                return x
            
            # 计算左子树宽度
            left_width = 0
            if current_node.left:
                left_width = AVLAdapter._calculate_subtree_width(current_node.left, node_width, min_spacing)
            
            # 当前节点位置
            current_x = x + left_width
            positions[current_node] = (current_x, y_pos)
            
            # 递归计算子节点位置
            if current_node.left:
                calculate_positions(current_node.left, x, y_pos + level_height, level + 1)
            if current_node.right:
                calculate_positions(current_node.right, current_x + node_width + min_spacing, y_pos + level_height, level + 1)
            
            return current_x
        
        calculate_positions(node, start_x, y, 0)
        return positions
    
    @staticmethod
    def _calculate_subtree_width(node, node_width, min_spacing):
        """计算子树宽度"""
        if not node:
            return 0
        
        left_width = AVLAdapter._calculate_subtree_width(node.left, node_width, min_spacing)
        right_width = AVLAdapter._calculate_subtree_width(node.right, node_width, min_spacing)
        
        return left_width + node_width + right_width + (min_spacing if node.left or node.right else 0)
    
    @staticmethod
    def _add_edges(node, positions, snapshot):
        """添加树的边连接"""
        if not node:
            return
        
        node_x, node_y = positions[node]
        node_id = f"node_{id(node)}"
        
        # 添加到左子节点的边
        if node.left:
            left_x, left_y = positions[node.left]
            left_id = f"node_{id(node.left)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=left_id,
                color="#2E86AB",
                arrow_type="line"
            )
            edge.from_x = node_x
            edge.from_y = node_y + AVLAdapter.NODE_RADIUS
            edge.to_x = left_x
            edge.to_y = left_y - AVLAdapter.NODE_RADIUS
            
            snapshot.edges.append(edge)
            
            # 递归处理左子树
            AVLAdapter._add_edges(node.left, positions, snapshot)
        
        # 添加到右子节点的边
        if node.right:
            right_x, right_y = positions[node.right]
            right_id = f"node_{id(node.right)}"
            
            edge = EdgeSnapshot(
                from_id=node_id,
                to_id=right_id,
                color="#2E86AB",
                arrow_type="line"
            )
            edge.from_x = node_x
            edge.from_y = node_y + AVLAdapter.NODE_RADIUS
            edge.to_x = right_x
            edge.to_y = right_y - AVLAdapter.NODE_RADIUS
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            AVLAdapter._add_edges(node.right, positions, snapshot)
    
    @staticmethod
    def to_snapshot(avl, start_x=640, y=200, level_height=120, node_width=60, min_spacing=100) -> StructureSnapshot:
        """将AVL树转换为快照 - 支持平衡因子显示和旋转动画"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"AVL平衡二叉树 (节点数: {len(avl.traverse_inorder())})"
        
        # 获取动画状态
        animation_state = getattr(avl, '_animation_state', None)
        animation_progress = getattr(avl, '_animation_progress', 0.0)
        phase_breaks = getattr(avl, '_phase_breaks', (0.25, 0.5, 0.75, 1.0))
        
        # 在旋转阶段触发真实旋转以保持算法与动画同步
        if animation_state == 'inserting':
            rotation_phase = phase_breaks[2] if len(phase_breaks) >= 3 else 0.75
            has_pending_rotation = getattr(avl, 'has_pending_rotation', None)
            apply_rotation = getattr(avl, 'apply_pending_rotation', None)
            if callable(has_pending_rotation) and callable(apply_rotation):
                if has_pending_rotation() and animation_progress >= rotation_phase:
                    apply_rotation()
        
        # 添加比较信息
        comparison_detail = None
        if animation_state == 'inserting' and hasattr(avl, '_insert_comparison_result') and avl._insert_comparison_result:
            if avl._insert_comparison_result == 'less':
                snapshot.comparison_text = f"新值 {avl._new_value} < 当前值 {avl._current_search_node_value} → 左"
                comparison_detail = f"比较: 新值 {avl._new_value} < 当前 {avl._current_search_node_value} → 左"
            elif avl._insert_comparison_result == 'greater':
                snapshot.comparison_text = f"新值 {avl._new_value} > 当前值 {avl._current_search_node_value} → 右"
                comparison_detail = f"比较: 新值 {avl._new_value} > 当前 {avl._current_search_node_value} → 右"
            else:
                snapshot.comparison_text = f"新值 {avl._new_value} = 当前值 {avl._current_search_node_value} → 已存在"
                comparison_detail = f"比较: 新值 {avl._new_value} = 当前 {avl._current_search_node_value}"
        else:
            snapshot.comparison_text = ""
        
        step_details = []
        if comparison_detail:
            step_details.append(comparison_detail)
        comparing_value = getattr(avl, '_current_search_node_value', None)
        insert_comp_result = getattr(avl, '_insert_comparison_result', None)
        rotation_type = getattr(avl, '_rotation_type', None)
        rotation_nodes = getattr(avl, '_rotation_nodes', []) or []
        rotation_detail_added = False
        
        # 添加旋转类型提示
        if hasattr(avl, '_rotation_type') and avl._rotation_type:
            step_details.append(f"旋转类型: {avl._rotation_type}型")
            rotation_detail_added = True
        
        if not avl.root:
            return snapshot
        
        # 使用改进的布局算法
        positions = AVLAdapter._layout_tree(
            avl.root, start_x, y, level_height, node_width, min_spacing)
        # 旋转阶段插值：使用未旋转影子树位置与当前树位置进行插值
        rotation_progress = getattr(avl, '_rotation_anim_progress', 0.0)
        shadow_root = getattr(avl, '_shadow_after_insert', None)

        def _clone_simple(node):
            if not node:
                return None
            nn = type("TmpNode", (), {})()
            nn.value = getattr(node, "value", None)
            nn.left = _clone_simple(getattr(node, "left", None))
            nn.right = _clone_simple(getattr(node, "right", None))
            return nn

        def _rotate_left_at(root_node, target_val):
            if not root_node:
                return root_node
            if root_node.value == target_val:
                x = root_node
                y = x.right
                if not y:
                    return x
                x.right = y.left
                y.left = x
                return y
            if target_val < root_node.value:
                root_node.left = _rotate_left_at(root_node.left, target_val)
            else:
                root_node.right = _rotate_left_at(root_node.right, target_val)
            return root_node

        def _rotate_right_at(root_node, target_val):
            if not root_node:
                return root_node
            if root_node.value == target_val:
                y = root_node
                x = y.left
                if not x:
                    return y
                y.left = x.right
                x.right = y
                return x
            if target_val < root_node.value:
                root_node.left = _rotate_right_at(root_node.left, target_val)
            else:
                root_node.right = _rotate_right_at(root_node.right, target_val)
            return root_node

        def _layout_snapshot(root_node):
            if not root_node:
                return {}
            return AVLAdapter._layout_tree(
                root_node, start_x, y, level_height, node_width, min_spacing
            )

        # 预布局（旋转前）
        pre_positions = {}
        if shadow_root is not None:
            pre_positions = _layout_snapshot(shadow_root)

        # 中间布局（两段动画）
        mid_positions = {}
        if shadow_root is not None and rotation_type:
            cloned_root = _clone_simple(shadow_root)
            if rotation_type == "LL":
                mid_root = _rotate_right_at(cloned_root, rotation_nodes[0] if rotation_nodes else None)
            elif rotation_type == "RR":
                mid_root = _rotate_left_at(cloned_root, rotation_nodes[0] if rotation_nodes else None)
            elif rotation_type == "LR":
                # 先对子节点左旋
                child_val = rotation_nodes[1] if len(rotation_nodes) > 1 else None
                if child_val is not None:
                    cloned_root = _rotate_left_at(cloned_root, child_val)
                mid_root = cloned_root
            elif rotation_type == "RL":
                # 先对子节点右旋
                child_val = rotation_nodes[1] if len(rotation_nodes) > 1 else None
                if child_val is not None:
                    cloned_root = _rotate_right_at(cloned_root, child_val)
                mid_root = cloned_root
            else:
                mid_root = cloned_root
            mid_positions = _layout_snapshot(mid_root)

        # 最终布局（当前真实树）
        final_positions = positions

        def _pos_map(layout):
            return {str(n.value): pos for n, pos in layout.items()} if layout else {}

        pre_map = _pos_map(pre_positions)
        mid_map = _pos_map(mid_positions)
        final_map = _pos_map(final_positions)

        render_positions = {}
        for node, final_pos in final_positions.items():
            key = str(getattr(node, "value", ""))
            if rotation_progress <= 0.0:
                render_positions[node] = pre_map.get(key, final_pos)
            elif rotation_progress < 0.5 and mid_positions:
                t = rotation_progress / 0.5
                start_pos = pre_map.get(key, final_pos)
                mid_pos = mid_map.get(key, final_pos)
                rx = start_pos[0] + (mid_pos[0] - start_pos[0]) * t
                ry = start_pos[1] + (mid_pos[1] - start_pos[1]) * t
                render_positions[node] = (rx, ry)
            elif rotation_progress < 1.0 and mid_positions:
                t = (rotation_progress - 0.5) / 0.5
                mid_pos = mid_map.get(key, final_pos)
                end_pos = final_map.get(key, final_pos)
                rx = mid_pos[0] + (end_pos[0] - mid_pos[0]) * t
                ry = mid_pos[1] + (end_pos[1] - mid_pos[1]) * t
                render_positions[node] = (rx, ry)
            else:
                render_positions[node] = final_pos
        rotation_active = (
            animation_state == 'inserting'
            and rotation_type is not None
            and animation_progress >= phase_breaks[2]
        )
        # 旋转步骤描述（更细粒度）
        if rotation_type and not rotation_detail_added:
            if rotation_type == 'LL':
                step_details.extend([
                    "LL右旋：以失衡节点为支点",
                    "步骤1：提升左子节点为新根",
                    "步骤2：原根成为右子节点"
                ])
            elif rotation_type == 'RR':
                step_details.extend([
                    "RR左旋：以失衡节点为支点",
                    "步骤1：提升右子节点为新根",
                    "步骤2：原根成为左子节点"
                ])
            elif rotation_type == 'LR':
                step_details.extend([
                    "LR双旋：先对左子节点左旋，再对根右旋",
                    "步骤1：左子节点左旋让孙节点上升",
                    "步骤2：根节点右旋完成平衡"
                ])
            elif rotation_type == 'RL':
                step_details.extend([
                    "RL双旋：先对右子节点右旋，再对根左旋",
                    "步骤1：右子节点右旋让孙节点上升",
                    "步骤2：根节点左旋完成平衡"
                ])
        # 双步提示的当前阶段
        if rotation_active and rotation_progress < 0.5 and rotation_type in ("LR", "RL"):
            step_details.append("旋转阶段：第1步进行中")
        elif rotation_active and rotation_progress >= 0.5 and rotation_type in ("LR", "RL"):
            step_details.append("旋转阶段：第2步进行中")
        elif rotation_active and rotation_type in ("LL", "RR"):
            if rotation_progress < 0.5:
                step_details.append("旋转阶段：准备旋转")
            else:
                step_details.append("旋转阶段：完成旋转")
        
        # 在生成节点快照前，先收集失衡节点信息
        imbalance_nodes = set()  # 平衡因子为±2的节点集合
        imbalance_children = set()  # 失衡节点的目标子节点集合
        
        for node in positions.keys():
            balance_factor = avl._get_balance_factor(node)
            # 找到失衡节点（平衡因子为±2）
            if abs(balance_factor) == 2:
                imbalance_nodes.add(node)
                # 根据平衡方向只标记重子节点
                if balance_factor > 1 and node.left:
                    imbalance_children.add(node.left)
                elif balance_factor < -1 and node.right:
                    imbalance_children.add(node.right)
        
        # 生成节点快照
        pivot_val = rotation_nodes[0] if rotation_nodes else None
        heavy_val = rotation_nodes[1] if len(rotation_nodes) > 1 else None
        grand_val = rotation_nodes[2] if len(rotation_nodes) > 2 else None
        for node, (x, y_pos) in render_positions.items():
            node_id = f"node_{id(node)}"
            
            # 计算平衡因子
            balance_factor = avl._get_balance_factor(node)
            is_checking = (hasattr(avl, '_current_check_node_value') and 
                           avl._current_check_node_value is not None and 
                           str(avl._current_check_node_value) == str(node.value))
            
            # 确定节点颜色和边框（简化逻辑，只保留失衡节点高亮）
            is_comparing_node = (
                animation_state == 'inserting'
                and insert_comp_result
                and comparing_value is not None
                and str(comparing_value) == str(node.value)
            )
            
            if node in imbalance_nodes:
                # 失衡节点（平衡因子为±2）- 整个节点填充红色
                node_color = "#FF0000"
                border_color = None
            elif node in imbalance_children:
                # 失衡节点的重子节点 - 整个节点填充黄色
                node_color = "#FFFF00"
                border_color = None
            elif rotation_active and pivot_val is not None and str(node.value) == str(pivot_val):
                node_color = "#FF6B6B"
                border_color = "#1f4e79"
            elif rotation_active and heavy_val is not None and str(node.value) == str(heavy_val):
                node_color = "#FFA500"
                border_color = "#1f4e79"
            elif rotation_active and grand_val is not None and str(node.value) == str(grand_val):
                node_color = "#FFD27F"
                border_color = "#1f4e79"
            elif is_comparing_node:
                # 阶段1比较路径节点 - 使用黄色高亮
                node_color = "#FFD700"
                border_color = None
            else:
                # 其他所有节点（包括新插入、比较、旋转节点）- 深蓝色
                node_color = "#1f4e79"  # 深蓝色
                border_color = None
            
            # 使用 positions 中已更新的位置（如果节点参与了旋转，位置已在前面更新）
            current_x, current_y = x, y_pos
            
            node_snapshot = AVLAdapter._circle_snapshot(
                node_id,
                str(node.value),
                current_x,
                current_y,
                node_color
            )
            
            # 添加边框颜色属性（检查节点保留金色边框）
            if is_checking:
                node_snapshot.border_color = "#FFD700"
                node_snapshot.border_width = 3
            elif border_color:
                node_snapshot.border_color = border_color
                node_snapshot.border_width = 3
            
            snapshot.nodes.append(node_snapshot)
            
            # 添加平衡因子标签
            bf_text = str(balance_factor)
            balance_label = BoxSnapshot(
                id=f"balance_{node_id}",
                value=bf_text,
                x=current_x + 50,  # 节点右侧
                y=current_y - 8,  # 节点上方
                width=48,
                height=24,
                color="#8B4513" if abs(balance_factor) <= 1 else "#FF6B6B",  # 褐色正常，红色失衡
                text_color="#FFFFFF"
            )
            snapshot.boxes.append(balance_label)
            
            # 在旋转阶段为支点添加方向标注
            if rotation_active and pivot_val is not None and str(node.value) == str(pivot_val):
                arrow_text = "右旋" if rotation_type in ("LL", "LR") else "左旋"
                label_box = BoxSnapshot(
                    id=f"rotate_label_{node_id}",
                    value=arrow_text,
                    x=current_x - 25,
                    y=current_y - 60,
                    width=60,
                    height=22,
                    color="#FF6B6B",
                    text_color="#FFFFFF"
                )
                snapshot.boxes.append(label_box)
        
        if step_details:
            snapshot.step_details = step_details
        
        # 生成边快照
        AVLAdapter._add_edges(avl.root, render_positions, snapshot)
        
        # 显示根指针 - 放在根节点上方
        root_pointer_x = start_x - 30  # 与根节点中心对齐
        root_pointer_y = y - 50  # 在根节点上方
        root_pointer_box = BoxSnapshot(
            id="root_pointer",
            value="root",
            x=root_pointer_x,
            y=root_pointer_y,
            width=60,
            height=30,
            color="#FFD700",  # 金色
            text_color="#000000"
        )
        snapshot.boxes.append(root_pointer_box)
        
        # 添加根指针箭头
        root_arrow = EdgeSnapshot(
            from_id="root_pointer",
            to_id=f"node_{id(avl.root)}",
            color="#FFD700",
            arrow_type="arrow"
        )
        root_arrow.from_x = root_pointer_x + 30
        root_arrow.from_y = root_pointer_y + 30
        root_arrow.to_x = start_x
        root_arrow.to_y = y - AVLAdapter.NODE_RADIUS
        snapshot.edges.append(root_arrow)
        
        return snapshot

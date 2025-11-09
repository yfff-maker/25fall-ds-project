# -*- coding: utf-8 -*-
"""
数据适配器：将数据结构状态转换为可视化快照
"""
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
            total_child_width = left_width + right_width + min_spacing * 1.5
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
            # 设置连线坐标 - 从红色左指针方框出发，连接到子节点中心
            edge.from_x = node_x - 60  # 左指针方框位置
            edge.from_y = node_y - 30  # 左指针方框位置（稍微偏下）
            edge.to_x = left_x - 40  # 子节点中心x坐标
            edge.to_y = left_y - 10  # 子节点中心y坐标（稍微偏上）
            
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
            # 设置连线坐标 - 从绿色右指针方框出发，连接到子节点中心
            edge.from_x = node_x  # 右指针方框位置
            edge.from_y = node_y - 30  # 右指针方框位置
            edge.to_x = right_x - 40  # 子节点中心x坐标
            edge.to_y = right_y - 10  # 子节点中心y坐标（稍微偏下）
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            BSTAdapter._add_edges(node.right, positions, snapshot)
    
    @staticmethod
    def to_snapshot(bst, start_x=640, y=200, level_height=80, node_width=60, min_spacing=100) -> StructureSnapshot:
        """将BST转换为快照 - 使用与链式二叉树相同的布局算法"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"二叉搜索树 (节点数: {len(bst.traverse_inorder())})"
        
        # 获取动画状态
        animation_state = getattr(bst, '_animation_state', None)
        animation_progress = getattr(bst, '_animation_progress', 0.0)
        
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
                root_edge.to_y = current_y - 20
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
            elif is_searching_node or is_insert_comparing_node:
                # 当前正在比较的节点 - 黄色
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#FFD700"  # 黄色表示正在比较
                )
            elif is_found_node:
                # 找到的目标节点 - 绿色
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#00FF00"  # 绿色表示找到
                )
            elif is_last_searched_node:
                # 最后搜索的节点（未找到时）- 橙色
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#FFA500"  # 橙色表示最后搜索
                )
            elif is_deleting_node:
                # 当前正在比较的删除节点 - 黄色
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#FFD700"  # 黄色表示正在比较
                )
            elif is_delete_target_node:
                # 要删除的目标节点 - 红色
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#FF0000"  # 红色表示要删除的节点
                )
            elif is_delete_replacement_node:
                # 替换节点（两子节点情况）- 蓝色
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.value),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#0000FF"  # 蓝色表示替换节点
                )
            else:
                # 普通节点 - 深蓝色
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
            root_edge.to_y = y - 20  # 到根节点顶部
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
                        x=current_x - 30,
                        y=current_y - 20,
                        node_type="box",
                        width=60,
                        height=40,
                        color="#FF6B6B"  # 红色表示正在移动
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
            # 如果还是没有，尝试从原始频率映射构建
            if not leaves:
                freq_map = getattr(huffman, '_original_freq_map', {})
                if freq_map:
                    queue = [(char, freq) for char, freq in freq_map.items()]
                else:
                    queue = []
            else:
                queue = leaves
        
        if not queue:
            # 如果队列为空但已有根节点，显示完整树（使用中序横向、层级纵向布局）
            root = getattr(huffman, 'root', None)
            if root:
                # 1) 中序遍历为每个节点分配横向序号（xIndex），纵向按深度（level）分层
                positions = {}  # node -> (xIndex, level)
                x_counter = 0
                
                def assign_positions(node, level=0):
                    nonlocal x_counter
                    if not node:
                        return
                    assign_positions(getattr(node, 'left', None), level + 1)
                    positions[node] = (x_counter, level)
                    x_counter += 1
                    assign_positions(getattr(node, 'right', None), level + 1)
                
                assign_positions(root, 0)
                
                if positions:
                    # 2) 把 xIndex/level 转换为像素坐标（类似 BST 的形状）
                    x_step = 110   # 横向间距
                    y_step = 90    # 纵向层距
                    base_x = merge_cx + 200
                    base_y = y - 140
                    
                    # 3) 先画边（父→子），再画节点框
                    def pix(node):
                        xi, lv = positions[node]
                        return base_x + xi * x_step, base_y + lv * y_step
                    
                    for node, (xi, lv) in positions.items():
                        x0, y0 = pix(node)
                        # 左子
                        if getattr(node, 'left', None):
                            xl, yl = pix(node.left)
                            e = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                            e.from_x, e.from_y = x0, y0
                            e.to_x,   e.to_y   = xl, yl
                            e.color = "#1f77b4"  # 左 0：蓝
                            snapshot.edges.append(e)
                        # 右子
                        if getattr(node, 'right', None):
                            xr, yr = pix(node.right)
                            e = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                            e.from_x, e.from_y = x0, y0
                            e.to_x,   e.to_y   = xr, yr
                            e.color = "#d62728"  # 右 1：红
                            snapshot.edges.append(e)
                    
                    # 4) 画节点框（根节点高亮）
                    for node, (xi, lv) in positions.items():
                        x0, y0 = pix(node)
                        nid = f"t_{id(node)}"
                        val = getattr(node, 'char', None) or "*"
                        freq = getattr(node, 'freq', 0)
                        color = "#90EE90" if node == root else "#E8F4FD"
                        box = BoxSnapshot(
                            id=f"{nid}_box",
                            value=f"{val}\n{freq}%",
                            x=x0 - 40, y=y0 - 20,
                            width=80, height=40,
                            color=color
                        )
                        snapshot.boxes.append(box)
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
        
        # 选中集合（当前合并的两项，可能是叶子也可能是子树）
        selected_ids = set()
        for it in current_merge:
            # 兼容传 id / 传对象 / 传字符
            if isinstance(it, (tuple, list)) or hasattr(it, 'freq'):
                selected_ids.add(item_id(it))
            else:
                selected_ids.add(f"leaf_{it}")  # 假定字符
        
        # 队列横向排布
        def queue_pos(i):
            return start_x + i * spacing, y
        
        # 画方框（字符+频率）
        def draw_box(id_key, label, freq, x, yy, color="#E8F4FD", text_color="#000", scale=1.0):
            bw = int(box_w * scale); bh = int(box_h * scale)
            box = BoxSnapshot(
                id=f"hf_{id_key}",
                value=f"{label}\n{freq}%",
                x=x - bw // 2, y=yy - bh // 2,
                width=bw, height=bh,
                color=color, text_color=text_color
            )
            snapshot.boxes.append(box)
            return box
        
        # 画折线模拟弧线（p->mid->q）
        def draw_arc(x1, y1, x2, y2, color="#FF8C00", lift=60):
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
                    e.color = "#1f77b4"  # 左 0
                    snapshot.edges.append(e)
                if getattr(nd, 'right', None):
                    xr, yr = pix(nd.right)
                    e = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                    e.from_x, e.from_y = x0, y0
                    e.to_x,   e.to_y   = xr, yr
                    e.color = "#d62728"  # 右 1
                    snapshot.edges.append(e)
            # 再画小框
            bw = int(80 * 0.6 * scale); bh = int(40 * 0.6 * scale)
            for nd in pos.keys():
                x0, y0 = pix(nd)
                nid = f"mini_{id(nd)}"
                val = getattr(nd, 'char', None) or "*"
                freq = getattr(nd, 'freq', 0)
                box = BoxSnapshot(
                    id=f"{nid}_box",
                    value=f"{val}\n{freq}%",
                    x=x0 - bw//2, y=y0 - bh//2,
                    width=bw, height=bh,
                    color="#E8F4FD"
                )
                snapshot.boxes.append(box)
        
        def lerp(a, b, t):
            return a + (b - a) * t
        
        # 预计算队列排布
        layout = []  # [(it, id, label, freq, qx, qy), ...]
        for i, it in enumerate(queue):
            iid = item_id(it)
            ch = get_char(it)
            freq = get_freq(it)
            label = ch if ch not in (None, "", "*") else "*"
            qx, qy = queue_pos(i)
            layout.append((it, iid, label, freq, qx, qy))
        
        # 找到被选中两项（按频率排序，决定回队列的中间位置）
        selected = [t for t in layout if t[1] in selected_ids]
        selected = sorted(selected, key=lambda x: x[3])[:2] if selected else []
        
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
                    draw_box(iid, label, freq, qx, qy, color="#EEEEEE", text_color="#888")
                else:
                    draw_box(iid, label, freq, qx, qy, color="#E8F4FD")
        
        # 2) 对被选中两项做动画
        if len(selected) == 2:
            (itA, idA, labelA, freqA, ax0, ay0), (itB, idB, labelB, freqB, bx0, by0) = selected
            
            # 0.00–0.20 高亮队列中的两个
            if progress < 0.20:
                # A
                if is_tree(itA):
                    draw_compact_tree(itA, ax0, ay0 - 6, scale=0.85)
                else:
                    draw_box(idA, labelA, freqA, ax0, ay0, color="#FFD166")
                # B
                if is_tree(itB):
                    draw_compact_tree(itB, bx0, by0 - 6, scale=0.85)
                else:
                    draw_box(idB, labelB, freqB, bx0, by0, color="#F58518")
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
                    draw_box(idA, labelA, freqA, ax, ay, color="#FFD166")
                # B
                if is_tree(itB):
                    draw_compact_tree(itB, bx, by, scale=0.9)
                else:
                    draw_box(idB, labelB, freqB, bx, by, color="#F58518")
                draw_arc(ax0, ay0, ax, ay, color="#F58518", lift=40)
                draw_arc(bx0, by0, bx, by, color="#F58518", lift=40)
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
                    draw_box(idA, labelA, freqA, ax, ay, color="#FFD166", scale=scale)
                if is_tree(itB):
                    draw_compact_tree(itB, bx, by, scale=scale)
                else:
                    draw_box(idB, labelB, freqB, bx, by, color="#F58518", scale=scale)
                
                # 父节点（仅渲染用）
                try:
                    pfreq = (int(freqA) if str(freqA).isdigit() else freqA) + \
                            (int(freqB) if str(freqB).isdigit() else freqB)
                except (ValueError, TypeError):
                    pfreq = freqA + freqB
                # 父->子连线（连接到两棵子树的根）
                draw_box("par_tmp", f"{labelA}+{labelB}", pfreq, merge_cx, merge_cy, color="#4ECDC4")
                # 父→A根
                eL = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                eL.from_x, eL.from_y = merge_cx, merge_cy
                eL.to_x,   eL.to_y   = ax, ay
                eL.color = "#1f77b4"  # 左 0
                snapshot.edges.append(eL)
                # 父→B根
                eR = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                eR.from_x, eR.from_y = merge_cx, merge_cy
                eR.to_x,   eR.to_y   = bx, by
                eR.color = "#d62728"  # 右 1
                snapshot.edges.append(eR)
                
                if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                    snapshot.step_details = []
                snapshot.step_details.append("融合生成新节点")
            
            # 0.60–0.80 父节点回到队列中点，旧两项淡出
            elif progress < 0.80:
                t = (progress - 0.60) / 0.20
                # 父节点作为"新树根"回队列中点
                rx = lerp(merge_cx, mid_x if mid_x is not None else merge_cx, t)
                ry = lerp(merge_cy, y, t)
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
                    draw_box(idA, labelA, freqA, ax0, ay0, color="#EEEEEE", text_color="#888")
                if not is_tree(itB):
                    draw_box(idB, labelB, freqB, bx0, by0, color="#EEEEEE", text_color="#888")
                
                if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                    snapshot.step_details = []
                snapshot.step_details.append("新节点回到队列")
            
            # 0.80–1.00 等下一轮（队列静态，父节点已就位）
            else:
                if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                    snapshot.step_details = []
                snapshot.step_details.append("等待下一轮合并")
        
        # 若已存在根，则（接近完成时）在右侧绘整棵树并突出根
        root = getattr(huffman, 'root', None)
        if root and (state in (None, "done", "huffman_done") or progress >= 0.95):
            # 1) 中序遍历为每个节点分配横向序号（xIndex），纵向按深度（level）分层
            positions = {}  # node -> (xIndex, level)
            x_counter = 0
            
            def assign_positions(node, level=0):
                nonlocal x_counter
                if not node:
                    return
                assign_positions(getattr(node, 'left', None), level + 1)
                positions[node] = (x_counter, level)
                x_counter += 1
                assign_positions(getattr(node, 'right', None), level + 1)
            
            assign_positions(root, 0)
            
            if positions:
                # 2) 把 xIndex/level 转换为像素坐标（类似 BST 的形状）
                x_step = 110   # 横向间距（可按画布宽调整）
                y_step = 90    # 纵向层距
                # 让整个树整体偏右一些（避免和队列重叠）
                # 你也可以把 base_x 设为画布中点，或根据节点总数动态居中
                base_x = merge_cx + 200
                base_y = y - 140
                
                # 3) 先画边（父→子），再画节点框
                def pix(node):
                    xi, lv = positions[node]
                    return base_x + xi * x_step, base_y + lv * y_step
                
                for node, (xi, lv) in positions.items():
                    x0, y0 = pix(node)
                    # 左子
                    if getattr(node, 'left', None):
                        xl, yl = pix(node.left)
                        e = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                        e.from_x, e.from_y = x0, y0
                        e.to_x,   e.to_y   = xl, yl
                        e.color = "#1f77b4"  # 左 0：蓝
                        snapshot.edges.append(e)
                    # 右子
                    if getattr(node, 'right', None):
                        xr, yr = pix(node.right)
                        e = EdgeSnapshot(from_id="", to_id="", arrow_type="arrow")
                        e.from_x, e.from_y = x0, y0
                        e.to_x,   e.to_y   = xr, yr
                        e.color = "#d62728"  # 右 1：红
                        snapshot.edges.append(e)
                
                # 4) 画节点框（根节点高亮）
                for node, (xi, lv) in positions.items():
                    x0, y0 = pix(node)
                    nid = f"t_{id(node)}"
                    val = getattr(node, 'char', None) or "*"
                    freq = getattr(node, 'freq', 0)
                    color = "#90EE90" if node == root else "#E8F4FD"
                    box = BoxSnapshot(
                        id=f"{nid}_box",
                        value=f"{val}\n{freq}%",
                        x=x0 - 40, y=y0 - 20,
                        width=80, height=40,
                        color=color
                    )
                    snapshot.boxes.append(box)
            
            if not hasattr(snapshot, 'step_details') or snapshot.step_details is None:
                snapshot.step_details = []
            snapshot.step_details.append("最终树已形成：中序横向、层级纵向布局")
        
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
        color = "#90EE90" if node == root_node else "#E8F4FD"
        
        box = BoxSnapshot(id=f"{nid}_box", value=f"{val}\n{freq}%", x=x-40, y=yy-20, width=80, height=40, color=color)
        snapshot.boxes.append(box)
        
        if getattr(node, 'left', None):
            lx, ly = x - dx, yy + dy
            e = EdgeSnapshot(from_id=f"{nid}_box", to_id=f"t_{id(node.left)}_box", arrow_type="arrow")
            e.from_x, e.from_y = x, yy; e.to_x, e.to_y = lx, ly; e.color = "#1f77b4"
            snapshot.edges.append(e)
            HuffmanTreeAdapter._draw_final_tree(node.left, snapshot, lx, ly, dx=int(dx*0.75), dy=dy, root_node=root_node)
        
        if getattr(node, 'right', None):
            rx, ry = x + dx, yy + dy
            e = EdgeSnapshot(from_id=f"{nid}_box", to_id=f"t_{id(node.right)}_box", arrow_type="arrow")
            e.from_x, e.from_y = x, yy; e.to_x, e.to_y = rx, ry; e.color = "#d62728"
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
            
            if is_merging:
                # 节点正在合并
                target_x = start_x  # 合并区域
                target_y = y + 200
                current_x = target_x
                current_y = target_y
                color = "#FF6B6B"  # 红色表示正在合并
                scale = 0.8 + 0.4 * progress  # 逐渐变大
            elif is_moving:
                # 节点正在移动
                target_x = start_x  # 合并区域
                target_y = y + 200
                current_x = node_x + (target_x - node_x) * progress
                current_y = node_y + (target_y - node_y) * progress
                color = "#FFD700"  # 金色表示正在移动
                scale = 1.2
            elif is_returning:
                # 节点正在返回
                target_x = top_start_x + i * node_spacing
                target_y = top_y
                current_x = start_x + (target_x - start_x) * progress
                current_y = y + 200 + (target_y - (y + 200)) * progress
                color = "#00FF00"  # 绿色表示新节点
                scale = 1.1
            elif build_step >= 2 and i < 2:
                # 已合并的节点淡出
                fade_alpha = max(0.1, 1.0 - (build_step - 2) * 0.5)
                color = f"rgba(76, 120, 168, {fade_alpha})"  # 淡出效果
                scale = 0.8
            elif is_selected:
                # 被选中的节点
                color = "#FFD700"  # 金色高亮
                scale = 1.1
            else:
                # 普通节点
                if tree.char is not None:
                    color = "#4C78A8"  # 蓝色表示叶子节点
                else:
                    color = "#8B4513"  # 棕色表示子树
                scale = 1.0
            
            # 确定最终位置
            final_x = current_x if (is_moving or is_merging or is_returning) else node_x
            final_y = current_y if (is_moving or is_merging or is_returning) else node_y
            
            # 根据节点类型选择形状
            node_type = "circle" if tree.char is not None else "box"
            
            node_snapshot = NodeSnapshot(
                id=f"queue_{i}_{char}",
                value=str(freq),  # 只显示权值数字
                x=final_x,
                y=final_y,
                node_type=node_type,
                color=color,
                width=int(60 * scale),
                height=int(60 * scale)
            )
            snapshot.nodes.append(node_snapshot)
            
            # 如果是子树且不在移动/合并/返回状态，显示子树结构
            if tree.char is None and not (is_moving or is_merging or is_returning):
                HuffmanTreeAdapter._add_subtree_visualization(tree, snapshot, final_x, final_y, node_spacing)
            
            # 如果节点正在移动，添加移动路径指示
            if is_moving and progress < 0.8:
                path_edge = EdgeSnapshot(
                    from_id=f"path_{char}",
                    to_id=f"target_{char}",
                    arrow_type="line"
                )
                path_edge.from_x = node_x
                path_edge.from_y = node_y
                path_edge.to_x = start_x
                path_edge.to_y = y + 200
                path_edge.color = "#FFD700"
                snapshot.edges.append(path_edge)
        
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
                
                new_node_snapshot = NodeSnapshot(
                    id="merged_node",
                    value=str(merged_freq),  # 只显示权值数字
                    x=new_node_x,
                    y=new_node_y,
                    node_type="circle",
                    color=color,
                    width=int(60 * scale),
                    height=int(60 * scale)
                )
                snapshot.nodes.append(new_node_snapshot)
        
        # 显示已构建的树结构
        if build_step > 0:
            HuffmanTreeAdapter._add_built_tree_nodes(huffman_tree, snapshot, start_x + 200, y, level_height, build_step, progress)
        
        # 如果动画完成，显示最终树和编码路径
        if build_step >= 4 and progress > 0.9:
            HuffmanTreeAdapter._add_final_tree_with_codes(huffman_tree, snapshot, start_x + 400, y, level_height)
        
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
    def _add_subtree_visualization(tree, snapshot, center_x, center_y, spacing):
        """添加子树的可视化表示"""
        if tree.char is not None:
            return  # 叶子节点不需要子树可视化
        
        # 计算子树的位置
        left_x = center_x - spacing * 0.3
        right_x = center_x + spacing * 0.3
        child_y = center_y + 40
        
        # 添加子节点
        if tree.left:
            left_node = NodeSnapshot(
                id=f"subtree_left_{id(tree)}",
                value=str(tree.left.freq),
                x=left_x,
                y=child_y,
                node_type="circle" if tree.left.char is not None else "box",
                color="#4C78A8" if tree.left.char is not None else "#8B4513",
                width=40,
                height=40
            )
            snapshot.nodes.append(left_node)
            
            # 添加边
            edge = EdgeSnapshot(
                from_id=f"queue_{id(tree)}",
                to_id=f"subtree_left_{id(tree)}",
                arrow_type="line"
            )
            edge.from_x = center_x - 15
            edge.from_y = center_y + 15
            edge.to_x = left_x + 20
            edge.to_y = child_y - 20
            edge.color = "#2E86AB"
            snapshot.edges.append(edge)
        
        if tree.right:
            right_node = NodeSnapshot(
                id=f"subtree_right_{id(tree)}",
                value=str(tree.right.freq),
                x=right_x,
                y=child_y,
                node_type="circle" if tree.right.char is not None else "box",
                color="#4C78A8" if tree.right.char is not None else "#8B4513",
                width=40,
                height=40
            )
            snapshot.nodes.append(right_node)
            
            # 添加边
            edge = EdgeSnapshot(
                from_id=f"queue_{id(tree)}",
                to_id=f"subtree_right_{id(tree)}",
                arrow_type="line"
            )
            edge.from_x = center_x + 15
            edge.from_y = center_y + 15
            edge.to_x = right_x - 20
            edge.to_y = child_y - 20
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
    def _add_final_tree_with_codes(huffman_tree, snapshot, start_x, y, level_height):
        """添加最终树和编码路径 - 使用水平布局"""
        if not huffman_tree.root:
            return
        
        # 获取哈夫曼编码
        codes = huffman_tree.get_codes()
        
        # 使用类似BST的水平布局算法
        positions = HuffmanTreeAdapter._layout_huffman_tree_horizontal(huffman_tree.root, start_x, y, level_height)
        
        # 生成节点快照
        for node, (x, y_pos) in positions.items():
            node_id = f"final_node_{id(node)}"
            
            # 创建节点快照
            if node.char is not None:
                # 叶子节点 - 只显示权值
                node_value = str(node.freq)
                node_color = "#FF6B6B"  # 红色表示叶子节点
            else:
                # 内部节点 - 显示权值
                node_value = str(node.freq)
                node_color = "#4C78A8"  # 蓝色表示内部节点
            
            node_snapshot = NodeSnapshot(
                id=node_id,
                value=node_value,
                x=x - 30,  # 节点中心对齐
                y=y_pos - 20,
                node_type="box",
                width=60,
                height=40,
                color=node_color
            )
            snapshot.nodes.append(node_snapshot)
            
            # 添加编码路径标签
            if node.char is not None and codes.get(node.char, ''):
                code_label = BoxSnapshot(
                    id=f"code_{node.char}",
                    value=f"{node.char}: {codes.get(node.char, '')}",
                    x=x - 40,
                    y=y_pos + 30,
                    width=80,
                    height=20,
                    color="#E0E0E0"
                )
                snapshot.boxes.append(code_label)
                
        # 添加边连接
        HuffmanTreeAdapter._add_horizontal_tree_edges(huffman_tree.root, positions, snapshot)
    
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
            edge.from_x = node_x - 30  # 从节点左边缘
            edge.from_y = node_y + 20  # 从节点底部
            edge.to_x = left_x + 30  # 到子节点右边缘
            edge.to_y = left_y - 20  # 到子节点顶部
            
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
            edge.from_x = node_x + 30  # 从节点右边缘
            edge.from_y = node_y + 20  # 从节点底部
            edge.to_x = right_x - 30  # 到子节点左边缘
            edge.to_y = right_y - 20  # 到子节点顶部
            
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
                
                # 创建节点快照
                if node.char is not None:
                    # 叶子节点
                    node_snapshot = NodeSnapshot(
                        id=node_id,
                        value=f"{node.char}\n{node.freq}",
                        x=node_x,
                        y=node_y,
                        node_type="circle",
                        color="#FF6B6B",
                        width=int(40 * scale),
                        height=int(40 * scale)
                    )
                else:
                    # 内部节点
                    node_snapshot = NodeSnapshot(
                        id=node_id,
                        value=str(node.freq),
                        x=node_x,
                        y=node_y,
                        node_type="circle",
                        color="#4C78A8",
                        width=int(40 * scale),
                        height=int(40 * scale)
                    )
                
                snapshot.nodes.append(node_snapshot)
                
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
            
            # 创建节点快照
            if node.char is not None:
                # 叶子节点 - 只显示权值
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.freq),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#FF6B6B"  # 红色表示叶子节点
                )
            else:
                # 内部节点
                node_snapshot = NodeSnapshot(
                    id=node_id,
                    value=str(node.freq),
                    x=x - 30,  # 节点中心对齐
                    y=y_pos - 20,
                    node_type="box",
                    width=60,
                    height=40,
                    color="#4C78A8"  # 蓝色表示内部节点
                )
            
            snapshot.nodes.append(node_snapshot)
        
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
            # 设置连线坐标 - 从红色左指针方框出发，连接到子节点中心
            edge.from_x = node_x - 60  # 左指针方框位置
            edge.from_y = node_y - 30  # 左指针方框位置（稍微偏下）
            edge.to_x = left_x - 40  # 子节点中心x坐标
            edge.to_y = left_y - 10  # 子节点中心y坐标（稍微偏上）
            
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
            # 设置连线坐标 - 从绿色右指针方框出发，连接到子节点中心
            edge.from_x = node_x  # 右指针方框位置
            edge.from_y = node_y - 30  # 右指针方框位置
            edge.to_x = right_x - 40  # 子节点中心x坐标
            edge.to_y = right_y - 10  # 子节点中心y坐标（稍微偏下）
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            AVLAdapter._add_edges(node.right, positions, snapshot)
    
    @staticmethod
    def to_snapshot(avl, start_x=640, y=200, level_height=80, node_width=60, min_spacing=100) -> StructureSnapshot:
        """将AVL树转换为快照 - 支持平衡因子显示和旋转动画"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"AVL平衡二叉树 (节点数: {len(avl.traverse_inorder())})"
        
        # 获取动画状态
        animation_state = getattr(avl, '_animation_state', None)
        animation_progress = getattr(avl, '_animation_progress', 0.0)
        
        # 添加比较信息
        if animation_state == 'inserting' and hasattr(avl, '_insert_comparison_result') and avl._insert_comparison_result:
            if avl._insert_comparison_result == 'less':
                snapshot.comparison_text = f"新值 {avl._new_value} < 当前值 {avl._current_search_node_value} → 左"
            elif avl._insert_comparison_result == 'greater':
                snapshot.comparison_text = f"新值 {avl._new_value} > 当前值 {avl._current_search_node_value} → 右"
            else:
                snapshot.comparison_text = f"新值 {avl._new_value} = 当前值 {avl._current_search_node_value} → 已存在"
        else:
            snapshot.comparison_text = ""
        
        # 添加旋转类型提示
        if hasattr(avl, '_rotation_type') and avl._rotation_type:
            snapshot.step_details = f"旋转类型: {avl._rotation_type}型"
        
        if not avl.root:
            return snapshot
        
        # 使用改进的布局算法
        positions = AVLAdapter._layout_tree(
            avl.root, start_x, y, level_height, node_width, min_spacing)
        
        # 生成节点快照
        for node, (x, y_pos) in positions.items():
            node_id = f"node_{id(node)}"
            
            # 计算平衡因子
            balance_factor = avl._get_balance_factor(node)
            is_checking = (hasattr(avl, '_current_check_node_value') and 
                           avl._current_check_node_value is not None and 
                           str(avl._current_check_node_value) == str(node.value))
            
            # 检查是否是动画中的新节点
            is_new_node = (animation_state == 'inserting' and 
                          hasattr(avl, '_new_value') and 
                          str(avl._new_value) == str(node.value))
            
            # 检查是否是插入比较动画中的节点
            is_insert_comparing_node = (animation_state == 'inserting' and 
                                      hasattr(avl, '_current_search_node_value') and 
                                      str(avl._current_search_node_value) == str(node.value))
            
            # 检查是否是旋转动画中的节点
            is_rotating_node = (hasattr(avl, '_rotation_nodes') and 
                              node.value in avl._rotation_nodes)
            
            # 确定节点颜色和边框
            if is_new_node:
                node_color = "#FF6B6B"  # 红色表示正在插入的节点
                border_color = None
            elif is_insert_comparing_node:
                node_color = "#FFA500"  # 橙色表示正在比较的节点
                border_color = None
            elif abs(balance_factor) > 1:
                node_color = "#1f4e79"  # 深蓝色表示失衡节点
                border_color = "#FF6B6B"  # 红色边框表示失衡
            elif is_rotating_node:
                node_color = "#FFA500"  # 橙色表示参与旋转的节点
                border_color = "#FFA500"  # 橙色边框
            else:
                node_color = "#1f4e79"  # 深蓝色表示正常节点
                border_color = None
            
            # 处理旋转动画中的位置插值
            if is_rotating_node and hasattr(avl, '_rotation_type') and avl._rotation_type:
                # 根据旋转类型计算弧线轨迹
                current_x, current_y = AVLAdapter._calculate_rotation_position(
                    node, x, y_pos, avl._rotation_type, animation_progress)
            else:
                current_x, current_y = x, y_pos
            
            node_snapshot = NodeSnapshot(
                id=node_id,
                value=str(node.value),
                x=current_x - 30,  # 节点中心对齐
                y=current_y - 20,
                node_type="box",
                width=60,
                height=40,
                color=node_color
            )
            
            # 添加边框颜色属性（检查节点优先金色）
            if is_checking:
                node_snapshot.border_color = "#FFD700"
                node_snapshot.border_width = 3
            elif border_color:
                node_snapshot.border_color = border_color
                node_snapshot.border_width = 3
            
            snapshot.nodes.append(node_snapshot)
            
            # 添加平衡因子标签
            bf_text = f"平衡因子={balance_factor}"
            if is_checking:
                bf_text += "（检查中）"
            balance_label = BoxSnapshot(
                id=f"balance_{node_id}",
                value=bf_text,
                x=current_x + 50,  # 节点右侧
                y=current_y - 10,  # 节点上方
                width=120,  # 增加宽度以完整显示文字
                height=25,  # 增加高度以适应文字
                color="#8B4513" if abs(balance_factor) <= 1 else "#FF6B6B",  # 褐色正常，红色失衡
                text_color="#FFFFFF"
            )
            snapshot.boxes.append(balance_label)
        
        # 生成边快照
        AVLAdapter._add_edges(avl.root, positions, snapshot)
        
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
        root_arrow.to_y = y - 20
        snapshot.edges.append(root_arrow)
        
        return snapshot
    
    @staticmethod
    def _calculate_rotation_position(node, base_x, base_y, rotation_type, progress):
        """计算旋转动画中的节点位置"""
        if not hasattr(AVLAdapter, '_rotation_centers'):
            AVLAdapter._rotation_centers = {}
        
        # 根据旋转类型计算弧线轨迹
        if rotation_type == 'LL':
            # 右旋：左子节点上移，父节点下移
            if progress < 0.5:
                # 前半段：左子节点沿弧线上移
                angle = progress * 2 * 3.14159  # 0 到 π
                radius = 50
                offset_x = radius * (1 - abs(progress - 0.5) * 2)
                offset_y = -radius * abs(progress - 0.5) * 2
            else:
                # 后半段：父节点沿弧线下移
                angle = (progress - 0.5) * 2 * 3.14159  # 0 到 π
                radius = 50
                offset_x = -radius * (progress - 0.5) * 2
                offset_y = radius * (progress - 0.5) * 2
        elif rotation_type == 'RR':
            # 左旋：右子节点上移，父节点下移
            if progress < 0.5:
                # 前半段：右子节点沿弧线上移
                angle = progress * 2 * 3.14159
                radius = 50
                offset_x = -radius * (1 - abs(progress - 0.5) * 2)
                offset_y = -radius * abs(progress - 0.5) * 2
            else:
                # 后半段：父节点沿弧线下移
                angle = (progress - 0.5) * 2 * 3.14159
                radius = 50
                offset_x = radius * (progress - 0.5) * 2
                offset_y = radius * (progress - 0.5) * 2
        else:
            # LR 和 RL 类型使用更复杂的轨迹
            offset_x = 0
            offset_y = 0
        
        return base_x + offset_x, base_y + offset_y

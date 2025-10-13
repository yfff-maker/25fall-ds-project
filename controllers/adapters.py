# -*- coding: utf-8 -*-
"""
数据适配器：将数据结构状态转换为可视化快照
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

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
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
        if self.edges is None:
            self.edges = []
        if self.boxes is None:
            self.boxes = []

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
        
        # 生成节点和边快照
        current = linked_list.data.head  # 访问CustomList的head
        i = 0
        prev_node_id = None
        
        # 检查是否在插入动画中，需要调整后续节点位置
        insert_position = getattr(linked_list, '_insert_position', -1)
        is_inserting = animation_state == 'inserting'
        
        while current:
            node_id = f"node_{i}"
            
            # 计算节点位置
            if is_inserting and i > insert_position:
                # 插入动画中，后续节点需要向右移动
                node_x = start_x + (i + 1) * node_spacing
            else:
                # 正常位置
                node_x = start_x + i * node_spacing
            
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
                edge = EdgeSnapshot(
                    from_id=f"{prev_node_id}_box",
                    to_id=f"{node_id}_box",
                    arrow_type="arrow"
                )
                # 添加坐标信息用于渲染
                if is_inserting and i - 1 > insert_position:
                    # 前一个节点也向右移动了
                    edge.from_x = start_x + i * node_spacing + node_width
                else:
                    edge.from_x = start_x + (i - 1) * node_spacing + node_width
                edge.from_y = y + node_height // 2
                edge.to_x = node_x
                edge.to_y = y + node_height // 2
                snapshot.edges.append(edge)
            
            prev_node_id = node_id
            current = current.next  # CustomList使用next属性
            i += 1
        
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
                if animation_progress < 0.2:
                    # 新节点还在上方
                    new_x = start_x + insert_position * node_spacing
                    new_y = y - 100
                else:
                    # 新节点移动到目标位置
                    new_x = start_x + insert_position * node_spacing
                    new_y = y
                
                node_width = 80
                node_height = 40
                
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
                        edge.to_x = start_x + insert_position * node_spacing
                        edge.to_y = y + node_height // 2
                        snapshot.edges.append(edge)
                
                if animation_progress > 0.4:
                    # 第二阶段：断开原来的连接（不显示前驱到后继的连接）
                    pass
                
                if animation_progress > 0.6:
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
    def _calculate_subtree_width(node, node_width=60, min_spacing=20):
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
    def _layout_tree(node, center_x, y, level_height=80, node_width=60, min_spacing=20):
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
            # 设置连线坐标
            edge.from_x = node_x
            edge.from_y = node_y + 20
            edge.to_x = left_x
            edge.to_y = left_y - 20
            
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
            # 设置连线坐标
            edge.from_x = node_x
            edge.from_y = node_y + 20
            edge.to_x = right_x
            edge.to_y = right_y - 20
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            BinaryTreeAdapter._add_edges(node.right, positions, snapshot)
    
    @staticmethod
    def to_snapshot(binary_tree, start_x=400, y=100, level_height=80, node_width=60, min_spacing=20) -> StructureSnapshot:
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
        
        # 显示根指针
        root_pointer_x = start_x - 100
        root_pointer_y = y
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
            root_edge.from_x = root_pointer_x + 60
            root_edge.from_y = root_pointer_y + 15
            root_edge.to_x = start_x - 30
            root_edge.to_y = y
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
    def _calculate_subtree_width(node, node_width=60, min_spacing=20):
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
            subtree_total_width += min_spacing
        
        return max(node_width, subtree_total_width)
    
    @staticmethod
    def _layout_tree(node, center_x, y, level_height=80, node_width=60, min_spacing=20):
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
            total_child_width = left_width + right_width + min_spacing
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
            # 设置连线坐标
            edge.from_x = node_x
            edge.from_y = node_y + 20
            edge.to_x = left_x
            edge.to_y = left_y - 20
            
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
            # 设置连线坐标
            edge.from_x = node_x
            edge.from_y = node_y + 20
            edge.to_x = right_x
            edge.to_y = right_y - 20
            
            snapshot.edges.append(edge)
            
            # 递归处理右子树
            BSTAdapter._add_edges(node.right, positions, snapshot)
    
    @staticmethod
    def to_snapshot(bst, start_x=400, y=100, level_height=80, node_width=60, min_spacing=20) -> StructureSnapshot:
        """将BST转换为快照 - 使用与链式二叉树相同的布局算法"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"二叉搜索树 (节点数: {len(bst.traverse_inorder())})"
        
        if not bst.root:
            return snapshot
        
        # 使用改进的布局算法
        positions = BSTAdapter._layout_tree(
            bst.root, start_x, y, level_height, node_width, min_spacing)
        
        # 生成节点快照
        for node, (x, y_pos) in positions.items():
            node_id = f"node_{id(node)}"
            
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
        
        # 显示根指针
        root_pointer_x = start_x - 100
        root_pointer_y = y
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
        if bst.root:
            root_edge = EdgeSnapshot(
                from_id="root_pointer",
                to_id=f"node_{id(bst.root)}",
                arrow_type="arrow"
            )
            root_edge.from_x = root_pointer_x + 60
            root_edge.from_y = root_pointer_y + 15
            root_edge.to_x = start_x - 30
            root_edge.to_y = y
            snapshot.edges.append(root_edge)
        
        return snapshot

class HuffmanTreeAdapter:
    """哈夫曼树适配器 - 支持构建动画"""
    
    @staticmethod
    def to_snapshot(huffman_tree, start_x=400, y=100, level_height=120, node_spacing=200) -> StructureSnapshot:
        """将哈夫曼树转换为快照 - 支持构建动画"""
        snapshot = StructureSnapshot()
        
        # 获取动画状态
        animation_state = getattr(huffman_tree, '_animation_state', None)
        animation_progress = getattr(huffman_tree, '_animation_progress', 0.0)
        build_step = getattr(huffman_tree, '_build_step', 0)
        freq_map = getattr(huffman_tree, '_original_freq_map', {})
        
        if animation_state == 'building' and freq_map:
            # 显示构建动画
            snapshot = HuffmanTreeAdapter._create_building_animation_snapshot(
                huffman_tree, freq_map, build_step, animation_progress, start_x, y, level_height
            )
        elif huffman_tree.root:
            # 显示完整树
            snapshot = HuffmanTreeAdapter._create_complete_tree_snapshot(
                huffman_tree, start_x, y, level_height, node_spacing
            )
        else:
            # 显示初始状态
            snapshot.hint_text = "哈夫曼树 (点击构建开始)"
        
        return snapshot
    
    @staticmethod
    def _create_building_animation_snapshot(huffman_tree, freq_map, build_step, progress, start_x, y, level_height):
        """创建构建动画快照"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"哈夫曼树构建中... (步骤 {build_step})"
        
        # 显示初始节点（屏幕下方）
        initial_y = y + 200
        sorted_items = sorted(freq_map.items(), key=lambda x: x[1])
        
        for i, (char, freq) in enumerate(sorted_items):
            node_x = start_x - 200 + i * 100
            node_y = initial_y
            
            # 检查是否是当前步骤的节点
            is_highlighted = (build_step == 0 and i < 2) or (build_step > 0 and i < 2)
            
            if is_highlighted:
                # 高亮效果
                scale = 1.0 + 0.2 * progress
                color = "#FFD700"  # 金色高亮
            else:
                scale = 1.0
                color = "#FF6B6B"  # 红色叶子节点
            
            node_snapshot = NodeSnapshot(
                id=f"initial_{char}",
                value=f"{char}:{freq}",
                x=node_x,
                y=node_y,
                node_type="circle",
                color=color,
                width=int(40 * scale),
                height=int(40 * scale)
            )
            snapshot.nodes.append(node_snapshot)
        
        # 显示已构建的树结构
        if build_step > 0:
            HuffmanTreeAdapter._add_built_tree_nodes(huffman_tree, snapshot, start_x, y, level_height, build_step, progress)
        
        return snapshot
    
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
                        value=f"{node.char}:{node.freq}",
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
        """创建完整树的快照"""
        snapshot = StructureSnapshot()
        snapshot.hint_text = f"哈夫曼树 (编码数: {len(huffman_tree.get_codes())})"
        
        # 使用层序遍历获取所有节点
        queue = [(huffman_tree.root, start_x, y)]
        level = 0
        
        while queue:
            next_queue = []
            level_width = node_spacing * (2 ** level)
            
            for i, (node, x, current_y) in enumerate(queue):
                node_id = f"node_{id(node)}"
                
                # 计算节点位置
                if len(queue) > 1:
                    node_x = x - level_width/2 + i * (level_width / (len(queue) - 1))
                else:
                    node_x = x
                
                # 创建节点快照
                if node.char is not None:
                    # 叶子节点
                    node_snapshot = NodeSnapshot(
                        id=node_id,
                        value=f"{node.char}:{node.freq}",
                        x=node_x,
                        y=current_y,
                        node_type="circle",
                        color="#FF6B6B"  # 红色表示叶子节点
                    )
                else:
                    # 内部节点
                    node_snapshot = NodeSnapshot(
                        id=node_id,
                        value=str(node.freq),
                        x=node_x,
                        y=current_y,
                        node_type="circle",
                        color="#4C78A8"  # 蓝色表示内部节点
                    )
                
                snapshot.nodes.append(node_snapshot)
                
                # 添加子节点到下一层
                if node.left:
                    next_queue.append((node.left, node_x, current_y + level_height))
                if node.right:
                    next_queue.append((node.right, node_x, current_y + level_height))
            
            queue = next_queue
            level += 1
        
        # 添加边
        HuffmanTreeAdapter._add_edges(huffman_tree.root, snapshot, start_x, y, level_height, node_spacing)
        
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

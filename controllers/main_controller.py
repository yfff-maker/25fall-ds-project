# -*- coding: utf-8 -*-
"""
主控制器：协调Model、View和用户交互
"""
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtCore import QObject, pyqtSignal

from structures.sequential_list import SequentialListModel
from structures.linked_list import LinkedListModel
from structures.stack import StackModel
from structures.binary_tree import BinaryTreeModel
from structures.bst import BSTModel
from structures.huffman import HuffmanTreeModel
from .adapters import (
    SequentialListAdapter, LinkedListAdapter, StackAdapter,
    BinaryTreeAdapter, BSTAdapter, HuffmanTreeAdapter,
    StructureSnapshot
)

class MainController(QObject):
    """主控制器类"""
    
    # 信号定义
    snapshot_updated = pyqtSignal(object)  # 快照更新信号
    hint_updated = pyqtSignal(str)  # 提示更新信号
    
    def __init__(self):
        super().__init__()
        
        # 初始化数据结构模型
        self.structures = {
            "SequentialList": SequentialListModel(),
            "LinkedList": LinkedListModel(),
            "Stack": StackModel(),
            "BinaryTree": BinaryTreeModel(),
            "BST": BSTModel(),
            "HuffmanTree": HuffmanTreeModel(),
        }
        
        # 激活所有数据结构
        for structure in self.structures.values():
            structure.set_active(True)
        
        # 适配器映射
        self.adapters = {
            "SequentialList": SequentialListAdapter(),
            "LinkedList": LinkedListAdapter(),
            "Stack": StackAdapter(),
            "BinaryTree": BinaryTreeAdapter(),
            "BST": BSTAdapter(),
            "HuffmanTree": HuffmanTreeAdapter(),
        }
        
        self.current_structure_key = "SequentialList"
        self._update_snapshot()
    
    def select_structure(self, key: str):
        """选择数据结构"""
        if key in self.structures:
            self.current_structure_key = key
            self._update_snapshot()
            self.hint_updated.emit(f"当前模式：{key}")
    
    def _update_snapshot(self):
        """更新当前快照"""
        if self.current_structure_key in self.structures:
            structure = self.structures[self.current_structure_key]
            adapter = self.adapters[self.current_structure_key]
            snapshot = adapter.to_snapshot(structure) # ← 创建：通过适配器创建 StructureSnapshot
            self.snapshot_updated.emit(snapshot)
    
    def _get_current_structure(self):
        """获取当前数据结构"""
        return self.structures.get(self.current_structure_key) # ← 依赖：使用数据结构实例
    
    def _get_current_adapter(self):
        """获取当前适配器"""
        return self.adapters.get(self.current_structure_key)
    
    # ========== 顺序表操作 ==========
    
    def build_sequential_list(self, input_text: str):
        """构建顺序表"""
        try:
            data = self._parse_comma_separated_values(input_text)
            structure = self._get_current_structure()
            if structure:
                structure.build(data)
                self._update_snapshot()
        except Exception as e:
            self._show_error("构建顺序表失败", str(e))
    
    def insert_at_sequential_list(self, position: int, value: str):
        """在指定位置插入元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 开始插入动画
                structure.insert_at(position, value)
                self._update_snapshot()
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                
                # 创建动画定时器
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_sequential_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次，实现平滑效果
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("插入失败", str(e))
    
    def delete_at_sequential_list(self, position: int):
        """删除指定位置的元素"""
        try:
            structure = self._get_current_structure()
            if structure:
                # 开始删除动画
                structure.delete_at(position)
                self._update_snapshot()
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                
                # 创建动画定时器
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_sequential_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次，实现平滑效果
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("删除失败", str(e))
    
    def insert_at_head_sequential_list(self, value: str):
        """在头部插入元素"""
        self.insert_at_sequential_list(0, value)
    
    def insert_at_tail_sequential_list(self, value: str):
        """在尾部插入元素"""
        self.insert_at_sequential_list(len(self._get_current_structure().data), value)
    
    def _update_sequential_animation(self, structure):
        """更新顺序表平滑动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = min(elapsed / self._animation_duration, 1.0)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            # 根据动画状态完成相应操作
            if structure._animation_state == 'inserting':
                structure.complete_insert_animation()
            elif structure._animation_state == 'deleting':
                structure.complete_delete_animation()
            self._update_snapshot()
            self._animation_timer.deleteLater()
    
    # ========== 链表操作 ==========
    
    def build_linked_list(self, input_text: str):
        """构建链表"""
        try:
            data_generator = self._parse_comma_separated_values(input_text)
            structure = self._get_current_structure()
            if structure:
                # 开始构建动画
                structure.build(data_generator)
                self._update_snapshot()
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                
                # 创建动画定时器
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_linked_list_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次，实现平滑效果
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
        except Exception as e:
            self._show_error("构建链表失败", str(e))
    
    def insert_at_linked_list(self, position: int, value: str):
        """在指定位置插入元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 开始插入动画
                structure.insert(position, value)
                self._update_snapshot()
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                
                # 创建动画定时器
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_linked_list_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次，实现平滑效果
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
        except Exception as e:
            self._show_error("插入失败", str(e))
    
    def delete_at_linked_list(self, position: int):
        """删除指定位置的元素"""
        try:
            structure = self._get_current_structure()
            if structure:
                structure.delete_at(position)
                self._update_snapshot()
        except Exception as e:
            self._show_error("删除失败", str(e))
    
    def insert_at_head_linked_list(self, value: str):
        """在头部插入元素"""
        self.insert_at_linked_list(0, value)
    
    def insert_at_tail_linked_list(self, value: str):
        """在尾部插入元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                structure.insert_at_end(value)
                self._update_snapshot()
        except Exception as e:
            self._show_error("尾部插入失败", str(e))
    
    def delete_by_value_linked_list(self, value: str):
        """按值删除元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                structure.delete_by_value(value)
                self._update_snapshot()
        except Exception as e:
            self._show_error("按值删除失败", str(e))
    
    # ========== 栈操作 ==========
    
    def push_stack(self, value: str):
        """入栈"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 开始入栈动画
                structure.push(value)
                self._update_snapshot()
                
                # 检查是否是栈满状态
                if getattr(structure, '_animation_state', None) == 'stack_full':
                    self._show_error("栈已满！", "无法添加更多元素，栈容量为10")
                    return
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                
                # 创建动画定时器
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_smooth_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次，实现平滑效果
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("入栈失败", str(e))
    
    def _update_smooth_animation(self, structure):
        """更新平滑动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = min(elapsed / self._animation_duration, 1.0)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            if structure._animation_state == 'pushing':
                structure.complete_push_animation()
            elif structure._animation_state == 'popping':
                structure.complete_pop_animation()
            self._update_snapshot()
            self._animation_timer.deleteLater()
    
    def _update_stack_animation(self, structure):
        """更新栈动画（入栈和出栈）"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = min(elapsed / self._animation_duration, 1.0)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            if structure._animation_state == 'pushing':
                structure.complete_push_animation()
            elif structure._animation_state == 'popping':
                structure.complete_pop_animation()
            self._update_snapshot()
            self._animation_timer.deleteLater()
    
    def _update_binary_tree_animation(self, structure):
        """更新二叉树动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = min(elapsed / self._animation_duration, 1.0)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            if structure._animation_state == 'creating_root':
                # 创建根节点
                structure.root = structure.Node(structure._new_value)
                structure._animation_state = None
                structure._animation_progress = 0.0
                structure._new_value = None
            elif structure._animation_state == 'inserting':
                # 插入新节点
                if structure._parent_value and structure._insert_position:
                    parent_node = structure.find_node_by_value(structure._parent_value)
                    if parent_node:
                        new_node = structure.Node(structure._new_value)
                        if structure._insert_position == 'left':
                            parent_node.left = new_node
                        else:  # right
                            parent_node.right = new_node
                
                structure._animation_state = None
                structure._animation_progress = 0.0
                structure._new_value = None
                structure._parent_value = None
                structure._insert_position = None
            
            # 最终更新显示
            self._update_snapshot()
            self._animation_timer.deleteLater()
    
    def pop_stack(self):
        """出栈"""
        try:
            structure = self._get_current_structure()
            if structure:
                # 开始出栈动画
                structure.pop()
                self._update_snapshot()
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                
                # 创建动画定时器
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_stack_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次，实现平滑效果
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("出栈失败", str(e))
    
    def clear_stack(self):
        """清空栈"""
        try:
            structure = self._get_current_structure()
            if structure:
                structure.clear()
                self._update_snapshot()
        except Exception as e:
            self._show_error("清空栈失败", str(e))
    
    def build_stack(self, input_text: str):
        """构建栈"""
        try:
            data = self._parse_comma_separated_values(input_text)
            structure = self._get_current_structure()
            if structure:
                # 开始构建动画
                structure.build(data)
                self._update_snapshot()
                
                # 检查是否是栈满状态
                if getattr(structure, '_animation_state', None) == 'stack_full':
                    self._show_error("栈已满！", "无法添加更多元素，栈容量为10")
                    return
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                
                # 创建动画定时器
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_stack_build_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次，实现平滑效果
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("构建栈失败", str(e))
    
    def _update_stack_build_animation(self, structure):
        """更新栈构建动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = min(elapsed / self._animation_duration, 1.0)
        structure.update_animation_progress(progress)
        
        # 处理构建动画的逐步显示
        if structure._animation_state == 'building':
            build_values = getattr(structure, '_build_values', [])
            total_elements = len(build_values)
            if total_elements > 0:
                # 计算当前应该显示到第几个元素
                current_element_index = int(progress * total_elements)
                structure._build_index = current_element_index
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            if structure._animation_state == 'building':
                structure.complete_build_animation()
            self._update_snapshot()
            self._animation_timer.deleteLater()
    
    # ========== 二叉树操作 ==========
    
    def insert_binary_tree_node(self, value: str, parent_value: str = None):
        """插入二叉树节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if not structure:
                return
            
            # 如果没有根节点，自动创建
            if structure.root is None:
                # 开始创建根节点动画
                structure._animation_state = 'creating_root'
                structure._animation_progress = 0.0
                structure._new_value = value
                structure._new_node = None  # 根节点还没有创建
                
                # 使用定时器实现平滑动画
                from PyQt5.QtCore import QTimer
                self._animation_timer = QTimer()
                self._animation_timer.timeout.connect(lambda: self._update_binary_tree_animation(structure))
                self._animation_timer.start(50)  # 每50ms更新一次
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
                self._update_snapshot()
                return
            
            # 如果有父节点值，开始插入动画
            if parent_value:
                # 确定插入位置（左孩子优先）
                parent_node = structure.find_node_by_value(parent_value)
                if parent_node:
                    if parent_node.left is None:
                        position = 'left'
                    elif parent_node.right is None:
                        position = 'right'
                    else:
                        self._show_warning(f"节点 {parent_value} 已有两个孩子，无法继续添加")
                        return
                    
                    # 开始插入动画
                    structure.start_insert_animation(value, parent_value, position)
                    
                    # 使用定时器实现平滑动画
                    from PyQt5.QtCore import QTimer
                    self._animation_timer = QTimer()
                    self._animation_timer.timeout.connect(lambda: self._update_binary_tree_animation(structure))
                    self._animation_timer.start(50)  # 每50ms更新一次
                    
                    # 设置动画总时长
                    self._animation_duration = 1000  # 1秒总时长
                    self._animation_start_time = 0
                    
                    self._update_snapshot()
            else:
                # 需要用户选择父节点
                self._request_parent_selection(value)
                
        except Exception as e:
            self._show_error("插入节点失败", str(e))
    
    def traverse_binary_tree(self, order: str):
        """遍历二叉树"""
        try:
            structure = self._get_current_structure()
            if structure:
                structure.traverse(order)
                self._update_snapshot()
        except Exception as e:
            self._show_error("遍历失败", str(e))
    
    def _request_parent_selection(self, value: str):
        """请求父节点选择（需要UI支持）"""
        # 这个方法需要与UI层交互，暂时抛出信号
        self.parent_selection_requested.emit(value)
    
    # ========== BST操作 ==========
    
    def insert_bst(self, value: str):
        """插入BST节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if structure:
                structure.insert(value)
                self._update_snapshot()
        except Exception as e:
            self._show_error("插入失败", str(e))
    
    def search_bst(self, value: str):
        """搜索BST节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if structure:
                result = structure.search(value)
                if result:
                    self.hint_updated.emit(f"找到节点: {value}")
                else:
                    self.hint_updated.emit(f"未找到节点: {value}")
                self._update_snapshot()
        except Exception as e:
            self._show_error("搜索失败", str(e))
    
    def delete_bst(self, value: str):
        """删除BST节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if structure:
                structure.delete(value)
                self._update_snapshot()
        except Exception as e:
            self._show_error("删除失败", str(e))
    
    # ========== 哈夫曼树操作 ==========
    
    def build_huffman_tree(self, freq_text: str):
        """构建哈夫曼树"""
        try:
            freq_dict = self._parse_frequency_mapping(freq_text)
            structure = self._get_current_structure()
            if structure:
                structure.build(freq_dict)
                self._update_snapshot()
        except Exception as e:
            self._show_error("构建哈夫曼树失败", str(e))
    
    # ========== 工具方法 ==========
    
    def _parse_comma_separated_values(self, text: str):
        """解析逗号分隔的值"""
        if not text.strip():
            return []
        
        # 使用生成器避免创建list
        for s in text.split(","):
            s = s.strip()
            if s:
                yield s
    
    def _parse_frequency_mapping(self, text: str) -> dict:
        """解析频率映射"""
        freq = {}
        if text.strip():
            for pair in text.split(","):
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    try:
                        freq[k.strip()] = int(v.strip())
                    except ValueError:
                        pass
        return freq
    
    def _update_linked_list_animation(self, structure):
        """更新链表平滑动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = min(elapsed / self._animation_duration, 1.0)
        structure.update_animation_progress(progress)
        
        # 处理构建动画的逐步显示
        if structure._animation_state == 'building':
            build_values = getattr(structure, '_build_values', [])
            total_nodes = len(build_values)
            if total_nodes > 0:
                # 计算当前应该显示到第几个节点
                current_node_index = int(progress * total_nodes)
                structure._build_index = current_node_index
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            if structure._animation_state == 'building':
                structure.complete_build_animation()
            elif structure._animation_state == 'inserting':
                structure.complete_insert_animation()
            self._update_snapshot()
            self._animation_timer.deleteLater()
    
    def _show_warning(self, message: str):
        """显示警告消息"""
        # 这里应该通过信号发送到UI层
        self.hint_updated.emit(f"警告: {message}")
    
    def _show_error(self, title: str, message: str):
        """显示错误消息"""
        # 这里应该通过信号发送到UI层
        self.hint_updated.emit(f"错误: {title} - {message}")
    
    # 信号定义（用于UI交互）
    parent_selection_requested = pyqtSignal(str)  # 请求父节点选择

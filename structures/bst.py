# -*- coding: utf-8 -*-
"""
二叉搜索树数据结构：纯业务逻辑实现
"""
from .base import BaseStructure

class BSTModel(BaseStructure):
    """二叉搜索树模型类"""
    
    class Node:
        def __init__(self, value, left=None, right=None):
            self.value = value
            self.left = left
            self.right = right

    def __init__(self):
        super().__init__()
        self.root = None
        
        # 动画相关属性
        self._animation_state = None  # 动画状态：None, 'creating_root', 'inserting', 'searching', 'search_found', 'search_not_found'
        self._animation_progress = 0.0  # 动画进度：0.0-1.0
        self._new_node = None  # 新节点引用
        self._new_value = None  # 新节点值
        self._parent_value = None  # 父节点值
        self._insert_position = None  # 插入位置：'left' 或 'right'
        self._start_x = 0  # 动画起始x坐标
        self._start_y = 0  # 动画起始y坐标
        self._target_x = 0  # 动画目标x坐标
        self._target_y = 0  # 动画目标y坐标
        
        # 查找动画相关属性
        self._search_value = None  # 要查找的值
        self._current_search_node_value = None  # 当前正在比较的节点值
        self._comparison_result = None  # 比较结果：'less', 'greater', 'equal'
        self._search_result_node_value = None  # 找到的节点值（成功时）
        self._last_search_node_value = None  # 最后访问的节点值（失败时）
        self._search_path = []  # 查找路径（节点值列表）
        self._current_search_step = 0  # 当前查找步骤

    def insert(self, value):
        """插入节点到BST"""
        if not self.active or value is None:
            return
        
        try:
            v = float(value)
        except:
            v = value
        
        if self.root is None:
            # 创建根节点 - 设置动画状态
            self._animation_state = 'creating_root'
            self._new_value = v
            self._animation_progress = 0.0
            # 不立即创建节点，等动画完成后再创建
        else:
            # 插入到现有树中 - 需要找到父节点和插入位置
            parent_node, position = self._find_insert_position(self.root, v)
            if parent_node:
                self._animation_state = 'inserting'
                self._new_value = v
                self._parent_value = parent_node.value
                self._insert_position = position
                self._animation_progress = 0.0
                # 不立即插入，等动画完成后再插入
            else:
                # 值已存在，直接返回
                return
    
    def _find_insert_position(self, node, value):
        """找到插入位置和父节点"""
        if value < node.value:
            if node.left is None:
                return node, 'left'
            else:
                return self._find_insert_position(node.left, value)
        elif value > node.value:
            if node.right is None:
                return node, 'right'
            else:
                return self._find_insert_position(node.right, value)
        else:
            # 值已存在
            return None, None

    def _insert_node(self, node, value):
        """递归插入节点"""
        if value < node.value:
            if node.left:
                self._insert_node(node.left, value)
            else:
                # 创建左孩子
                node.left = BSTModel.Node(value)
        elif value > node.value:
            if node.right:
                self._insert_node(node.right, value)
            else:
                # 创建右孩子
                node.right = BSTModel.Node(value)

    def search(self, value):
        """搜索节点"""
        if not self.active or value is None or self.root is None:
            return False
        
        try:
            v = float(value)
        except:
            v = value

        return self._search_node(self.root, v)

    def _search_node(self, node, value):
        """递归搜索节点"""
        if not node:
            return False
        
        if value == node.value:
            return True
        elif value < node.value:
            return self._search_node(node.left, value)
        else:
            return self._search_node(node.right, value)

    def delete(self, value):
        """删除节点"""
        if not self.active or value is None or self.root is None:
            return
        
        try:
            v = float(value)
        except:
            v = value
        
        self.root = self._delete_node(self.root, v)

    def _delete_node(self, node, value):
        """递归删除节点"""
        if not node:
            return node
        
        if value < node.value:
            node.left = self._delete_node(node.left, value)
        elif value > node.value:
            node.right = self._delete_node(node.right, value)
        else:
            # 找到要删除的节点
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            
            # 节点有两个子节点，找到右子树的最小值
            min_node = self._find_min(node.right)
            node.value = min_node.value
            node.right = self._delete_node(node.right, min_node.value)
        
        return node

    def _find_min(self, node):
        """找到子树中的最小节点"""
        while node.left:
            node = node.left
        return node

    def _count_nodes(self, node):
        """计算节点数量"""
        if not node:
            return 0
        return 1 + self._count_nodes(node.left) + self._count_nodes(node.right)

    def get_height(self):
        """获取树的高度"""
        return self._get_height(self.root)

    def _get_height(self, node):
        """递归计算树的高度"""
        if not node:
            return 0
        return 1 + max(self._get_height(node.left), self._get_height(node.right))

    def is_empty(self):
        """判断树是否为空"""
        return self.root is None

    def clear(self):
        """清空树"""
        self.root = None

    def traverse_inorder(self):
        """中序遍历"""
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        """递归中序遍历"""
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)
    
    def find_node_by_value(self, value):
        """根据值查找节点"""
        return self._find_node(self.root, value)
    
    def _find_node(self, node, value):
        """递归查找节点"""
        if not node:
            return None
        if node.value == value:
            return node
        elif value < node.value:
            return self._find_node(node.left, value)
        else:
            return self._find_node(node.right, value)
    
    def start_insert_animation(self, value, parent_value, position):
        """开始插入动画"""
        if not self.active or value is None:
            return
        
        self._animation_state = 'inserting'
        self._new_value = value
        self._parent_value = parent_value
        self._insert_position = position
        self._animation_progress = 0.0
    
    def complete_insert_animation(self):
        """完成插入节点动画"""
        if self._animation_state == 'creating_root' and self._new_value is not None:
            # 创建根节点
            self.root = BSTModel.Node(self._new_value)
            self._animation_state = None
            self._new_value = None
            self._animation_progress = 0.0
        elif self._animation_state == 'inserting' and self._new_value is not None:
            # 执行实际的插入操作
            self._insert_node(self.root, self._new_value)
            
            self._animation_state = None
            self._new_value = None
            self._parent_value = None
            self._insert_position = None
            self._animation_progress = 0.0
    
    def cancel_animation(self):
        """取消动画"""
        self._animation_state = None
        self._new_value = None
        self._parent_value = None
        self._insert_position = None
        self._animation_progress = 0.0
    
    def update_animation_progress(self, progress):
        """更新动画进度"""
        self._animation_progress = max(0.0, min(1.0, progress))
    
    def set_animation_target(self, target_x, target_y):
        """设置动画目标位置"""
        self._target_x = target_x
        self._target_y = target_y
    
    def search_with_animation(self, value):
        """带动画的查找方法"""
        if not self.active or value is None or self.root is None:
            return False
        
        try:
            v = float(value)
        except:
            v = value
        
        # 初始化查找动画状态
        self._animation_state = 'searching'
        self._search_value = v
        self._current_search_node_value = None
        self._comparison_result = None
        self._search_result_node_value = None
        self._last_search_node_value = None
        self._search_path = []
        self._current_search_step = 0
        self._animation_progress = 0.0
        
        # 预计算查找路径
        self._search_path = self._calculate_search_path(self.root, v)
        
        return True
    
    def _calculate_search_path(self, node, value):
        """计算查找路径"""
        path = []
        current = node
        
        while current:
            path.append(current.value)
            if value < current.value:
                current = current.left
            elif value > current.value:
                current = current.right
            else:
                break  # 找到目标
        
        return path
    
    def update_search_animation(self, progress):
        """更新查找动画进度"""
        if self._animation_state != 'searching':
            return
        
        self._animation_progress = max(0.0, min(1.0, progress))
        
        # 根据进度计算当前步骤
        total_steps = len(self._search_path)
        if total_steps == 0:
            return
        
        # 计算当前步骤（基于进度）
        current_step = int(self._animation_progress * total_steps)
        current_step = min(current_step, total_steps - 1)
        
        if current_step < len(self._search_path):
            self._current_search_step = current_step
            self._current_search_node_value = self._search_path[current_step]
            
            # 计算比较结果
            if self._search_value < self._current_search_node_value:
                self._comparison_result = 'less'
            elif self._search_value > self._current_search_node_value:
                self._comparison_result = 'greater'
            else:
                self._comparison_result = 'equal'
                # 找到目标
                self._animation_state = 'search_found'
                self._search_result_node_value = self._current_search_node_value
                return
        
        # 检查是否到达路径末尾（未找到）
        if self._animation_progress >= 1.0 and self._comparison_result != 'equal':
            self._animation_state = 'search_not_found'
            self._last_search_node_value = self._search_path[-1] if self._search_path else None
    
    def complete_search_animation(self):
        """完成查找动画"""
        if self._animation_state in ['search_found', 'search_not_found']:
            # 保持最终状态，不重置
            pass
        else:
            # 如果动画被中断，重置状态
            self._animation_state = None
            self._search_value = None
            self._current_search_node_value = None
            self._comparison_result = None
            self._search_result_node_value = None
            self._last_search_node_value = None
            self._search_path = []
            self._current_search_step = 0
            self._animation_progress = 0.0
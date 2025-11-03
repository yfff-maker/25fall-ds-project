# -*- coding: utf-8 -*-
"""
二叉树数据结构：纯业务逻辑实现
"""
from .base import BaseStructure

class BinaryTreeModel(BaseStructure):
    """二叉树模型类"""
    
    class Node:
        def __init__(self, value, left=None, right=None):
            self.value = value
            self.left = left
            self.right = right

    def __init__(self):
        super().__init__()
        self.root = None
        
        # 动画相关属性
        self._animation_state = None  # 动画状态：None, 'creating_root', 'inserting'
        self._animation_progress = 0.0  # 动画进度：0.0-1.0
        self._new_node = None  # 新节点引用
        self._new_value = None  # 新节点值
        self._parent_value = None  # 父节点值
        self._insert_position = None  # 插入位置：'left' 或 'right'
        self._start_x = 0  # 动画起始x坐标
        self._start_y = 0  # 动画起始y坐标
        self._target_x = 0  # 动画目标x坐标
        self._target_y = 0  # 动画目标y坐标

    def create_root_node(self, value):
        """创建根节点"""
        if not self.active or value is None:
            return
            
        # 直接创建根节点
        self.root = BinaryTreeModel.Node(value)

    def get_all_node_values(self):
        """获取所有节点的值"""
        values = []
        self._collect_values(self.root, values)
        return values

    def _collect_values(self, node, values):
        """递归收集节点值"""
        if node:
            values.append(node.value)
            self._collect_values(node.left, values)
            self._collect_values(node.right, values)

    def find_node_by_value(self, value):
        """根据值查找节点"""
        return self._find_node(self.root, value)

    def _find_node(self, node, value):
        """递归查找节点"""
        if not node:
            return None
        if str(node.value) == str(value):
            return node
        
        left_result = self._find_node(node.left, value)
        if left_result:
            return left_result
        
        return self._find_node(node.right, value)
    
    def find_parent_node(self, target_value):
        """查找目标节点的父节点"""
        if not self.root:
            return None
        if str(self.root.value) == str(target_value):
            return None  # 根节点没有父节点
        
        return self._find_parent(self.root, target_value)
    
    def _find_parent(self, node, target_value):
        """递归查找父节点"""
        if not node:
            return None
        
        # 检查左子节点
        if node.left and str(node.left.value) == str(target_value):
            return node, 'left'
        
        # 检查右子节点
        if node.right and str(node.right.value) == str(target_value):
            return node, 'right'
        
        # 递归查找左子树
        left_result = self._find_parent(node.left, target_value)
        if left_result:
            return left_result
        
        # 递归查找右子树
        return self._find_parent(node.right, target_value)
    
    def delete_node(self, value):
        """删除节点及其所有子树"""
        if not self.active or value is None:
            return False
        
        # 如果要删除的是根节点
        if self.root and str(self.root.value) == str(value):
            self.root = None
            return True
        
        # 查找父节点
        parent_info = self.find_parent_node(value)
        if not parent_info:
            return False  # 节点不存在
        
        parent_node, position = parent_info
        
        # 删除节点
        if position == 'left':
            parent_node.left = None
        else:  # position == 'right'
            parent_node.right = None
        
        return True

    def insert_node(self, value, parent_value):
        """插入新节点到指定父节点"""
        if not self.active or value is None or parent_value is None:
            return
        
        parent_node = self.find_node_by_value(parent_value)
        if not parent_node:
            return
        
        # 确定插入位置（左孩子优先）
        if parent_node.left is None:
            # 插入左孩子
            parent_node.left = BinaryTreeModel.Node(value)
        elif parent_node.right is None:
            # 插入右孩子
            parent_node.right = BinaryTreeModel.Node(value)
        else:
            # 父节点已有两个孩子，无法继续添加
            raise ValueError(f"节点 {parent_value} 已有两个孩子，无法继续添加")

    def traverse(self, method: str):
        """遍历二叉树"""
        result = []
        
        def pre(node):
            if not node: return
            result.append(node.value)
            pre(node.left)
            pre(node.right)

        def ino(node):
            if not node: return
            ino(node.left)
            result.append(node.value)
            ino(node.right)

        def post(node):
            if not node: return
            post(node.left)
            post(node.right)
            result.append(node.value)

        if method == "pre": 
            pre(self.root)
        elif method == "in": 
            ino(self.root)
        elif method == "post": 
            post(self.root)
        
        return result

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
    
    def update_animation_progress(self, progress):
        """更新动画进度"""
        self._animation_progress = progress
    
    def start_insert_animation(self, value, parent_value, position):
        """开始插入动画"""
        self._animation_state = 'inserting'
        self._animation_progress = 0.0
        self._new_value = value
        self._parent_value = parent_value
        self._insert_position = position
    
    def complete_insert_animation(self):
        """完成插入动画"""
        if self._animation_state == 'inserting':
            # 实际执行插入操作
            if self._parent_value and self._insert_position:
                self.insert_node(self._new_value, self._parent_value)
            
            # 重置动画状态
            self._animation_state = None
            self._animation_progress = 0.0
            self._new_value = None
            self._parent_value = None
            self._insert_position = None
            self._new_node = None
    
    def complete_create_root_animation(self):
        """完成创建根节点动画"""
        if self._animation_state == 'creating_root' and self._new_value is not None:
            self.root = BinaryTreeModel.Node(self._new_value)
            self._animation_state = None
            self._new_value = None
            self._animation_progress = 0.0
    
    def complete_insert_animation(self):
        """完成插入节点动画"""
        if self._animation_state == 'inserting' and self._new_value is not None and self._parent_value is not None:
            parent_node = self.find_node_by_value(self._parent_value)
            if parent_node:
                if self._insert_position == 'left':
                    parent_node.left = BinaryTreeModel.Node(self._new_value)
                elif self._insert_position == 'right':
                    parent_node.right = BinaryTreeModel.Node(self._new_value)
            
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

    # ===== 序列化 =====
    def _node_to_dict(self, node):
        if node is None:
            return None
        return {
            "value": node.value,
            "left": self._node_to_dict(node.left),
            "right": self._node_to_dict(node.right),
        }

    def _dict_to_node(self, data):
        if not data:
            return None
        node = BinaryTreeModel.Node(data.get("value"))
        node.left = self._dict_to_node(data.get("left"))
        node.right = self._dict_to_node(data.get("right"))
        return node

    def to_dict(self) -> dict:
        return {
            "root": self._node_to_dict(self.root)
        }

    def from_dict(self, data: dict) -> None:
        self.root = self._dict_to_node(data.get("root"))
        # 清理动画状态
        self._animation_state = None
        self._animation_progress = 0.0
        self._new_node = None
        self._new_value = None
        self._parent_value = None
        self._insert_position = None
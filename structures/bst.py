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

    def insert(self, value):
        """插入节点到BST"""
        if not self.active or value is None:
            return
        
        try:
            v = float(value)
        except:
            v = value
        
        if self.root is None:
            # 创建根节点
            self.root = BSTModel.Node(v)
        else:
            # 插入到现有树中
            self._insert_node(self.root, v)

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
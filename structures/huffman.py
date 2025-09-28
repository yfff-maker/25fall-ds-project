# -*- coding: utf-8 -*-
"""
哈夫曼树数据结构：纯业务逻辑实现
"""
from .base import BaseStructure

class HuffmanTreeModel(BaseStructure):
    """哈夫曼树模型类"""
    
    class Node:
        def __init__(self, freq, char=None, left=None, right=None):
            self.freq = freq
            self.char = char
            self.left = left
            self.right = right

    class MinHeap:
        """最小堆实现"""
        def __init__(self):
            self.heap = []
        
        def push(self, item):
            self.heap.append(item)
            self._bubble_up(len(self.heap) - 1)
        
        def pop(self):
            if not self.heap:
                return None
            if len(self.heap) == 1:
                return self.heap.pop()
            
            min_item = self.heap[0]
            self.heap[0] = self.heap.pop()
            self._bubble_down(0)
            return min_item
        
        def _bubble_up(self, index):
            while index > 0:
                parent = (index - 1) // 2
                if self.heap[index].freq < self.heap[parent].freq:
                    self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
                    index = parent
                else:
                    break
        
        def _bubble_down(self, index):
            while True:
                left_child = 2 * index + 1
                right_child = 2 * index + 2
                smallest = index
                
                if left_child < len(self.heap) and self.heap[left_child].freq < self.heap[smallest].freq:
                    smallest = left_child
                
                if right_child < len(self.heap) and self.heap[right_child].freq < self.heap[smallest].freq:
                    smallest = right_child
                
                if smallest == index:
                    break
                
                self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
                index = smallest
        
        def is_empty(self):
            return len(self.heap) == 0
        
        def __len__(self):
            return len(self.heap)

    def __init__(self):
        super().__init__()
        self.root = None

    def build(self, freq_map):
        """构建哈夫曼树"""
        if not self.active or not freq_map:
            return
        
        # 使用最小堆
        heap = self.MinHeap()
        
        # 将所有字符和频率插入堆
        for char, freq in freq_map.items():
            node = HuffmanTreeModel.Node(freq, char=char)
            heap.push(node)

        # 构建哈夫曼树
        while len(heap) > 1:
            # 弹出两个最小元素
            left = heap.pop()
            right = heap.pop()
            
            # 创建父节点
            parent = HuffmanTreeModel.Node(left.freq + right.freq)
            parent.left = left
            parent.right = right
            
            # 将父节点插入堆
            heap.push(parent)
        
        # 设置根节点
        if not heap.is_empty():
            self.root = heap.pop()

    def get_codes(self):
        """获取哈夫曼编码"""
        if not self.root:
            return {}
        
        codes = {}
        self._generate_codes(self.root, "", codes)
        return codes

    def _generate_codes(self, node, code, codes):
        """递归生成哈夫曼编码"""
        if node.char is not None:
            # 叶子节点
            codes[node.char] = code if code else "0"
        else:
            # 内部节点
            if node.left:
                self._generate_codes(node.left, code + "0", codes)
            if node.right:
                self._generate_codes(node.right, code + "1", codes)

    def encode(self, text):
        """编码文本"""
        codes = self.get_codes()
        encoded = ""
        for char in text:
            if char in codes:
                encoded += codes[char]
            else:
                raise ValueError(f"字符 '{char}' 不在哈夫曼树中")
        return encoded

    def decode(self, encoded_text):
        """解码文本"""
        if not self.root:
            return ""
        
        result = ""
        current = self.root
        
        for bit in encoded_text:
            if bit == "0":
                current = current.left
            else:
                current = current.right
            
            if current.char is not None:
                result += current.char
                current = self.root
        
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
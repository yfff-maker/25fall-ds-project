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

    class FixedArray:
        """固定大小数组，替代Python list"""
        def __init__(self, capacity=1000):
            self.capacity = capacity
            self.data = [None] * capacity  # 只在初始化时使用list
            self.size = 0
        
        def append(self, item):
            if self.size < self.capacity:
                self.data[self.size] = item
                self.size += 1
                return True
            return False
        
        def get(self, index):
            if 0 <= index < self.size:
                return self.data[index]
            return None
        
        def set(self, index, item):
            if 0 <= index < self.size:
                self.data[index] = item
                return True
            return False
        
        def swap(self, i, j):
            if 0 <= i < self.size and 0 <= j < self.size:
                self.data[i], self.data[j] = self.data[j], self.data[i]
        
        def pop_last(self):
            if self.size > 0:
                self.size -= 1
                item = self.data[self.size]
                self.data[self.size] = None
                return item
            return None
        
        def is_empty(self):
            return self.size == 0
        
        def __len__(self):
            return self.size

    class MinHeap:
        """最小堆实现，使用自定义数组"""
        def __init__(self, capacity=1000):
            self.heap = HuffmanTreeModel.FixedArray(capacity)
        
        def push(self, item):
            if self.heap.append(item):
                self._bubble_up(self.heap.size - 1)
                return True
            return False
        
        def pop(self):
            if self.heap.is_empty():
                return None
            if self.heap.size == 1:
                return self.heap.pop_last()
            
            min_item = self.heap.get(0)
            last_item = self.heap.pop_last()
            self.heap.set(0, last_item)
            self._bubble_down(0)
            return min_item
        
        def _bubble_up(self, index):
            while index > 0:
                parent = (index - 1) // 2
                if self.heap.get(index).freq < self.heap.get(parent).freq:
                    self.heap.swap(index, parent)
                    index = parent
                else:
                    break
        
        def _bubble_down(self, index):
            while True:
                left_child = 2 * index + 1
                right_child = 2 * index + 2
                smallest = index
                
                if left_child < self.heap.size and self.heap.get(left_child).freq < self.heap.get(smallest).freq:
                    smallest = left_child
                
                if right_child < self.heap.size and self.heap.get(right_child).freq < self.heap.get(smallest).freq:
                    smallest = right_child
                
                if smallest == index:
                    break
                
                self.heap.swap(index, smallest)
                index = smallest
        
        def is_empty(self):
            return self.heap.is_empty()
        
        def __len__(self):
            return len(self.heap)

    def __init__(self):
        super().__init__()
        self.root = None

    def build(self, freq_map):
        """构建哈夫曼树"""
        if not self.active or not freq_map:
            return
        
        # 保存原始频率映射用于动画
        self._original_freq_map = freq_map
        self._animation_state = 'building'
        self._animation_progress = 0.0
        self._build_step = 0
        self._build_timer = None
        self._build_phase = 0  # 0: 选择节点, 1: 移动节点, 2: 合并节点, 3: 返回节点, 4: 完成
        self._current_merge_nodes = []  # 当前合并的节点
        self._merged_nodes = []  # 已合并的节点列表
        self._current_round = 0  # 当前轮次
        self._total_rounds = len(freq_map) - 1  # 总轮次（n个节点需要n-1轮合并）
        self._current_queue = []  # 当前队列中的节点/子树
        self._queue_trees = []  # 队列中每个元素对应的树结构
        self._build_complete = False  # 构建是否完成
        
        # 初始化队列
        sorted_items = sorted(freq_map.items(), key=lambda x: x[1])
        self._current_queue = [(char, freq) for char, freq in sorted_items]
        # 初始化队列中的树结构（初始时都是叶子节点）
        self._queue_trees = [self.Node(char, freq) for char, freq in sorted_items]
        
        # 不立即构建，让动画系统控制构建过程
        # self._start_build_animation()

    def _start_build_animation(self):
        """开始构建动画 - 现在由控制器调用"""
        if not hasattr(self, '_original_freq_map') or not self._original_freq_map:
            return
        
        # 使用最小堆
        heap = self.MinHeap()
        
        # 将所有字符和频率插入堆
        for char, freq in self._original_freq_map.items():
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
        
        # 完成构建
        self._animation_state = None
        self._animation_progress = 1.0

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
    
    def update_animation_progress(self, progress):
        """更新动画进度"""
        try:
            if hasattr(self, '_animation_state') and self._animation_state == 'building':
                self._animation_progress = progress
                
                # 计算当前轮次和步骤
                if not hasattr(self, '_current_round'):
                    self._current_round = 0
                if not hasattr(self, '_total_rounds'):
                    self._total_rounds = len(self._original_freq_map) - 1
                
                # 每轮包含5个步骤，计算当前轮次
                steps_per_round = 5
                total_steps = self._total_rounds * steps_per_round
                current_step = int(progress * total_steps)
                self._current_round = current_step // steps_per_round
                step_in_round = current_step % steps_per_round
                
                # 更新构建步骤
                if step_in_round < 1:
                    self._build_step = 0  # 选择最小两个节点
                elif step_in_round < 2:
                    self._build_step = 1  # 节点移动到合并区域
                elif step_in_round < 3:
                    self._build_step = 2  # 合并操作
                elif step_in_round < 4:
                    self._build_step = 3  # 新节点返回
                else:
                    self._build_step = 4  # 完成当前轮次
                    
                # 如果所有轮次完成，构建实际的哈夫曼树
                if progress >= 1.0:
                    self._complete_build_animation()
                else:
                    # 更新队列中的树结构
                    self._update_queue_trees()
        except Exception as e:
            print(f"更新动画进度错误: {e}")
            # 设置错误状态
            self._animation_state = 'error'
    
    def _update_queue_trees(self):
        """更新队列中的树结构"""
        try:
            if not hasattr(self, '_current_queue') or not hasattr(self, '_queue_trees'):
                return
            
            # 如果当前轮次完成，进行合并操作
            if self._build_step == 4 and self._current_round < self._total_rounds:
                if len(self._current_queue) >= 2:
                    # 获取前两个最小权值的节点/子树
                    left_tree = self._queue_trees[0]
                    right_tree = self._queue_trees[1]
                    
                    # 创建新的合并节点
                    merged_freq = left_tree.freq + right_tree.freq
                    new_tree = HuffmanTreeModel.Node(merged_freq)
                    new_tree.left = left_tree
                    new_tree.right = right_tree
                    
                    # 更新队列
                    new_queue = self._current_queue[2:] + [(f"merged_{self._current_round}", merged_freq)]
                    new_queue.sort(key=lambda x: x[1])
                    self._current_queue = new_queue
                    
                    # 更新队列中的树结构
                    new_trees = self._queue_trees[2:] + [new_tree]
                    new_trees.sort(key=lambda x: x.freq)
                    self._queue_trees = new_trees
        except Exception as e:
            print(f"更新队列树结构错误: {e}")
    
    def _complete_build_animation(self):
        """完成构建动画，创建实际的哈夫曼树"""
        if not hasattr(self, '_original_freq_map') or not self._original_freq_map:
            return
        
        # 使用最小堆
        heap = self.MinHeap()
        
        # 将所有字符和频率插入堆
        for char, freq in self._original_freq_map.items():
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
        
        # 完成构建
        self._animation_state = None
        self._animation_progress = 1.0
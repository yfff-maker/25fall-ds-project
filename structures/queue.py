# -*- coding: utf-8 -*-
"""
队列数据结构：纯业务逻辑实现
"""
from .base import BaseStructure
from .linked_list import CustomList

class QueueModel(BaseStructure):
    """队列模型类"""
    
    def __init__(self):
        super().__init__()
        self.data = CustomList()  # 使用CustomList作为底层容器
    
    def enqueue(self, value):
        """入队"""
        if not self.active or value is None:
            return
        self.data.append(value)
    
    def dequeue(self):
        """出队"""
        if not self.active or len(self.data) == 0:
            return None
        
        # 获取第一个元素
        first_value = self.data.get(0)
        
        # 删除第一个元素（模拟队列的FIFO）
        if len(self.data) > 0:
            # 将head指针移动到下一个节点
            if self.data.head:
                self.data.head = self.data.head.next
                self.data.size -= 1
        
        return first_value
    
    def front(self):
        """查看队首元素"""
        if not self.active or len(self.data) == 0:
            return None
        return self.data.get(0)
    
    def is_empty(self):
        """判断队列是否为空"""
        return len(self.data) == 0
    
    def size(self):
        """获取队列大小"""
        return len(self.data)
    
    def to_list(self):
        """转换为列表"""
        return self.data
    
    def clear(self):
        """清空队列"""
        if not self.active:
            return
        self.data = CustomList()
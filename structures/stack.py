# -*- coding: utf-8 -*-
"""
栈数据结构：纯业务逻辑实现
"""
from .base import BaseStructure
from .linked_list import CustomList

class StackModel(BaseStructure):
    """栈模型类"""
    
    
    class StackLL:
        """自写链表栈，完全避免使用list"""
        class Node:
            def __init__(self, v, nxt=None):
                self.v = v
                self.nxt = nxt
        
        def __init__(self):
            self.top = None
            self.n = 0
        
        def push(self, v):
            self.top = self.Node(v, self.top)
            self.n += 1
        
        def pop(self):
            if self.top is None:
                return None
            v = self.top.v
            self.top = self.top.nxt
            self.n -= 1
            return v
        
        def peek(self):
            return None if self.top is None else self.top.v
        
        def is_empty(self):
            return self.top is None
        
        def __len__(self):
            return self.n
        
        def to_list(self):
            """转换为自定义链表（用于调试和序列化）"""
            result = CustomList()
            current = self.top
            while current:
                result.append(current.v)
                current = current.nxt
            return result
        
        def to_array(self):
            """转换为数组形式（从栈底到栈顶的顺序）"""
            # 先收集所有元素
            elements = []
            current = self.top
            while current:
                elements.append(current.v)
                current = current.nxt
            # 反转顺序，使栈底元素在索引0，栈顶元素在最后
            return elements[::-1]

    def __init__(self):
        '''初始化栈'''
        super().__init__()
        self.data = self.StackLL()
        self._animation_state = None  # 动画状态：None, 'pushing', 'popping'
        self._new_value = None  # 新值（用于动画显示）
        self._animation_progress = 0.0  # 动画进度：0.0-1.0
        self._start_x = 0  # 动画起始x坐标
        self._start_y = 0  # 动画起始y坐标
        self._target_x = 0  # 动画目标x坐标
        self._target_y = 0  # 动画目标y坐标

    def push(self, value):
        """入栈"""
        if not self.active or value is None:
            return
        
        # 设置动画状态
        self._animation_state = 'pushing'
        self._new_value = value
        self._animation_progress = 0.0  # 开始动画
        
        # 设置动画起始位置（屏幕正上方）
        self._start_x = 0  # 将在适配器中计算
        self._start_y = 50  # 屏幕正上方
        
        # 设置动画目标位置（将在适配器中计算）
        self._target_x = 0
        self._target_y = 0
        
        # 延迟执行实际的入栈操作
        # 这里先不执行 self.data.push(value)，等动画完成后再执行

    def pop(self):
        """出栈"""
        if not self.active or self.data.is_empty():
            return None
        
        # 设置出栈动画状态
        self._animation_state = 'popping'
        self._pop_value = self.data.peek()  # 保存要弹出的值
        self._animation_progress = 0.0
        
        # 设置动画起始位置（栈顶位置）
        self._start_x = 0  # 将在适配器中计算
        self._start_y = 0
        
        # 设置动画目标位置（向上弹出）
        self._target_x = 0
        self._target_y = 0
        
        # 延迟执行实际的出栈操作
        # 这里先不执行 self.data.pop()，等动画完成后再执行
        return None

    def peek(self):
        """查看栈顶元素"""
        if not self.active:
            return None
        return self.data.peek()

    def is_empty(self):
        """判断栈是否为空"""
        return self.data.is_empty()

    def size(self):
        """获取栈的大小"""
        return len(self.data)

    def to_list(self):
        """转换为列表"""
        return self.data.to_list()
    
    def clear(self):
        """清空栈"""
        if not self.active:
            return
        # 重新初始化栈
        self.data = self.StackLL()
        self._animation_state = None
        self._new_value = None
    
    def build(self, values):
        """构建栈 - 批量添加元素"""
        if not self.active:
            return
        
        # 检查输入元素数量是否超过栈容量
        values_list = list(values)
        if len(values_list) > 10:
            # 设置栈满状态，不执行构建操作
            self._animation_state = 'stack_full'
            self._animation_progress = 0.0
            return
        
        # 清空当前栈
        self.data = self.StackLL()
        self._animation_state = None
        self._new_value = None
        
        # 设置构建动画状态
        self._animation_state = 'building'
        self._build_values = values_list  # 转换为列表
        self._build_index = 0  # 当前构建到的索引
        self._animation_progress = 0.0
    
    def complete_build_animation(self):
        """完成构建动画"""
        if self._animation_state == 'building':
            # 将所有值推入栈中
            for value in self._build_values:
                self.data.push(value)
            
            self._animation_state = None
            self._build_values = []
            self._build_index = 0
            self._animation_progress = 0.0
    
    def complete_push_animation(self):
        """完成入栈动画"""
        if self._animation_state == 'pushing' and self._new_value is not None:
            self.data.push(self._new_value)
            self._animation_state = None
            self._new_value = None
            self._animation_progress = 0.0
    
    def complete_pop_animation(self):
        """完成出栈动画"""
        if self._animation_state == 'popping':
            result = self.data.pop()
            self._animation_state = None
            self._pop_value = None
            self._animation_progress = 0.0
            return result
        return None
    
    def cancel_animation(self):
        """取消动画"""
        self._animation_state = None
        self._new_value = None
        self._animation_progress = 0.0
    
    def update_animation_progress(self, progress):
        """更新动画进度"""
        self._animation_progress = max(0.0, min(1.0, progress))
    
    def set_animation_target(self, target_x, target_y):
        """设置动画目标位置"""
        self._target_x = target_x
        self._target_y = target_y
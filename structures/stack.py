# -*- coding: utf-8 -*-
"""
栈数据结构：纯业务逻辑实现
"""
from .base import BaseStructure
from .linked_list import CustomList

class StackModel(BaseStructure):
    """栈模型类"""
    
    
    class SequentialStack:
        """顺序栈实现，使用数组存储"""
        def __init__(self, capacity=100):
            self._capacity = capacity
            self._data = [None] * capacity  # 固定大小数组
            self._top = -1  # 栈顶索引，-1表示空栈

        def _ensure_capacity(self, min_capacity):
            """确保容量至少为 min_capacity，不够则扩容为两倍或所需值"""
            if min_capacity <= self._capacity:
                return
            new_capacity = max(min_capacity, self._capacity * 2)
            new_data = [None] * new_capacity
            for i in range(self._top + 1):
                new_data[i] = self._data[i]
            self._data = new_data
            self._capacity = new_capacity
        
        def push(self, v):
            if self.is_full():
                # 自动扩容后再插入
                self._ensure_capacity(self._capacity + 1)
            self._top += 1
            self._data[self._top] = v
            return True
        
        def pop(self):
            if self.is_empty():
                return None
            v = self._data[self._top]
            self._data[self._top] = None
            self._top -= 1
            return v
        
        def peek(self):
            if self.is_empty():
                return None
            return self._data[self._top]
        
        def is_empty(self):
            return self._top == -1
        
        def is_full(self):
            return self._top == self._capacity - 1
        
        def __len__(self):
            return self._top + 1
        
        def to_list(self):
            """转换为自定义链表（用于调试和序列化）"""
            result = CustomList()
            for i in range(self._top + 1):
                result.append(self._data[i])
            return result
        
        def to_array(self):
            """转换为数组形式（从栈底到栈顶的顺序）"""
            return [self._data[i] for i in range(self._top + 1)]
        
        def clear(self):
            """清空栈"""
            self._top = -1
            # 清空数组内容
            for i in range(self._capacity):
                self._data[i] = None

    def __init__(self):
        '''初始化栈'''
        super().__init__()
        self.data = self.SequentialStack()
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
        # 使用 StackLL 的 clear 方法
        self.data.clear()
        self._animation_state = None
        self._new_value = None
    
    def build(self, values):
        """构建栈 - 批量添加元素"""
        if not self.active:
            return
        
        values_list = list(values)
        
        # 清空当前栈
        self.data = self.SequentialStack(max(len(values_list), self.data._capacity))
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
            success = self.data.push(self._new_value)
            if not success:
                # 如果入栈失败（栈满），设置栈满状态
                self._animation_state = 'stack_full'
            else:
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

    # ===== 序列化 =====
    def to_dict(self) -> dict:
        return {
            "elements": self.data.to_array(),
            "capacity": self.data._capacity,
        }

    def from_dict(self, data: dict) -> None:
        capacity = int(data.get("capacity", 100) or 100)
        self.data = self.SequentialStack(capacity)
        elements = data.get("elements", []) or []
        for v in elements:
            self.data.push(v)
        # 清理动画状态
        self._animation_state = None
        self._new_value = None
        self._animation_progress = 0.0
# -*- coding: utf-8 -*-
"""
顺序表数据结构：纯业务逻辑实现
使用数组式顺序存储，完全避免使用Python内置list
"""
from .base import BaseStructure

class SequentialListModel(BaseStructure):
    """顺序表模型类 - 数组式顺序存储"""
    
    class SequentialArray:
        """自写数组式顺序表，提供按位访问/插入/删除，完全避免使用list"""
        
        def __init__(self, capacity=100):
            self.capacity = capacity  # 数组容量
            self.data = [None] * capacity  # 固定大小数组
            self.size = 0  # 当前元素个数
        
        def _is_valid_position(self, pos):
            """检查位置是否有效"""
            return 0 <= pos < self.size
        
        def _is_full(self):
            """检查数组是否已满"""
            return self.size >= self.capacity
        
        def _expand_capacity(self):
            """扩容数组（当数组满时）"""
            # 创建新的更大数组
            new_capacity = self.capacity * 2
            new_data = [None] * new_capacity
            
            # 复制现有数据
            for i in range(self.size):
                new_data[i] = self.data[i]
            
            self.data = new_data
            self.capacity = new_capacity
        
        def get(self, pos):
            """获取指定位置的元素"""
            if not self._is_valid_position(pos):
                return None
            return self.data[pos]
        
        def set(self, pos, value):
            """设置指定位置的元素"""
            if not self._is_valid_position(pos):
                return False
            self.data[pos] = value
            return True
        
        def insert_at(self, pos, value):
            """在指定位置插入元素"""
            if value is None:
                return False
            
            # 调整位置到有效范围
            if pos < 0:
                pos = 0
            if pos > self.size:
                pos = self.size
            
            # 检查是否需要扩容
            if self._is_full():
                self._expand_capacity()
            
            # 将pos及之后的元素向后移动一位
            for i in range(self.size, pos, -1):
                self.data[i] = self.data[i - 1]
            
            # 在pos位置插入新元素
            self.data[pos] = value
            self.size += 1
            return True
        
        def delete_at(self, pos):
            """删除指定位置的元素"""
            if not self._is_valid_position(pos):
                return None
            
            # 保存要删除的元素
            deleted_value = self.data[pos]
            
            # 将pos之后的元素向前移动一位
            for i in range(pos, self.size - 1):
                self.data[i] = self.data[i + 1]
            
            # 清空最后一个位置
            self.data[self.size - 1] = None
            self.size -= 1
            return deleted_value
        
        def append(self, value):
            """在尾部添加元素"""
            return self.insert_at(self.size, value)
        
        def __len__(self):
            return self.size
        
        def to_list(self):
            """转换为列表（用于调试和序列化）"""
            # 使用生成器避免创建list
            for i in range(self.size):
                yield self.data[i]
        
        def __iter__(self):
            """支持迭代"""
            for i in range(self.size):
                yield self.data[i]
        
        def __str__(self):
            """字符串表示"""
            return f"SequentialArray({list(self)})"
        
        def __repr__(self):
            """调试表示"""
            return self.__str__()

    def __init__(self):
        super().__init__()
        self.data = self.SequentialArray()
        
        # 动画相关属性
        self._animation_state = None  # 动画状态：None, 'inserting', 'deleting'
        self._new_value = None  # 新值（用于动画显示）
        self._animation_progress = 0.0  # 动画进度：0.0-1.0
        self._start_x = 0  # 动画起始x坐标
        self._start_y = 0  # 动画起始y坐标
        self._target_x = 0  # 动画目标x坐标
        self._target_y = 0  # 动画目标y坐标
        self._insert_position = 0  # 插入位置

    def build(self, arr):
        """构建顺序表"""
        if not self.active:
            return
        
        # 清空现有数据
        self.data = self.SequentialArray()
        
        # 插入所有元素
        for v in arr:
            self.data.append(v)

    def insert_at(self, pos, value):
        """在指定位置插入元素"""
        if not self.active or value is None:
            return
        pos = max(0, min(pos, len(self.data)))
        
        # 设置动画状态
        self._animation_state = 'inserting'
        self._new_value = value
        self._insert_position = pos
        self._animation_progress = 0.0
        
        # 设置动画起始位置（屏幕正上方）
        self._start_x = 0  # 将在适配器中计算
        self._start_y = 50  # 屏幕正上方
        
        # 设置动画目标位置（将在适配器中计算）
        self._target_x = 0
        self._target_y = 0
        
        # 延迟执行实际的插入操作
        # 这里先不执行 self.data.insert_at(pos, value)，等动画完成后再执行

    def delete_at(self, pos):
        """删除指定位置的元素"""
        if not self.active or len(self.data) == 0:
            return
        if pos < 0 or pos >= len(self.data):
            return
        
        # 设置删除动画状态
        self._animation_state = 'deleting'
        self._delete_position = pos
        self._animation_progress = 0.0
        
        # 保存要删除的元素值（用于动画显示）
        self._deleted_value = self.data.get(pos)
        
        # 延迟执行实际的删除操作
        # 这里先不执行 self.data.delete_at(pos)，等动画完成后再执行

    def insert_at_head(self, value):
        """在头部插入元素"""
        if not self.active or value is None:
            return
        self.insert_at(0, value)

    def insert_at_tail(self, value):
        """在尾部插入元素"""
        if not self.active or value is None:
            return
        self.insert_at(len(self.data), value)
    
    def complete_insert_animation(self):
        """完成插入动画"""
        if self._animation_state == 'inserting' and self._new_value is not None:
            self.data.insert_at(self._insert_position, self._new_value)
            self._animation_state = None
            self._new_value = None
            self._animation_progress = 0.0
    
    def complete_delete_animation(self):
        """完成删除动画"""
        if self._animation_state == 'deleting':
            self.data.delete_at(self._delete_position)
            self._animation_state = None
            self._deleted_value = None
            self._delete_position = 0
            self._animation_progress = 0.0
    
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

    def get_at(self, pos):
        """获取指定位置的元素"""
        if not self.active:
            return None
        return self.data.get(pos)

    def set_at(self, pos, value):
        """设置指定位置的元素"""
        if not self.active:
            return
        self.data.set(pos, value)

    def length(self):
        """获取长度"""
        return len(self.data)

    def to_list(self):
        """转换为列表"""
        return self.data
    
    def clear(self):
        """清空顺序表"""
        if not self.active:
            return
        self.data = self.SequentialArray()
    
    def is_empty(self):
        """判断是否为空"""
        return len(self.data) == 0
    
    def is_full(self):
        """判断是否已满"""
        return self.data._is_full()
    
    def get_capacity(self):
        """获取数组容量"""
        return self.data.capacity
    
    def get_size(self):
        """获取当前元素个数"""
        return self.data.size
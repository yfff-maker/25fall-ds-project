"""
通用链表模块
提供自定义链表实现，替代Python内置list
支持多种数据结构的底层实现
"""
from .base import BaseStructure

class ListNode:
    """链表节点类"""
    def __init__(self, val):
        self.val = val
        self.next = None

class CustomList:
    """自定义链表类，替代Python内置list"""
    
    def __init__(self):
        self.head = None
        self.size = 0
    
    def append(self, val):
        """在链表末尾添加元素"""
        new_node = ListNode(val)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.size += 1
    
    def get(self, value):
        """按值查询元素位置索引"""
        current = self.head
        index = 0
        while current:
            if current.val == value:
                return index
            current = current.next
            index += 1
        return -1
    
    def insert(self, index, val):
        """在指定位置插入元素"""
        if index < 0 or index > self.size:
            return False
        
        new_node = ListNode(val)
        
        if index == 0:
            # 在头部插入
            new_node.next = self.head
            self.head = new_node
        else:
            # 在中间或尾部插入
            current = self.head
            for i in range(index - 1):
                current = current.next
            new_node.next = current.next
            current.next = new_node
        
        self.size += 1
        return True
    
    def delete(self, index):
        """删除指定位置的元素"""
        if index < 0 or index >= self.size:
            return None
        
        if index == 0:
            # 删除头节点
            if self.head:
                deleted_val = self.head.val
                self.head = self.head.next
                self.size -= 1
                return deleted_val
        else:
            # 删除中间或尾节点
            current = self.head
            for i in range(index - 1):
                if current and current.next:
                    current = current.next
                else:
                    return None
            
            if current and current.next:
                deleted_val = current.next.val
                current.next = current.next.next
                self.size -= 1
                return deleted_val
        
        return None
    
    def to_array(self):
        """转换为数组形式（用于调试）"""
        # 使用生成器避免创建list
        current = self.head
        while current:
            yield current.val
            current = current.next
    
    def __len__(self):
        return self.size
    
    def __iter__(self):
        """支持迭代"""
        current = self.head
        while current:
            yield current.val
            current = current.next
    
    def __str__(self):
        """字符串表示"""
        return f"CustomList({list(self)})"
    
    def __repr__(self):
        """调试表示"""
        return self.__str__()

class LinkedListModel(BaseStructure):
    """链表模型类 - 独立的数据结构"""
    
    def __init__(self):
        super().__init__()
        self.data = CustomList()
        
        # 动画状态
        self._animation_state = None  # 'building', 'inserting', 'deleting'
        self._animation_progress = 0.0
        self._new_value = None
        self._insert_position = 0
        self._delete_position = 0
        self._deleted_value = None
        self._start_x = 0
        self._start_y = 0
        self._target_x = 0
        self._target_y = 0
    
    def append(self, value):
        """在链表末尾添加元素"""
        if not self.active or value is None:
            return
        self.data.append(value)
    
    def insert(self, index, value):
        """在指定位置插入元素"""
        if not self.active or value is None:
            return
        
        if index < 0 or index > len(self.data):
            return
        
        # 设置插入动画状态
        self._animation_state = 'inserting'
        self._new_value = value
        self._insert_position = index
        self._animation_progress = 0.0
        
        # 设置动画起始位置（屏幕正上方）
        self._start_x = 0  # 将在适配器中计算
        self._start_y = 50  # 屏幕正上方
        
        # 设置动画目标位置（将在适配器中计算）
        self._target_x = 0
        self._target_y = 0
        
        # 延迟执行实际的插入操作
        # 这里先不执行 self.data.insert(value)，等动画完成后再执行
    
    def get(self, index):
        """获取指定位置的元素"""
        if not self.active:
            return None
        return self.data.get(index)
    
    def remove(self, value):
        """删除指定值的元素"""
        if not self.active:
            return
        
        if self.data.head is None:
            return
        
        # 如果删除头节点
        if self.data.head.val == value:
            self.data.head = self.data.head.next
            self.data.size -= 1
            return
        
        # 删除中间或尾节点
        current = self.data.head
        while current.next and current.next.val != value:
            current = current.next
        
        if current.next:
            current.next = current.next.next
            self.data.size -= 1
    
    def size(self):
        """获取链表大小"""
        return len(self.data)
    
    def is_empty(self):
        """判断链表是否为空"""
        return len(self.data) == 0
    
    def to_list(self):
        """转换为列表"""
        return self.data
    
    def clear(self):
        """清空链表"""
        if not self.active:
            return
        self.data = CustomList()
    
    def find(self, value):
        """查找元素位置"""
        if not self.active:
            return -1
        
        current = self.data.head
        index = 0
        while current:
            if current.val == value:
                return index
            current = current.next
            index += 1
        return -1
    
    def reverse(self):
        """反转链表"""
        if not self.active or self.data.head is None:
            return
        
        prev = None
        current = self.data.head
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        self.data.head = prev
    
    def build(self, values):
        """构建链表"""
        if not self.active:
            return
        
        # 设置构建动画状态
        self._animation_state = 'building'
        self._animation_progress = 0.0
        self._build_values = list(values) if hasattr(values, '__iter__') else [values]
        self._build_index = 0
        
        # 清空现有数据
        self.data = CustomList()
        
        # 延迟执行实际的构建操作
        # 这里先不执行 self.data.append(value)，等动画完成后再执行
    
    def insert_at(self, position, value):
        """在指定位置插入元素（别名方法）"""
        self.insert(position, value)
    
    def delete_at(self, position):
        """删除指定位置的元素"""
        if not self.active or position < 0 or position >= len(self.data):
            return
        
        # 设置删除动画状态
        self._animation_state = 'deleting'
        self._animation_progress = 0.0
        self._delete_position = position
        
        # 取出将要删除的值（仅用于渲染时高亮/占位）
        cur = self.data.head
        idx = 0
        while cur and idx < position:
            cur = cur.next
            idx += 1
        self._deleted_value = cur.val if cur else None
        
        # 这里先不执行 self.data.delete(position)，等动画完成后再执行
    
    def insert_at_end(self, value):
        """在末尾插入元素（别名方法）"""
        self.append(value)
    
    def delete_by_value(self, value):
        """按值删除元素（别名方法）"""
        self.remove(value)
    
    def update_animation_progress(self, progress):
        """更新动画进度"""
        self._animation_progress = progress
    
    def complete_build_animation(self):
        """完成构建动画"""
        if self._animation_state == 'building' and hasattr(self, '_build_values'):
            # 执行实际的构建操作
            for value in self._build_values:
                if value is not None:
                    self.data.append(value)
            self._animation_state = None
    
    def complete_insert_animation(self):
        """完成插入动画"""
        if self._animation_state == 'inserting':
            # 执行实际的插入操作
            index = self._insert_position
            value = self._new_value
            
            # 使用 CustomList 的 insert 方法
            self.data.insert(index, value)
            
            self._animation_state = None
    
    def complete_delete_animation(self):
        """完成删除动画"""
        if self._animation_state == 'deleting':
            pos = getattr(self, '_delete_position', -1)
            if pos >= 0:
                self.data.delete(pos)
            self._animation_state = None
            self._animation_progress = 0.0
            self._delete_position = 0
            self._deleted_value = None
    
    # ===== 序列化 =====
    def to_dict(self) -> dict:
        elements = list(self.data.to_array()) if hasattr(self.data, 'to_array') else list(self.data)
        return {
            "elements": elements,
        }

    def from_dict(self, data: dict) -> None:
        # 清空后逐个 append 重建
        self.data = CustomList()
        elements = data.get("elements", []) or []
        for v in elements:
            self.data.append(v)
        # 清理动画状态
        self._animation_state = None
        self._animation_progress = 0.0
        self._new_value = None
        self._insert_position = 0
        self._delete_position = 0
        self._deleted_value = None
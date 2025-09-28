# 数据结构架构设计

## 完全分离设计原则

### 设计理念
- **容器层**: 提供通用数据结构容器
- **结构层**: 提供具体数据结构的业务逻辑
- **分离原则**: 容器和数据结构职责分离

## 架构层次

```
应用层 (main.py, controllers/)
    ↓
数据结构层 (StackModel, LinkedListModel, QueueModel)
    ↓
容器层 (CustomList)
    ↓
节点层 (ListNode)
```

## 详细设计

### 1. 容器层 (Container Layer)

#### CustomList - 通用链表容器
```python
class CustomList:
    """通用链表容器，替代Python内置list"""
    - 提供基础的链表操作
    - 不继承BaseStructure
    - 可被多个数据结构复用
    - 类似Python内置list的功能
```

**特点**:
- ✅ 纯容器，无业务逻辑
- ✅ 可复用性强
- ✅ 避免使用Python内置list
- ✅ 支持迭代、索引访问等

### 2. 数据结构层 (Structure Layer)

#### StackModel - 栈数据结构
```python
class StackModel(BaseStructure):
    """栈数据结构，基于CustomList实现"""
    - 继承BaseStructure
    - 内部使用CustomList
    - 实现LIFO逻辑
    - 提供栈特有操作
```

#### LinkedListModel - 链表数据结构
```python
class LinkedListModel(BaseStructure):
    """链表数据结构，基于CustomList实现"""
    - 继承BaseStructure
    - 内部使用CustomList
    - 实现链表特有操作
    - 提供插入、删除、查找等
```

#### QueueModel - 队列数据结构
```python
class QueueModel(BaseStructure):
    """队列数据结构，基于CustomList实现"""
    - 继承BaseStructure
    - 内部使用CustomList
    - 实现FIFO逻辑
    - 提供队列特有操作
```

## 设计优势

### 1. 职责分离
- **CustomList**: 专注容器功能
- **数据结构类**: 专注业务逻辑
- **清晰边界**: 各司其职

### 2. 可复用性
- **CustomList**: 可被多个数据结构使用
- **避免重复**: 不需要重复实现链表
- **统一接口**: 所有数据结构使用相同的容器

### 3. 可维护性
- **修改容器**: 只需修改CustomList
- **修改逻辑**: 只需修改具体数据结构
- **影响隔离**: 修改不会相互影响

### 4. 符合要求
- **无内置list**: 完全避免使用Python内置list
- **自定义实现**: 所有容器都是自定义的
- **教学友好**: 符合数据结构教学要求

## 使用示例

### 创建数据结构
```python
# 栈
stack = StackModel()
stack.push(1)
stack.push(2)

# 链表
linked_list = LinkedListModel()
linked_list.append(1)
linked_list.insert(0, 2)

# 队列
queue = QueueModel()
queue.enqueue(1)
queue.enqueue(2)
```

### 底层都使用CustomList
```python
# 所有数据结构内部都使用CustomList
stack.data        # CustomList实例
linked_list.data  # CustomList实例
queue.data        # CustomList实例
```

## 扩展指南

### 添加新数据结构
1. 继承`BaseStructure`
2. 内部使用`CustomList`
3. 实现数据结构特有操作
4. 添加适配器支持可视化

### 示例：双端队列
```python
class DequeModel(BaseStructure):
    def __init__(self):
        super().__init__()
        self.data = CustomList()  # 复用容器
    
    def add_front(self, value):
        self.data.insert(0, value)
    
    def add_rear(self, value):
        self.data.append(value)
```

## 总结

✅ **完全分离**: 容器和数据结构职责分离  
✅ **高度复用**: CustomList可被多个数据结构使用  
✅ **易于维护**: 修改影响范围小  
✅ **符合要求**: 完全避免使用Python内置list  
✅ **教学友好**: 结构清晰，易于理解  

这种设计既满足了"不使用内置list"的要求，又提供了清晰的架构和良好的可维护性！

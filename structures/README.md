# 数据结构模块说明

## 项目结构

```
structures/
├── __init__.py          # 模块初始化
├── base.py              # 基础结构类
├── linked_list.py       # 通用链表实现
├── stack.py             # 栈数据结构
├── queue.py             # 队列数据结构
├── binary_tree.py       # 二叉树数据结构
├── bst.py               # 二叉搜索树
├── huffman.py           # 哈夫曼树
└── README.md            # 本说明文档
```

## 模块设计原则

### 1. 分层设计
- **基础层**: `base.py` - 提供所有数据结构的共同接口
- **容器层**: `linked_list.py` - 提供通用链表容器
- **结构层**: `stack.py`, `queue.py` 等 - 具体数据结构实现

### 2. 职责分离
- **linked_list.py**: 通用链表实现，替代Python内置list
- **stack.py**: 栈的LIFO逻辑实现
- **queue.py**: 队列的FIFO逻辑实现
- **tree.py**: 树结构实现

### 3. 复用性
- 所有数据结构都可以基于`CustomList`构建
- 避免重复实现链表功能
- 统一的接口设计

## 使用示例

### 通用链表
```python
from .linked_list import CustomList

# 创建链表
my_list = CustomList()
my_list.append(1)
my_list.append(2)
my_list.append(3)

# 支持迭代
for val in my_list:
    print(val)

# 支持索引访问
val = my_list.get(1)  # 2
```

### 栈数据结构
```python
from .stack import StackModel

# 创建栈
stack = StackModel()
stack.push(1)
stack.push(2)
stack.push(3)

# 栈操作
val = stack.pop()  # 3
top = stack.peek()  # 2
```

## 扩展指南

### 添加新的数据结构
1. 在`structures/`目录下创建新文件
2. 继承`BaseStructure`基类
3. 使用`CustomList`作为底层容器
4. 实现必需的方法

### 示例：队列实现
```python
from .base import BaseStructure
from .linked_list import CustomList

class QueueModel(BaseStructure):
    def __init__(self):
        super().__init__()
        self.data = CustomList()
    
    def enqueue(self, value):
        self.data.append(value)
    
    def dequeue(self):
        if len(self.data) == 0:
            return None
        val = self.data.get(0)
        # 移除第一个元素
        # ... 实现逻辑
        return val
```

## 设计优势

1. **模块化**: 每个数据结构独立成文件
2. **可复用**: 通用链表可被多个数据结构使用
3. **可维护**: 修改链表实现不影响其他结构
4. **可扩展**: 易于添加新的数据结构
5. **符合要求**: 完全避免使用Python内置list

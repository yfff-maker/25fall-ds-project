# 数据结构可视化模拟器 (PyQt5)

## 运行
```bash
pip install PyQt5
python main.py
```

## 功能
- 左侧分组选择数据结构；中间是绘图区域；底部是算法控制面板（播放/暂停/下一步/速度）。
- 已实现：
  - 链表：尾插、按值删除（带高亮动画与指针重连）。
  - 栈：push/pop（动画移除）。
  - BST：插入/查找（路径高亮）。
  - 二叉树：简化的插入（首次插入作为根）与遍历（前/中/后序高亮）。
  - 哈夫曼树：根据频率表动态合并可视化。
- 动画系统：基于步进队列 + QTimer（播放/暂停/逐步/速度）。
- **DSL自动化**: 支持通过简洁的DSL命令自动化操作数据结构（新增功能）

## DSL语法

DSL（领域特定语言）允许用户通过简洁的文本命令来自动化操作数据结构。

### 顺序表操作
```
create arraylist with 1,2,3
insert 4 at 1 in arraylist
delete at 0 from arraylist
delete at 1 from arraylist
```

### 链表操作
```
create linkedlist with 10,20,30
insert 15 at 1 in linkedlist
delete at 2 from linkedlist
```

### 栈操作
```
create stack
push 100 to stack
push 200 to stack
pop from stack
```

### 二叉树操作(层序构建和单个插入)
```
create binarytree with 1,2,3,4,5,6,7  # 层序构建完整树
insert 8 as left of 4 in binarytree      # 在指定位置插入
insert 9 as right of 4 in binarytree
```

### 二叉搜索树操作
```
create bst with 50,30,70,20,40,60,80
insert 25 in bst
search 60 in bst
delete 30 from bst
```

### AVL树操作
```
create avl with 7,19,16,27,9,5,14,11,17,12
insert 25 in avl
clear avl
```

### 哈夫曼树操作
```
build huffman with a:5,b:9,c:12,d:13,e:16,f:45
```

### 使用方法
1. 在左侧面板的"DSL命令"区域输入命令
2. 点击"执行"按钮运行
3. 点击"从文件导入"可加载`.dsl`脚本文件
4. 脚本示例见 `example_commands.dsl`

## 目录
- main.py：应用入口、左侧动态面板、状态栏、控制面板绑定、DSL命令输入界面。
- canvas.py：QGraphicsScene 封装、绘图与动画原语（节点/箭头/高亮/队列动画）。
- widgets/control_panel.py：底部控制面板（Dock）。
- controllers/：
  - main_controller.py：主控制器，协调所有数据结构操作。
  - dsl_parser.py：DSL解析器，将文本命令解析为结构化命令对象。
  - dsl_executor.py：DSL执行器，将命令转换为控制器方法调用。
- structures/：
  - base.py：BaseStructure 抽象基类（持有 Canvas 的可视化调用）。
  - sequential_list.py：顺序表可视化逻辑。
  - linked_list.py：链表可视化逻辑。
  - stack.py：栈可视化逻辑。
  - binary_tree.py：普通二叉树遍历可视化。
  - bst.py：二叉搜索树插入/查找可视化。
  - avl.py：AVL平衡树可视化。
  - huffman.py：哈夫曼树构建可视化。
- example_commands.dsl：DSL命令脚本示例文件。

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

## 目录
- main.py：应用入口、左侧动态面板、状态栏、控制面板绑定。
- canvas.py：QGraphicsScene 封装、绘图与动画原语（节点/箭头/高亮/队列动画）。
- widgets/control_panel.py：底部控制面板（Dock）。
- structures/：
  - base.py：BaseStructure 抽象基类（持有 Canvas 的可视化调用）。
  - linked_list.py：链表可视化逻辑。
  - stack.py：栈可视化逻辑。
  - binary_tree.py：普通二叉树遍历可视化。
  - bst.py：二叉搜索树插入/查找可视化。
  - huffman.py：哈夫曼树构建可视化。

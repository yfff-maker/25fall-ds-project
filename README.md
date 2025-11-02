# 数据结构可视化模拟器 (PyQt5)

## 运行
```bash
pip install PyQt5 requests
python main.py
```

**注意：** 使用LLM自然语言功能需要：
1. 安装requests库：`pip install requests`（通常Python已自带）
2. 设置环境变量：`OPENROUTER_API_KEY=your_api_key_here`
3. （可选）指定模型：`OPENROUTER_MODEL=openai/gpt-3.5-turbo`（默认值）

## 功能
- 左侧分组选择数据结构；中间是绘图区域；底部是算法控制面板（播放/暂停/下一步/速度）。
- 已实现：
  - 链表：尾插、按值删除（带高亮动画与指针重连）。
  - 栈：push/pop（动画移除）。
  - BST：插入/查找（路径高亮）。
  - 二叉树：简化的插入（首次插入作为根）与遍历（前/中/后序高亮）。
  - 哈夫曼树：根据频率表动态合并可视化。
- 动画系统：基于步进队列 + QTimer（播放/暂停/逐步/速度）。
- **DSL自动化**: 支持通过简洁的DSL命令自动化操作数据结构
- **LLM自然语言交互**: 支持使用自然语言描述操作，AI自动转换为操作指令并执行（新增功能）

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

## LLM自然语言交互

### 功能说明
通过AI助手，用户可以使用自然语言描述操作，系统会自动将其转换为操作指令并执行。

### 使用方法
1. 注册OpenRouter账户：访问 https://openrouter.ai 并获取API密钥
2. 设置环境变量 `OPENROUTER_API_KEY`（您的OpenRouter API密钥）
   - Windows PowerShell: `$env:OPENROUTER_API_KEY="your_api_key_here"`
   - Windows CMD: `set OPENROUTER_API_KEY=your_api_key_here`
   - Linux/Mac: `export OPENROUTER_API_KEY="your_api_key_here"`
3. （可选）指定模型：`OPENROUTER_MODEL=openai/gpt-3.5-turbo`（支持多种模型，如claude、llama等）
4. 在菜单栏点击"AI助手" -> "自然语言操作"（或按 Ctrl+L）
5. 在对话框中输入自然语言描述，例如：
   - "创建一个包含数据元素[5,3,7,2,4]的二叉搜索树"
   - "在BST中插入25"
   - "创建一个包含1,2,3的顺序表"
6. 点击"执行"，系统会自动转换并执行操作

### 支持的自然语言操作
- 创建数据结构（顺序表、链表、栈、二叉树、BST、AVL树、哈夫曼树）
- 插入、删除、查找等操作
- 支持多种自然语言表达方式

### 注意事项
- 需要有效的OpenRouter API密钥（可在 https://openrouter.ai 获取）
- 支持多种大模型（GPT、Claude、Llama等），通过环境变量`OPENROUTER_MODEL`指定
- 首次使用需要网络连接
- 如果LLM转换失败，可以尝试在DSL输入框中手动输入DSL命令
- OpenRouter提供统一的API接口，访问多个模型提供商

## 目录
- main.py：应用入口、左侧动态面板、状态栏、控制面板绑定、DSL命令输入界面。
- canvas.py：QGraphicsScene 封装、绘图与动画原语（节点/箭头/高亮/队列动画）。
- widgets/control_panel.py：底部控制面板（Dock）。
- controllers/：
  - main_controller.py：主控制器，协调所有数据结构操作。
  - dsl_parser.py：DSL解析器，将文本命令解析为结构化命令对象。
  - dsl_executor.py：DSL执行器，将命令转换为控制器方法调用。
  - llm_service.py：LLM服务，通过OpenRouter API将自然语言转换为JSON格式的操作动作。
  - action_executor.py：动作执行器，根据JSON动作直接调用控制器方法。
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

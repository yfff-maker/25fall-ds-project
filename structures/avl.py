# -*- coding: utf-8 -*-
"""
AVL树数据结构：自平衡二叉搜索树实现
"""
from .base import BaseStructure

class AVLModel(BaseStructure):
    """AVL树模型类"""
    
    class Node:
        def __init__(self, value, left=None, right=None, height=1):
            self.value = value
            self.left = left
            self.right = right
            self.height = height

    def __init__(self):
        super().__init__()
        self.root = None
        
        # 动画相关属性
        self._animation_state = None  # 动画状态：None, 'inserting', 'rotating_LL', 'rotating_RR', 'rotating_LR', 'rotating_RL'
        self._animation_progress = 0.0  # 动画进度：0.0-1.0
        self._new_value = None  # 新节点值
        self._imbalance_node_value = None  # 失衡节点值
        self._rotation_type = None  # 旋转类型：'LL', 'RR', 'LR', 'RL'
        self._rotation_nodes = []  # 参与旋转的节点值列表
        self._insert_path = []  # 插入路径（节点值列表）
        self._current_insert_step = 0  # 当前插入步骤
        self._insert_comparison_result = None  # 插入比较结果
        self._current_search_node_value = None  # 当前搜索的节点值
        
        # 插入可视化四阶段相关状态
        self._check_path = []             # 自上而下路径（逻辑路径）
        self._check_path_rev = []         # 自底向上检查路径
        self._current_check_node_value = None
        self._current_check_bf = None
        self._rotation_plan = None        # {'type': 'LL'|..., 'nodes': [...]} 用于动画展示
        self._phase_breaks = (0.35, 0.75, 0.85, 1.0)  # 插入/检查/决策/旋转

    def insert(self, value):
        """插入节点到AVL树"""
        if not self.active or value is None:
            return
        
        try:
            v = float(value)
        except:
            v = value
        
        # 统一进入插入动画
        self._animation_state = 'inserting'
        self._new_value = v
        self._animation_progress = 0.0
        
        # 计算插入路径用于比较动画
        if self.root is not None:
            self._insert_path = self._calculate_insert_path(self.root, v)
        else:
            self._insert_path = []
        self._current_insert_step = 0
        self._insert_comparison_result = None
        
        # 生成检查路径（末尾追加逻辑插入点）
        self._check_path = list(self._insert_path)
        if self._check_path and self._check_path[-1] != v:
            self._check_path.append(v)
        elif not self._check_path:
            self._check_path = [v]
        self._check_path_rev = list(reversed(self._check_path))
        self._current_check_node_value = None
        self._current_check_bf = None
        
        # 预演一次插入（影子树），推导首个失衡与旋转类型，仅用于可视化
        shadow_root = self._clone_tree(self.root)
        shadow_root = self._shadow_insert(shadow_root, v)
        self._rotation_plan = self._analyze_first_imbalance_and_rotation(shadow_root)

    def _calculate_insert_path(self, node, value):
        """计算插入路径（用于比较动画）"""
        path = []
        current = node
        
        while current:
            path.append(current.value)
            if value < current.value:
                if current.left is None:
                    break  # 到达插入位置
                current = current.left
            elif value > current.value:
                if current.right is None:
                    break  # 到达插入位置
                current = current.right
            else:
                break  # 值已存在
        
        return path

    def _insert_recursive(self, node, value):
        """递归插入节点并返回调整后的子树根"""
        # 1. 执行标准BST插入
        if not node:
            return self.Node(value)
        
        if value < node.value:
            node.left = self._insert_recursive(node.left, value)
        elif value > node.value:
            node.right = self._insert_recursive(node.right, value)
        else:
            return node  # 值已存在，不插入
        
        # 2. 更新节点高度
        self._update_height(node)
        
        # 3. 获取平衡因子
        balance = self._get_balance_factor(node)
        
        # 4. 如果节点失衡，执行相应的旋转
        if balance > 1:  # 左子树过高
            if value < node.left.value:
                # LL情况：左左
                return self._rotate_right(node)
            else:
                # LR情况：左右
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node)
        
        elif balance < -1:  # 右子树过高
            if value > node.right.value:
                # RR情况：右右
                return self._rotate_left(node)
            else:
                # RL情况：右左
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node)
        
        return node

    # ===== 影子树与预演分析 =====
    def _clone_tree(self, node):
        if not node:
            return None
        new_node = self.Node(node.value, height=node.height)
        new_node.left = self._clone_tree(node.left)
        new_node.right = self._clone_tree(node.right)
        return new_node

    def _shadow_insert(self, node, value):
        if not node:
            return self.Node(value)
        if value < node.value:
            node.left = self._shadow_insert(node.left, value)
        elif value > node.value:
            node.right = self._shadow_insert(node.right, value)
        self._update_height(node)
        balance = self._get_balance_factor(node)
        if balance > 1:
            if value < node.left.value:
                return self._rotate_right(node)
            else:
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node)
        if balance < -1:
            if value > node.right.value:
                return self._rotate_left(node)
            else:
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node)
        return node

    def _analyze_first_imbalance_and_rotation(self, root_after):
        plan = None
        v = self._new_value
        # 重新走到插入值所在的节点
        path = []
        current = root_after
        while current:
            path.append(current)
            if v < current.value:
                current = current.left
            elif v > current.value:
                current = current.right
            else:
                break
        for node in reversed(path):
            bf = self._get_balance_factor(node)
            if abs(bf) > 1:
                if bf > 1:
                    if self._get_balance_factor(node.left) >= 0:
                        plan = {'type': 'LL', 'nodes': [node.value, node.left.value]}
                    else:
                        plan = {'type': 'LR', 'nodes': [node.value, node.left.value, node.left.right.value]}
                else:
                    if self._get_balance_factor(node.right) <= 0:
                        plan = {'type': 'RR', 'nodes': [node.value, node.right.value]}
                    else:
                        plan = {'type': 'RL', 'nodes': [node.value, node.right.value, node.right.left.value]}
                break
        return plan

    def _get_height(self, node):
        """获取节点高度"""
        if not node:
            return 0
        return node.height

    def _update_height(self, node):
        """更新节点高度"""
        if node:
            node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))

    def _get_balance_factor(self, node):
        """计算平衡因子（左子树高度 - 右子树高度）"""
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)

    def _rotate_left(self, node):
        """左旋操作"""
        if not node or not node.right:
            return node
        
        # 执行左旋
        new_root = node.right
        node.right = new_root.left
        new_root.left = node
        
        # 更新高度
        self._update_height(node)
        self._update_height(new_root)
        
        return new_root

    def _rotate_right(self, node):
        """右旋操作"""
        if not node or not node.left:
            return node
        
        # 执行右旋
        new_root = node.left
        node.left = new_root.right
        new_root.right = node
        
        # 更新高度
        self._update_height(node)
        self._update_height(new_root)
        
        return new_root

    def _balance(self, node):
        """判断失衡类型并执行对应旋转"""
        if not node:
            return node
        
        balance = self._get_balance_factor(node)
        
        # 左子树过高
        if balance > 1:
            left_balance = self._get_balance_factor(node.left)
            if left_balance >= 0:
                # LL情况
                self._rotation_type = 'LL'
                self._rotation_nodes = [node.value, node.left.value]
                return self._rotate_right(node)
            else:
                # LR情况
                self._rotation_type = 'LR'
                self._rotation_nodes = [node.value, node.left.value, node.left.right.value]
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node)
        
        # 右子树过高
        elif balance < -1:
            right_balance = self._get_balance_factor(node.right)
            if right_balance <= 0:
                # RR情况
                self._rotation_type = 'RR'
                self._rotation_nodes = [node.value, node.right.value]
                return self._rotate_left(node)
            else:
                # RL情况
                self._rotation_type = 'RL'
                self._rotation_nodes = [node.value, node.right.value, node.right.left.value]
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node)
        
        return node

    def find_node_by_value(self, value):
        """根据值查找节点"""
        return self._find_node(self.root, value)

    def _find_node(self, node, value):
        """递归查找节点"""
        if not node:
            return None
        if node.value == value:
            return node
        elif value < node.value:
            return self._find_node(node.left, value)
        else:
            return self._find_node(node.right, value)

    def get_all_node_values(self):
        """获取所有节点的值"""
        values = []
        self._collect_values(self.root, values)
        return values

    def _collect_values(self, node, values):
        """递归收集节点值"""
        if node:
            values.append(node.value)
            self._collect_values(node.left, values)
            self._collect_values(node.right, values)

    def get_height(self):
        """获取树的高度"""
        return self._get_height(self.root)

    def is_empty(self):
        """判断树是否为空"""
        return self.root is None

    def clear(self):
        """清空树"""
        self.root = None

    def traverse_inorder(self):
        """中序遍历"""
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        """递归中序遍历"""
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)

    def update_insert_animation(self, progress):
        """更新插入动画进度（四阶段）"""
        if self._animation_state != 'inserting':
            return
        
        self._animation_progress = max(0.0, min(1.0, progress))
        p1, p2, p3, p4 = self._phase_breaks
        prog = self._animation_progress
        
        # 阶段1：新节点路径比较/下落
        if prog < p1:
            total_steps = max(1, len(self._insert_path))
            idx = min(int((prog / p1) * total_steps), total_steps - 1)
            if self._insert_path:
                self._current_insert_step = idx
                self._current_search_node_value = self._insert_path[idx]
                if self._new_value < self._current_search_node_value:
                    self._insert_comparison_result = 'less'
                elif self._new_value > self._current_search_node_value:
                    self._insert_comparison_result = 'greater'
                else:
                    self._insert_comparison_result = 'equal'
            self._current_check_node_value = None
            self._current_check_bf = None
            self._rotation_type = None
            self._rotation_nodes = []
            return
        
        # 阶段2：自底向上检查BF
        if prog < p2 and self._check_path_rev:
            local = (prog - p1) / (p2 - p1)
            total = len(self._check_path_rev)
            idx = min(int(local * total), total - 1)
            val = self._check_path_rev[idx]
            self._current_check_node_value = val
            node = self.find_node_by_value(val)
            if node:
                self._current_check_bf = self._get_balance_factor(node)
            else:
                self._current_check_bf = 0
            self._rotation_type = None
            self._rotation_nodes = []
            return
        
        # 阶段3：显示旋转类型提示
        if prog < p3:
            if self._rotation_plan:
                self._rotation_type = self._rotation_plan['type']
                self._rotation_nodes = self._rotation_plan['nodes']
            else:
                self._rotation_type = None
                self._rotation_nodes = []
            return
        
        # 阶段4：旋转细节动画（位置插值交由适配器处理）
        if self._rotation_plan:
            self._rotation_type = self._rotation_plan['type']
            self._rotation_nodes = self._rotation_plan['nodes']
        else:
            self._rotation_type = None
            self._rotation_nodes = []

    def complete_insert_animation(self):
        """完成插入节点动画"""
        if self._animation_state == 'creating_root' and self._new_value is not None:
            # 创建根节点
            self.root = self.Node(self._new_value)
            self._animation_state = None
            self._new_value = None
            self._animation_progress = 0.0
        elif self._animation_state == 'inserting' and self._new_value is not None:
            # 执行实际的插入操作
            self.root = self._insert_recursive(self.root, self._new_value)
            
            self._animation_state = None
            self._new_value = None
            self._insert_path = []
            self._current_insert_step = 0
            self._insert_comparison_result = None
            self._animation_progress = 0.0

    def cancel_animation(self):
        """取消动画"""
        self._animation_state = None
        self._new_value = None
        self._imbalance_node_value = None
        self._rotation_type = None
        self._rotation_nodes = []
        self._insert_path = []
        self._current_insert_step = 0
        self._insert_comparison_result = None
        self._current_search_node_value = None
        self._animation_progress = 0.0
        self._check_path = []
        self._check_path_rev = []
        self._current_check_node_value = None
        self._current_check_bf = None
        self._rotation_plan = None

    def update_animation_progress(self, progress):
        """更新动画进度"""
        self._animation_progress = max(0.0, min(1.0, progress))

    # ===== 序列化 =====
    def _node_to_dict(self, node):
        if node is None:
            return None
        return {
            "value": node.value,
            "left": self._node_to_dict(node.left),
            "right": self._node_to_dict(node.right),
            "height": node.height,
        }

    def _dict_to_node(self, data):
        if not data:
            return None
        node = self.Node(data.get("value"), height=data.get("height", 1))
        node.left = self._dict_to_node(data.get("left"))
        node.right = self._dict_to_node(data.get("right"))
        return node

    def to_dict(self) -> dict:
        return {
            "root": self._node_to_dict(self.root)
        }

    def from_dict(self, data: dict) -> None:
        self.root = self._dict_to_node(data.get("root"))
        # 清理动画状态
        self._animation_state = None
        self._animation_progress = 0.0
        self._new_value = None
        self._imbalance_node_value = None
        self._rotation_type = None
        self._rotation_nodes = []
        self._insert_path = []
        self._current_insert_step = 0
        self._insert_comparison_result = None
        self._current_search_node_value = None
        self._check_path = []
        self._check_path_rev = []
        self._current_check_node_value = None
        self._current_check_bf = None
        self._rotation_plan = None

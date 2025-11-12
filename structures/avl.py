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
        # 插入动画阶段：比较 -> 检查 -> 高亮提示 -> 旋转
        # 将高亮提示阶段时长扩展为原来的5倍，以便用户有更多时间观察失衡节点
        self._phase_breaks = (0.0279, 0.0558, 0.3058, 1.0)
        self._insert_committed = False    # 是否已将真实节点插入但未旋转
        self._rotation_applied = False    # 是否已执行计划中的旋转

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
        shadow_root = self._shadow_insert_no_rotate(shadow_root, v)  # 使用不旋转的版本，以便分析失衡节点
        self._rotation_plan = self._analyze_first_imbalance_and_rotation(shadow_root)
        self._insert_committed = False
        self._rotation_applied = False
        
        # 添加调试输出
        print(f"DEBUG - AVL Insert: value={v}")
        print(f"DEBUG - Insert path: {self._insert_path}")
        print(f"DEBUG - Rotation plan: {self._rotation_plan}")

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
            left_balance = self._get_balance_factor(node.left)
            if left_balance >= 0:
                # LL情况：左左（左子节点的左子树更高或等高）
                return self._rotate_right(node)
            else:
                # LR情况：左右（左子节点的右子树更高）
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node)
        
        elif balance < -1:  # 右子树过高
            right_balance = self._get_balance_factor(node.right)
            if right_balance <= 0:
                # RR情况：右右（右子节点的右子树更高或等高）
                return self._rotate_left(node)
            else:
                # RL情况：右左（右子节点的左子树更高）
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
            left_balance = self._get_balance_factor(node.left)
            if left_balance >= 0:
                # LL情况：左左（左子节点的左子树更高或等高）
                return self._rotate_right(node)
            else:
                # LR情况：左右（左子节点的右子树更高）
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node)
        if balance < -1:
            right_balance = self._get_balance_factor(node.right)
            if right_balance <= 0:
                # RR情况：右右（右子节点的右子树更高或等高）
                return self._rotate_left(node)
            else:
                # RL情况：右左（右子节点的左子树更高）
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node)
        return node

    def _shadow_insert_no_rotate(self, node, value):
        """影子插入，只插入和更新高度，不执行旋转（用于分析失衡节点）"""
        if not node:
            return self.Node(value)
        if value < node.value:
            node.left = self._shadow_insert_no_rotate(node.left, value)
        elif value > node.value:
            node.right = self._shadow_insert_no_rotate(node.right, value)
        self._update_height(node)
        return node  # 不执行旋转，直接返回

    def _analyze_first_imbalance_and_rotation(self, root_after):
        """分析首个失衡节点和旋转类型"""
        plan = None
        v = self._new_value
        
        # 从根开始，沿着插入路径找到第一个失衡节点
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
        
        # 从底向上检查，找到第一个失衡节点
        for node in reversed(path):
            bf = self._get_balance_factor(node)
            if abs(bf) > 1:
                # 找到失衡节点，判断旋转类型
                if bf > 1:  # 左子树更高
                    left_bf = self._get_balance_factor(node.left) if node.left else 0
                    if left_bf >= 0:
                        # LL型
                        plan = {
                            'type': 'LL',
                            'nodes': [node.value, node.left.value if node.left else None]
                        }
                    else:
                        # LR型
                        plan = {
                            'type': 'LR',
                            'nodes': [
                                node.value,
                                node.left.value if node.left else None,
                                node.left.right.value if (node.left and node.left.right) else None
                            ]
                        }
                else:  # bf < -1, 右子树更高
                    right_bf = self._get_balance_factor(node.right) if node.right else 0
                    if right_bf <= 0:
                        # RR型
                        plan = {
                            'type': 'RR',
                            'nodes': [node.value, node.right.value if node.right else None]
                        }
                    else:
                        # RL型
                        plan = {
                            'type': 'RL',
                            'nodes': [
                                node.value,
                                node.right.value if node.right else None,
                                node.right.left.value if (node.right and node.right.left) else None
                            ]
                        }
                break  # 只处理第一个失衡节点
        
        return plan

    def _ensure_insert_committed(self):
        """确保真实树已经执行插入但尚未旋转"""
        if self._insert_committed or self._new_value is None:
            return
        self.root = self._shadow_insert_no_rotate(self.root, self._new_value)
        self._insert_committed = True

    def has_pending_rotation(self):
        """是否存在待执行的旋转计划"""
        return bool(self._rotation_plan) and not self._rotation_applied

    def apply_pending_rotation(self):
        """执行待定的旋转计划，并在执行后清理计划"""
        if not self.has_pending_rotation():
            return False
        
        rotation_type = self._rotation_plan.get('type')
        plan_nodes = self._rotation_plan.get('nodes') or []
        pivot_value = plan_nodes[0] if plan_nodes else None
        
        if pivot_value is None or rotation_type is None:
            self._rotation_applied = True
            self._rotation_plan = None
            return False
        
        self.root = self._apply_rotation_at_node(self.root, pivot_value, rotation_type)
        self._rotation_applied = True
        # 保留旋转信息用于阶段提示
        self._rotation_type = rotation_type
        self._rotation_nodes = plan_nodes
        self._rotation_plan = None
        self._refresh_heights(self.root)
        return True

    def _apply_rotation_at_node(self, node, target_value, rotation_type):
        """在包含 target_value 的节点处执行指定类型的旋转"""
        if not node:
            return None
        
        if target_value < node.value:
            node.left = self._apply_rotation_at_node(node.left, target_value, rotation_type)
            self._update_height(node)
            return node
        if target_value > node.value:
            node.right = self._apply_rotation_at_node(node.right, target_value, rotation_type)
            self._update_height(node)
            return node
        
        # 当前节点即为失衡节点
        if rotation_type == 'LL':
            return self._rotate_right(node)
        if rotation_type == 'RR':
            return self._rotate_left(node)
        if rotation_type == 'LR':
            if node.left:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if rotation_type == 'RL':
            if node.right:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node

    def _refresh_heights(self, node):
        """重新计算整棵树的高度，确保旋转后数据一致"""
        if not node:
            return 0
        left_height = self._refresh_heights(node.left)
        right_height = self._refresh_heights(node.right)
        node.height = 1 + max(left_height, right_height)
        return node.height

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
        self.cancel_animation()

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

        # 从阶段2开始，真实树需要展示插入后的未旋转状态
        if prog >= p1:
            self._ensure_insert_committed()
        
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
        if self._rotation_plan and not self._rotation_applied:
            self._rotation_type = self._rotation_plan['type']
            self._rotation_nodes = self._rotation_plan['nodes']
        elif self._rotation_applied and self._rotation_type:
            # 已执行旋转，保持提示信息直到动画结束
            self._rotation_nodes = getattr(self, "_rotation_nodes", [])
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
            # 确保真实结构已经包含新节点
            self._ensure_insert_committed()
            # 若旋转尚未执行，作为兜底在动画结束时执行
            if self.has_pending_rotation():
                self.apply_pending_rotation()
            
            self._animation_state = None
            self._new_value = None
            self._insert_path = []
            self._current_insert_step = 0
            self._insert_comparison_result = None
            self._current_search_node_value = None
            self._current_check_node_value = None
            self._current_check_bf = None
            self._rotation_plan = None
            self._animation_progress = 0.0
            self._rotation_type = None
            self._rotation_nodes = []
            self._insert_committed = False
            self._rotation_applied = False

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
        self._insert_committed = False
        self._rotation_applied = False

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
        self._insert_committed = False
        self._rotation_applied = False

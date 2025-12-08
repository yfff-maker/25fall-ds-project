# -*- coding: utf-8 -*-
"""
哈夫曼树数据结构：纯业务逻辑 + 全新动画状态机
"""
from typing import Dict, List, Tuple, Optional
from .base import BaseStructure


class HuffmanTreeModel(BaseStructure):
    """哈夫曼树模型：同时承载动画状态"""

    class Node:
        def __init__(self, freq, char=None, left=None, right=None):
            self.freq = int(freq) if freq is not None else 0
            self.char = char
            self.left = left
            self.right = right

        def __repr__(self):
            return f"HuffNode({self.char or '*'}:{self.freq})"

    def __init__(self):
        super().__init__()
        self.root: Optional[HuffmanTreeModel.Node] = None
        self._reset_state()

    # ====== 基础与动画状态 ======
    def _reset_state(self):
        self._queue: List[HuffmanTreeModel.Node] = []
        self._animation_state: str = "idle"  # idle/select/move/merge/return/done
        self._animation_progress: float = 0.0
        self._current_pair: List[HuffmanTreeModel.Node] = []
        self._current_parent: Optional[HuffmanTreeModel.Node] = None
        self._queue_before: List[HuffmanTreeModel.Node] = []
        self._queue_after: List[HuffmanTreeModel.Node] = []
        self._round: int = 0
        self._total_rounds: int = 0
        self._original_freq_map: Dict[str, int] = {}

    def clear(self):
        """清空树与动画状态"""
        self.root = None
        self._reset_state()

    def build(self, freq_map: Dict[str, int]):
        """准备构建（动画驱动，暂不直接合并）"""
        if not self.active or not freq_map:
            self.clear()
            return
        self._reset_state()
        self._original_freq_map = dict(freq_map)
        # 队列按频率排序
        self._queue = [self.Node(v, char=k) for k, v in sorted(freq_map.items(), key=lambda x: x[1])]
        self._queue_before = list(self._queue)
        self._queue_after = list(self._queue)
        self._total_rounds = max(0, len(self._queue) - 1)
        self._animation_state = "idle"
        self._animation_progress = 0.0
        # 若只有一个节点，直接成为根
        if len(self._queue) == 1:
            self.root = self._queue[0]
            self._animation_state = "done"

    def start_animation(self) -> bool:
        """开启第一阶段动画；若无需动画返回 False"""
        if not self._queue:
            self._animation_state = "done"
            self.root = None
            return False
        if len(self._queue) == 1:
            self._animation_state = "done"
            self.root = self._queue[0]
            return False
        self._round = 0
        self._select_pair()
        self._animation_state = "select"
        self._animation_progress = 0.0
        return True

    def _select_pair(self):
        """选出当前轮的最小两项并记录队列快照"""
        self._queue.sort(key=lambda n: n.freq)
        self._queue_before = list(self._queue)
        self._current_pair = self._queue[:2] if len(self._queue) >= 2 else []
        self._current_parent = None
        self._queue_after = list(self._queue)

    def update_animation(self, progress: float):
        """由控制器驱动的阶段进度 [0,1]"""
        self._animation_progress = max(0.0, min(1.0, progress))

    def finish_phase(self):
        """当前阶段结束后切换到下一阶段并做必要的数据更新"""
        state = self._animation_state

        if state == "select":
            self._animation_state = "move"

        elif state == "move":
            self._animation_state = "merge"

        elif state == "merge":
            if len(self._current_pair) != 2:
                self._animation_state = "done"
            else:
                a, b = self._current_pair
                parent = self.Node(a.freq + b.freq, char=None, left=a, right=b)
                self._current_parent = parent

                # 计算父节点加入后的目标队列
                remaining = [n for n in self._queue_before if n not in (a, b)]
                insert_idx = 0
                for i, n in enumerate(remaining):
                    if parent.freq >= n.freq:
                        insert_idx = i + 1
                remaining.insert(insert_idx, parent)
                self._queue_after = remaining
                self._animation_state = "return"

        elif state == "return":
            # 真正合并队列
            if len(self._current_pair) == 2:
                for n in self._current_pair:
                    if n in self._queue:
                        self._queue.remove(n)
            if self._current_parent:
                inserted = False
                for i, n in enumerate(self._queue):
                    if self._current_parent.freq < n.freq:
                        self._queue.insert(i, self._current_parent)
                        inserted = True
                        break
                if not inserted:
                    self._queue.append(self._current_parent)

            # 收尾或进入下一轮
            if len(self._queue) == 1:
                self.root = self._queue[0]
                # 动画完成后清空队列，避免残留
                self._queue.clear()
                self._queue_before = []
                self._queue_after = []
                self._animation_state = "done"
                self._animation_progress = 1.0
            else:
                self._round += 1
                self._select_pair()
                self._animation_state = "select"

            # 仅在完成时清理；未完成需保留下一轮选择结果
            if self._animation_state == "done":
                self._current_pair = []
                self._current_parent = None
            self._queue_before = list(self._queue)
            self._queue_after = list(self._queue)

        self._animation_progress = 0.0

    # ====== 算法与编码 ======
    def _ensure_tree_ready(self):
        """若动画未跑完，快速构建一棵树用于编码/解码"""
        if self.root:
            return
        if not self._queue:
            return
        nodes = list(self._queue)
        nodes.sort(key=lambda n: n.freq)
        while len(nodes) > 1:
            a = nodes.pop(0)
            b = nodes.pop(0)
            parent = self.Node(a.freq + b.freq, char=None, left=a, right=b)
            # 按频率插回保持有序
            inserted = False
            for i, n in enumerate(nodes):
                if parent.freq < n.freq:
                    nodes.insert(i, parent)
                    inserted = True
                    break
            if not inserted:
                nodes.append(parent)
        self.root = nodes[0] if nodes else None

    def get_codes(self) -> Dict[str, str]:
        self._ensure_tree_ready()
        if not self.root:
            return {}
        codes: Dict[str, str] = {}
        self._generate_codes(self.root, "", codes)
        return codes

    def _generate_codes(self, node, code, codes: Dict[str, str]):
        if node is None:
            return
        if node.char is not None:
            codes[node.char] = code if code else "0"
        else:
            self._generate_codes(node.left, code + "0", codes)
            self._generate_codes(node.right, code + "1", codes)

    def encode(self, text: str) -> str:
        codes = self.get_codes()
        encoded = ""
        for ch in text:
            if ch not in codes:
                raise ValueError(f"字符 '{ch}' 不在哈夫曼树中")
            encoded += codes[ch]
        return encoded

    def decode(self, encoded_text: str) -> str:
        self._ensure_tree_ready()
        if not self.root:
            return ""
        result = ""
        cur = self.root
        for bit in encoded_text:
            cur = cur.left if bit == "0" else cur.right
            if cur.char is not None:
                result += cur.char
                cur = self.root
        return result

    # ====== 其它辅助 ======
    def is_empty(self) -> bool:
        return self.root is None

    def get_height(self):
        return self._get_height(self.root)

    def _get_height(self, node):
        if not node:
            return 0
        return 1 + max(self._get_height(node.left), self._get_height(node.right))

    # ====== 序列化 ======
    def _node_to_dict(self, node):
        if node is None:
            return None
        return {
            "freq": node.freq,
            "char": node.char,
            "left": self._node_to_dict(node.left),
            "right": self._node_to_dict(node.right),
        }

    def _dict_to_node(self, data):
        if not data:
            return None
        node = self.Node(data.get("freq"), char=data.get("char"))
        node.left = self._dict_to_node(data.get("left"))
        node.right = self._dict_to_node(data.get("right"))
        return node

    def to_dict(self) -> dict:
        payload = {}
        if self._original_freq_map:
            payload["freq_map"] = dict(self._original_freq_map)
        else:
            payload["root"] = self._node_to_dict(self.root)
        return payload

    def from_dict(self, data: dict) -> None:
        freq_map = data.get("freq_map")
        if freq_map:
            self.build(freq_map)
            self._ensure_tree_ready()
        else:
            self.root = self._dict_to_node(data.get("root"))
            self._reset_state()
            self._animation_state = "done" if self.root else "idle"
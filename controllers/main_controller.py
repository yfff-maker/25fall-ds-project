# -*- coding: utf-8 -*-
"""
主控制器：协调Model、View和用户交互
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from structures.sequential_list import SequentialListModel
from structures.linked_list import LinkedListModel
from structures.stack import StackModel
from structures.binary_tree import BinaryTreeModel
from structures.bst import BSTModel
from structures.avl import AVLModel
from structures.huffman import HuffmanTreeModel
from collections import deque
from .adapters import (
    SequentialListAdapter, LinkedListAdapter, StackAdapter,
    BinaryTreeAdapter, BSTAdapter, AVLAdapter, HuffmanTreeAdapter,
    StructureSnapshot, center_snapshot
)
from .dsl_parser import DSLParser
from .dsl_executor import DSLExecutor
from .llm_service import LLMService
from .action_executor import ActionExecutor

class _HuffNode:
    """轻量节点类，用于控制器临时维护队列和树"""
    def __init__(self, char, freq, left=None, right=None):
        self.char = char
        self.freq = int(freq) if freq is not None else 0
        self.left = left
        self.right = right

class MainController(QObject):
    """主控制器类"""
    
    # 信号定义
    snapshot_updated = pyqtSignal(object)  # 快照更新信号
    hint_updated = pyqtSignal(str)  # 提示更新信号
    operation_logged = pyqtSignal(str)  # 操作记录信号
    operation_log_cleared = pyqtSignal()  # 日志清空信号
    parent_selection_requested = pyqtSignal(str)  # 请求父节点选择
    
    def __init__(self):
        super().__init__()
        
        # 初始化数据结构模型
        self.structures = {
            "SequentialList": SequentialListModel(),
            "LinkedList": LinkedListModel(),
            "Stack": StackModel(),
            "BinaryTree": BinaryTreeModel(),
            "BST": BSTModel(),
            "AVL": AVLModel(),
            "HuffmanTree": HuffmanTreeModel(),
        }
        
        # 激活所有数据结构
        for structure in self.structures.values():
            structure.set_active(True)
        
        # 适配器映射
        self.adapters = {
            "SequentialList": SequentialListAdapter(),
            "LinkedList": LinkedListAdapter(),
            "Stack": StackAdapter(),
            "BinaryTree": BinaryTreeAdapter(),
            "BST": BSTAdapter(),
            "AVL": AVLAdapter(),
            "HuffmanTree": HuffmanTreeAdapter(),
        }
        
        self.current_structure_key = "SequentialList"
        self._huffman_animation_paused = False  # 哈夫曼树动画暂停状态
        self._huffman_animation_paused_time = 0  # 暂停时的时间
        self._huffman_animation_pause_offset = 0  # 暂停时间偏移
        self._bst_build_queue = []  # BST批量构建队列
        self._avl_build_queue = []  # AVL批量构建队列
        self._operation_logs: List[str] = []
        
        # 初始化DSL解析器和执行器
        self.dsl_parser = DSLParser()
        self.dsl_executor = DSLExecutor(self)
        
        # 初始化LLM服务和动作执行器
        self.llm_service = LLMService()
        self.action_executor = ActionExecutor(self)
        self.llm_context_actions: List[Dict[str, Any]] = []  # 供LLM参考的已有操作上下文
        self._animation_timer: Optional[QTimer] = None
        self._animation_paused: bool = False
        self._paused_elapsed: float = 0.0  # 毫秒
        self.current_llm_model: Optional[str] = self.llm_service.default_model
        # 动画倍速（0.5/1/1.5/2），影响所有统一定时器与持续时间
        self._speed_multiplier: float = 1.0
        self._current_base_interval: int = 0  # 记录最近一次启动定时器的基准间隔
        
        self._update_snapshot()

    # ========== LLM 上下文：构造更可靠的 prompt 输入 ==========
    def _build_llm_prompt_context(self) -> List[Dict[str, Any]]:
        """
        构造传给 LLM 的上下文。
        - 基础：self.llm_context_actions（按时间追加的动作历史）
        - 追加：当前结构的“有效状态 state”（优先用于推断，例如链表的 elements）
        """
        base = list(getattr(self, "llm_context_actions", []) or [])
        state_entry = self._build_llm_state_entry()
        if state_entry:
            base.append(state_entry)
        return base

    def _build_llm_state_entry(self) -> Optional[Dict[str, Any]]:
        """
        为当前结构生成一条 operation='state' 的上下文项，尽量反映“视觉上/用户认为”的当前状态。
        目前重点覆盖 LinkedList（解决“最后一个位置”随插入/删除不更新的问题）。
        """
        key = getattr(self, "current_structure_key", None)
        if not key or key not in getattr(self, "structures", {}):
            return None
        try:
            struct = self.structures[key]
        except Exception:
            return None

        # 链表：给出当前有效 elements（包含动画中尚未提交的数据变化）
        if key == "LinkedList":
            try:
                base_elems = []
                data = getattr(struct, "data", None)
                if data is not None:
                    if hasattr(data, "to_array"):
                        base_elems = list(data.to_array())
                    else:
                        base_elems = list(data)
                state = getattr(struct, "_animation_state", None)
                effective = list(base_elems)

                # 构建动画：以目标 build_values 为准（更符合用户认知）
                if state == "building" and hasattr(struct, "_build_values"):
                    effective = list(getattr(struct, "_build_values") or [])
                # 插入动画：data 尚未插入，但画面上已经出现新节点 → 反映到 effective
                elif state == "inserting":
                    pos = int(getattr(struct, "_insert_position", 0) or 0)
                    val = getattr(struct, "_new_value", None)
                    if val is not None:
                        pos = max(0, min(pos, len(effective)))
                        effective.insert(pos, val)
                # 删除动画：data 尚未删除，但画面上该节点已被标记移除 → 反映到 effective
                elif state == "deleting":
                    pos = int(getattr(struct, "_delete_position", -1) or -1)
                    if 0 <= pos < len(effective):
                        effective.pop(pos)

                return {
                    "structure_type": "LinkedList",
                    "operation": "state",
                    "parameters": {
                        "elements": [str(x) for x in effective],
                        "note": "当前链表有效状态（包含动画中未提交的插入/删除变化），用于推断诸如“最后一个位置”等相对位置。",
                    },
                }
            except Exception:
                return None

        # 顺序表：同样给出当前有效 elements（包含动画中未提交的插入/删除变化）
        if key == "SequentialList":
            try:
                base_elems = []
                data = getattr(struct, "data", None)
                if data is not None:
                    # SequentialArray 支持迭代（__iter__），to_list() 也是生成器
                    if hasattr(data, "to_list"):
                        base_elems = list(data.to_list())
                    else:
                        base_elems = list(data)
                state = getattr(struct, "_animation_state", None)
                effective = list(base_elems)

                if state == "inserting":
                    pos = int(getattr(struct, "_insert_position", 0) or 0)
                    val = getattr(struct, "_new_value", None)
                    if val is not None:
                        pos = max(0, min(pos, len(effective)))
                        effective.insert(pos, val)
                elif state == "deleting":
                    pos = int(getattr(struct, "_delete_position", -1) or -1)
                    if 0 <= pos < len(effective):
                        effective.pop(pos)

                return {
                    "structure_type": "SequentialList",
                    "operation": "state",
                    "parameters": {
                        "elements": [str(x) for x in effective],
                        "note": "当前顺序表有效状态（包含动画中未提交的插入/删除变化），用于推断诸如“最后一个位置”等相对位置。",
                    },
                }
            except Exception:
                return None

        return None

    @staticmethod
    def _normalize_position_from_user_text(user_input: str, action: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        统一“第N个位置”的口径为 0-based：用户写第N个位置 => action.parameters.position 强制为 N。
        主要用于避免 LLM 偶尔按 1-based（把第4个位置当 index=3）解读。
        """
        if not action or not isinstance(action, dict) or not isinstance(user_input, str):
            return action
        params = action.get("parameters", {})
        if not isinstance(params, dict) or "position" not in params:
            return action

        try:
            import re
            m = re.search(r"第\s*(\d+)\s*个?\s*位置", user_input)
            if not m:
                return action
            pos = int(m.group(1))
            if pos < 0:
                return action
            params["position"] = pos
            action["parameters"] = params
            return action
        except Exception:
            return action
    
    # ====== 序列化：保存/加载 ======
    def save_to_file(self, path: str) -> None:
        """保存当前所有数据结构状态到 .dsv(JSON) 文件"""
        try:
            data = {
                "version": 1,
                "current_structure_key": self.current_structure_key,
                "structures": {
                    key: struct.to_dict() for key, struct in self.structures.items()
                }
            }
            import json
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.hint_updated.emit(f"已保存到: {path}")
        except Exception as e:
            self._show_error("保存失败", str(e))

    def load_from_file(self, path: str) -> None:
        """从 .dsv(JSON) 文件加载数据结构状态"""
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict) or data.get("version") != 1:
                raise ValueError("文件版本不兼容或格式错误")

            # 恢复各结构
            structures_payload = data.get("structures", {}) or {}
            for key, struct in self.structures.items():
                payload = structures_payload.get(key)
                if payload is not None:
                    struct.from_dict(payload)
                else:
                    # 如果缺失，重置为空状态
                    if hasattr(struct, 'clear'):
                        struct.clear()

            # 恢复当前结构选择
            key = data.get("current_structure_key")
            if key in self.structures:
                self.current_structure_key = key

            # 刷新视图
            self._update_snapshot()
            self.hint_updated.emit(f"已从文件加载: {path}")
        except Exception as e:
            self._show_error("加载失败", str(e))

    def select_structure(self, key: str):
        """选择数据结构"""
        if key in self.structures:
            self.current_structure_key = key
            self._update_snapshot()
            self.hint_updated.emit(f"当前模式：{key}")
    
    def _update_snapshot(self):
        """更新当前快照"""
        if self.current_structure_key in self.structures:
            structure = self.structures[self.current_structure_key]
            adapter = self.adapters[self.current_structure_key]
            snapshot = adapter.to_snapshot(structure) # ← 创建：通过适配器创建 StructureSnapshot
            self.snapshot_updated.emit(snapshot)
    
    def _get_current_structure(self):
        """获取当前数据结构"""
        return self.structures.get(self.current_structure_key) # ← 依赖：使用数据结构实例
    
    def _get_current_adapter(self):
        """获取当前适配器"""
        return self.adapters.get(self.current_structure_key)
    
    def is_busy(self) -> bool:
        """判断是否仍有动画或批量任务在执行"""
        if self._animation_timer and self._animation_timer.isActive():
            return True
        if getattr(self, "_bst_build_queue", None):
            if len(self._bst_build_queue) > 0:
                return True
        if getattr(self, "_avl_build_queue", None):
            if len(self._avl_build_queue) > 0:
                return True
        huffman_queue = getattr(self, "_huffman_queue", None)
        if huffman_queue and len(huffman_queue) > 1:
            huffman_struct = self.structures.get("HuffmanTree")
            if huffman_struct and getattr(huffman_struct, "_animation_state", None) == "huffman_merging":
                return True
        return False
    
    def _restart_animation_timer(self, callback, interval: int = 50):
        """停止旧定时器并以新的回调/间隔重新启动"""
        if self._animation_timer is None:
            self._animation_timer = QTimer(self)
        else:
            self._animation_timer.stop()
            try:
                self._animation_timer.timeout.disconnect()
            except TypeError:
                pass
        # 重置暂停状态
        self._animation_paused = False
        self._paused_elapsed = 0.0
        self._animation_timer.timeout.connect(callback)
        self._current_base_interval = interval
        effective_interval = self._apply_speed_interval(interval)
        self._animation_timer.start(effective_interval)

    def _apply_speed_interval(self, base_interval: int) -> int:
        """根据倍速调整定时器间隔（倍速大→间隔小，默认1x不变）"""
        base = max(1, int(base_interval))
        speed = max(0.1, float(self._speed_multiplier))
        return max(5, int(base / speed))

    def _calc_progress(self, elapsed: float) -> float:
        """将耗时转换为进度，受倍速影响"""
        duration = max(1.0, float(self._animation_duration))
        speed = max(0.1, float(self._speed_multiplier))
        return min((elapsed * speed) / duration, 1.0)
    
    def pause_current_animation(self):
        """通用暂停：哈夫曼走专用逻辑，其它结构暂停统一定时器"""
        if self.current_structure_key == "HuffmanTree":
            self.pause_huffman_animation()
            return
        timer = getattr(self, "_animation_timer", None)
        if timer and timer.isActive():
            import time
            now = time.time() * 1000.0
            if self._animation_start_time:
                self._paused_elapsed = now - self._animation_start_time
            else:
                self._paused_elapsed = 0.0
            self._animation_paused = True
            timer.stop()
            self.hint_updated.emit("动画已暂停")
    
    def resume_current_animation(self):
        """通用继续播放：哈夫曼走专用逻辑，其它结构恢复统一定时器"""
        if self.current_structure_key == "HuffmanTree":
            self.resume_huffman_animation()
            return
        timer = getattr(self, "_animation_timer", None)
        if timer and not timer.isActive():
            import time
            now = time.time() * 1000.0
            self._animation_start_time = now - (self._paused_elapsed or 0.0)
            self._animation_paused = False
            self._paused_elapsed = 0.0
            timer.start(timer.interval())
            self.hint_updated.emit("动画已恢复")
    
    # ========== 顺序表操作 ==========
    
    def build_sequential_list(self, input_text: str):
        """构建顺序表"""
        try:
            data = self._parse_comma_separated_values(input_text)
            values_list = list(data)
            structure = self._get_current_structure()
            if structure:
                # 先清空，防止同样数据不触发重绘
                if hasattr(structure, "clear"):
                    structure.clear()
                structure.build(values_list)
                self._update_snapshot()
                text_repr = input_text.strip() if isinstance(input_text, str) else str(input_text)
                self._pending_llm_action = {
                    "structure_type": "SequentialList",
                    "operation": "create",
                    "parameters": {"values": values_list},
                }
                self.log_operation(f"[顺序表] 构建数据: {text_repr or '(空)'}")
        except Exception as e:
            self._show_error("构建顺序表失败", str(e))
    
    def insert_at_sequential_list(self, position: int, value: str):
        """在指定位置插入元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 开始插入动画
                structure.insert_at(position, value)
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "SequentialList",
                    "operation": "insert",
                    "parameters": {"position": position, "value": value},
                }
                self.log_operation(f"[顺序表] 在位置 {position} 插入值 {value}")
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_sequential_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("插入失败", str(e))
    
    def delete_at_sequential_list(self, position: int):
        """删除指定位置的元素"""
        try:
            structure = self._get_current_structure()
            if structure:
                # 开始删除动画
                structure.delete_at(position)
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "SequentialList",
                    "operation": "delete",
                    "parameters": {"position": position},
                }
                self.log_operation(f"[顺序表] 删除位置 {position} 的元素")
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_sequential_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("删除失败", str(e))
    
    def insert_at_head_sequential_list(self, value: str):
        """在头部插入元素"""
        self.insert_at_sequential_list(0, value)
    
    def insert_at_tail_sequential_list(self, value: str):
        """在尾部插入元素"""
        self.insert_at_sequential_list(len(self._get_current_structure().data), value)
    
    def _update_sequential_animation(self, structure):
        """更新顺序表平滑动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            self._animation_paused = False
            self._paused_elapsed = 0.0
            # 根据动画状态完成相应操作
            if structure._animation_state == 'inserting':
                structure.complete_insert_animation()
            elif structure._animation_state == 'deleting':
                structure.complete_delete_animation()
            self._update_snapshot()
    
    # ========== 链表操作 ==========
    
    def build_linked_list(self, input_text: str):
        """构建链表"""
        try:
            data_generator = self._parse_comma_separated_values(input_text)
            values_list = list(data_generator)
            structure = self._get_current_structure()
            if structure:
                if hasattr(structure, "clear"):
                    structure.clear()
                # 开始构建动画
                structure.build(values_list)
                self._update_snapshot()
                text_repr = input_text.strip() if isinstance(input_text, str) else str(input_text)
                self._pending_llm_action = {
                    "structure_type": "LinkedList",
                    "operation": "create",
                    "parameters": {"values": values_list},
                }
                self.log_operation(f"[链表] 构建数据: {text_repr or '(空)'}")
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_linked_list_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
        except Exception as e:
            self._show_error("构建链表失败", str(e))
    
    def insert_at_linked_list(self, position: int, value: str):
        """在指定位置插入元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 开始插入动画
                structure.insert(position, value)
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "LinkedList",
                    "operation": "insert",
                    "parameters": {"position": position, "value": value},
                }
                self.log_operation(f"[链表] 在位置 {position} 插入值 {value}")
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_linked_list_animation(structure), 100)
                
                # 设置动画总时长
                self._animation_duration = 2000  # 2秒总时长
                self._animation_start_time = 0
        except Exception as e:
            self._show_error("插入失败", str(e))
    
    def delete_at_linked_list(self, position: int):
        """删除指定位置的元素"""
        try:
            structure = self._get_current_structure()
            if structure:
                # 启动删除动画
                structure.delete_at(position)
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "LinkedList",
                    "operation": "delete",
                    "parameters": {"position": position},
                }
                self.log_operation(f"[链表] 删除位置 {position} 的元素")
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_linked_list_animation(structure), 100)
                
                # 设置动画总时长
                self._animation_duration = 2000  # 放慢：动画总时长 2000ms
                self._animation_start_time = 0
        except Exception as e:
            self._show_error("删除失败", str(e))
    
    def insert_at_head_linked_list(self, value: str):
        """在头部插入元素"""
        self.insert_at_linked_list(0, value)
    
    def insert_at_tail_linked_list(self, value: str):
        """在尾部插入元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 记录插入发生时的“尾部位置”（等价于 len_before）
                try:
                    len_before = len(getattr(structure, "data", []))
                except Exception:
                    try:
                        len_before = int(structure.size())
                    except Exception:
                        len_before = None

                structure.insert_at_end(value)
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "LinkedList",
                    # 统一用 insert，便于 LLM 复原状态
                    "operation": "insert",
                    "parameters": (
                        {"position": int(len_before), "value": value}
                        if isinstance(len_before, int) and len_before >= 0
                        else {"value": value}
                    ),
                }
                self.log_operation(f"[链表] 在尾部插入值 {value}")
        except Exception as e:
            self._show_error("尾部插入失败", str(e))
    
    def delete_by_value_linked_list(self, value: str):
        """按值删除元素"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 尽量转换为 delete(position)，避免 LLM 不认识 delete_by_value
                pos = None
                try:
                    data = getattr(structure, "data", None)
                    if data is not None and hasattr(data, "get"):
                        pos = data.get(value)  # CustomList.get(value) -> index
                except Exception:
                    pos = None

                structure.delete_by_value(value)
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "LinkedList",
                    "operation": "delete",
                    "parameters": (
                        {"position": int(pos)}
                        if isinstance(pos, int) and pos >= 0
                        else {"value": value}
                    ),
                }
                self.log_operation(f"[链表] 删除值 {value}")
        except Exception as e:
            self._show_error("按值删除失败", str(e))
    
    # ========== 栈操作 ==========
    
    def push_stack(self, value: str):
        """入栈"""
        try:
            structure = self._get_current_structure()
            if structure and value:
                # 开始入栈动画
                structure.push(value)
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "Stack",
                    "operation": "push",
                    "parameters": {"value": value},
                }
                self.log_operation(f"[栈] Push 值 {value}")
                
                # 检查是否是栈满状态
                if getattr(structure, '_animation_state', None) == 'stack_full':
                    self._show_error("栈已满！", "无法添加更多元素，栈容量为10")
                    return
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_smooth_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("入栈失败", str(e))
    
    def _update_smooth_animation(self, structure):
        """更新平滑动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            self._animation_paused = False
            self._paused_elapsed = 0.0
            if structure._animation_state == 'pushing':
                structure.complete_push_animation()
            elif structure._animation_state == 'popping':
                structure.complete_pop_animation()
            self._update_snapshot()
    
    def _update_stack_animation(self, structure):
        """更新栈动画（入栈和出栈）"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            if structure._animation_state == 'pushing':
                structure.complete_push_animation()
            elif structure._animation_state == 'popping':
                structure.complete_pop_animation()
            self._update_snapshot()
    
    def _update_binary_tree_animation(self, structure):
        """更新二叉树动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            if structure._animation_state == 'creating_root':
                # 创建根节点
                structure.root = structure.Node(structure._new_value)
                structure._animation_state = None
                structure._animation_progress = 0.0
                structure._new_value = None
            elif structure._animation_state == 'inserting':
                # 插入新节点
                if structure._parent_value and structure._insert_position:
                    parent_node = structure.find_node_by_value(structure._parent_value)
                    if parent_node:
                        new_node = structure.Node(structure._new_value)
                        if structure._insert_position == 'left':
                            parent_node.left = new_node
                        else:  # right
                            parent_node.right = new_node
                
                structure._animation_state = None
                structure._animation_progress = 0.0
                structure._new_value = None
                structure._parent_value = None
                structure._insert_position = None
            
            # 最终更新显示
            self._update_snapshot()
    
    def _update_bst_animation(self, structure):
        """更新BST动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        
        # 根据动画状态选择不同的更新方法
        if structure._animation_state == 'inserting':
            structure.update_insert_animation(progress)
        else:
            structure.update_animation_progress(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            
            # 调用complete_insert_animation()来正确完成插入操作
            # 这会使用BST的递归插入逻辑，而不是手动插入
            if structure._animation_state in ['creating_root', 'inserting']:
                structure.complete_insert_animation()
            
            # 重置动画计时器，确保下一个节点的动画能正确计时
            self._animation_start_time = 0
            
            # 最终更新显示
            self._update_snapshot()
            
            # 保存队列状态，稍后继续执行队列
            has_next = bool(self._bst_build_queue)
            
            # 清理定时器
            old_timer = self._animation_timer
            self._animation_timer = None  # 先清空引用
            if old_timer is not None:
                old_timer.stop()
            
            # 检查是否有待插入的BST节点（批量构建）
            # 使用QTimer.singleShot延迟一小段时间，确保前一个定时器完全清理
            if has_next:
                QTimer.singleShot(100, self._insert_next_bst_value)
    
    def _insert_next_bst_value(self):
        """插入BST批量构建队列中的下一个值"""
        if not self._bst_build_queue:
            return
        
        next_value = self._bst_build_queue.pop(0)
        self.insert_bst(next_value)
    
    def _insert_next_avl_value(self):
        """插入AVL批量构建队列中的下一个值"""
        try:
            if not self._avl_build_queue:
                return
            
            next_value = self._avl_build_queue.pop(0)
            self.insert_avl(next_value)
        except Exception as e:
            # 异常时继续处理队列，不中断批量构建
            self._show_error("插入节点失败", str(e))
            if self._avl_build_queue:
                QTimer.singleShot(100, self._insert_next_avl_value)
    
    def build_bst(self, values):
        """批量构建BST（自动顺序插入动画）"""
        try:
            if not values:
                self._show_warning("请输入要构建的节点值")
                return
            
            structure = self._get_current_structure()
            if not structure:
                self._show_error("构建失败", "BST结构不存在")
                return
            if hasattr(structure, "clear"):
                structure.clear()
            # 清空旧BST，确保同样数据也会重绘
            if hasattr(structure, "clear"):
                structure.clear()
            
            # 初始化队列
            self._bst_build_queue = list(values) if isinstance(values, list) else [v.strip() for v in str(values).split(',') if v.strip()]
            
            if not self._bst_build_queue:
                self._show_warning("请输入有效的节点值")
                return
            self._pending_llm_action = {
                "structure_type": "BST",
                "operation": "build",
                "parameters": {"values": list(self._bst_build_queue)},
            }
            self.log_operation(f"[BST] 批量构建: {', '.join(str(v) for v in self._bst_build_queue)}")
            
            # 立即更新视图，确保切换到BST视图可见（即使树为空）
            self._update_snapshot()
            
            # 开始插入第一个节点
            self._insert_next_bst_value()
            
        except Exception as e:
            self._show_error("构建失败", str(e))
            self._bst_build_queue = []  # 清空队列
    
    def build_avl(self, values):
        """批量构建AVL树（自动顺序插入动画）"""
        try:
            if not values:
                self._show_warning("请输入要构建的节点值")
                return
            
            structure = self.structures.get("AVL")
            if not structure:
                self._show_error("构建失败", "AVL结构不存在")
                return
            if hasattr(structure, "clear"):
                structure.clear()
            
            # 如果已有批量构建在进行，先停止当前动画
            timer = getattr(self, '_animation_timer', None)
            if timer is not None:
                timer.stop()
                self._animation_timer = None
            
            # 初始化队列
            self._avl_build_queue = list(values) if isinstance(values, list) else [v.strip() for v in str(values).split(',') if v.strip()]
            
            if not self._avl_build_queue:
                self._show_warning("请输入有效的节点值")
                return
            self._pending_llm_action = {
                "structure_type": "AVL",
                "operation": "build",
                "parameters": {"values": list(self._avl_build_queue)},
            }
            self.log_operation(f"[AVL] 批量构建: {', '.join(str(v) for v in self._avl_build_queue)}")
            
            # 立即更新视图，确保切换到AVL视图可见（即使树为空）
            self._update_snapshot()
            
            # 开始插入第一个节点
            self._insert_next_avl_value()
            
        except Exception as e:
            self._show_error("构建失败", str(e))
            self._avl_build_queue = []  # 清空队列
            # 清理定时器
            timer = getattr(self, '_animation_timer', None)
            if timer is not None:
                timer.stop()
                self._animation_timer = None
    
    def pop_stack(self):
        """出栈"""
        try:
            structure = self._get_current_structure()
            if structure:
                # 开始出栈动画
                structure.pop()
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "Stack",
                    "operation": "pop",
                    "parameters": {},
                }
                self.log_operation("[栈] Pop 栈顶元素")
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_stack_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("出栈失败", str(e))
    
    def clear_stack(self):
        """清空栈"""
        try:
            structure = self._get_current_structure()
            if structure:
                structure.clear()
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "Stack",
                    "operation": "clear",
                    "parameters": {},
                }
                self.log_operation("[栈] 清空所有元素")
        except Exception as e:
            self._show_error("清空栈失败", str(e))
    
    def build_stack(self, input_text: str):
        """构建栈"""
        try:
            data = self._parse_comma_separated_values(input_text)
            structure = self._get_current_structure()
            if structure:
                if hasattr(structure, "clear"):
                    structure.clear()
                # 开始构建动画
                data_list = list(data)
                structure.build(data_list)
                self._update_snapshot()
                text_repr = input_text.strip() if isinstance(input_text, str) else str(input_text)
                self._pending_llm_action = {
                    "structure_type": "Stack",
                    "operation": "create",
                    "parameters": {"values": data_list},
                }
                self.log_operation(f"[栈] 批量构建: {text_repr or '(空)'}")
                
                # 检查是否是栈满状态
                if getattr(structure, '_animation_state', None) == 'stack_full':
                    self._show_error("栈已满！", "无法添加更多元素，栈容量为10")
                    return
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_stack_build_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
        except Exception as e:
            self._show_error("构建栈失败", str(e))

    def peek_stack(self) -> Optional[str]:
        """查看当前栈顶元素（不修改栈）"""
        try:
            structure = self._get_current_structure()
            if not structure:
                return None
            # 统一用模型的 peek
            v = structure.peek()
            return None if v is None else str(v)
        except Exception:
            return None
    
    def _update_stack_build_animation(self, structure):
        """更新栈构建动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_animation_progress(progress)
        
        # 处理构建动画的逐步显示
        if structure._animation_state == 'building':
            build_values = getattr(structure, '_build_values', [])
            total_elements = len(build_values)
            if total_elements > 0:
                # 计算当前应该显示到第几个元素
                current_element_index = int(progress * total_elements)
                structure._build_index = current_element_index
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            self._animation_paused = False
            self._paused_elapsed = 0.0
            if structure._animation_state == 'building':
                structure.complete_build_animation()
            self._update_snapshot()
    
    # ========== 二叉树操作 ==========
    
    def insert_binary_tree_node(self, value: str, parent_value: str = None):
        """插入二叉树节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if not structure:
                return
            
            # 如果没有根节点，自动创建
            if structure.root is None:
                # 开始创建根节点动画
                structure._animation_state = 'creating_root'
                structure._animation_progress = 0.0
                structure._new_value = value
                structure._new_node = None  # 根节点还没有创建
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_binary_tree_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
                self._update_snapshot()
                self.log_operation(f"[二叉树] 创建根节点 {value}")
                return
            
            # 如果有父节点值，开始插入动画
            if parent_value:
                # 确定插入位置（左孩子优先）
                parent_node = structure.find_node_by_value(parent_value)
                if parent_node:
                    if parent_node.left is None:
                        position = 'left'
                    elif parent_node.right is None:
                        position = 'right'
                    else:
                        self._show_warning(f"节点 {parent_value} 已有两个孩子，无法继续添加")
                        return
                    
                    # 开始插入动画
                    structure.start_insert_animation(value, parent_value, position)
                    
                    # 使用定时器实现平滑动画
                    self._restart_animation_timer(lambda: self._update_binary_tree_animation(structure), 50)
                    
                    # 设置动画总时长
                    self._animation_duration = 1000  # 1秒总时长
                    self._animation_start_time = 0
                    
                    self._update_snapshot()
                    self._pending_llm_action = {
                        "structure_type": "BinaryTree",
                        "operation": "insert",
                        "parameters": {"value": value, "parent_value": parent_value, "position": position},
                    }
                    self.log_operation(f"[二叉树] 在节点 {parent_value} 的{position}子节点插入 {value}")
            else:
                # 需要用户选择父节点
                self._request_parent_selection(value)
                
        except Exception as e:
            self._show_error("插入节点失败", str(e))
    
    def traverse_binary_tree(self, order: str):
        """遍历二叉树"""
        try:
            structure = self._get_current_structure()
            if structure:
                structure.traverse(order)
                self._update_snapshot()
        except Exception as e:
            self._show_error("遍历失败", str(e))
    
    def _request_parent_selection(self, value: str):
        """请求父节点选择（需要UI支持）"""
        # 这个方法需要与UI层交互，暂时抛出信号
        self.parent_selection_requested.emit(value)
    
    def build_binary_tree(self, values):
        """层序构建二叉树（批量插入）"""
        try:
            structure = self.structures.get("BinaryTree")
            if not structure:
                return
            
            # 清空旧树，防止相同数据不触发刷新或残留旧形状
            if hasattr(structure, "clear"):
                structure.clear()
            
            # 如果tree为空，先创建根节点
            if structure.root is None and values:
                value = values[0]
                structure.root = BinaryTreeModel.Node(value)
                self._update_snapshot()
                
                # 如果只有一个值，直接返回
                if len(values) == 1:
                    return
                
                # 从第二个值开始插入
                remaining_values = values[1:]
            else:
                remaining_values = values
            
            # 使用队列进行层序插入
            for value in remaining_values:
                # 每次都重新构建队列，从根开始查找
                queue = deque([structure.root])
                found_parent = None
                
                while queue:
                    parent = queue.popleft()
                    
                    # 左子节点为空
                    if parent.left is None:
                        parent.left = BinaryTreeModel.Node(value)
                        found_parent = parent
                        break
                    
                    # 右子节点为空
                    elif parent.right is None:
                        parent.right = BinaryTreeModel.Node(value)
                        found_parent = parent
                        break
                    
                    # 如果左右都不为空，加入队列继续查找
                    queue.append(parent.left)
                    queue.append(parent.right)
                
                # 如果没找到合适的父节点，说明树已经满了或异常
                if not found_parent:
                    self._show_error("构建失败", f"无法为值 {value} 找到合适的插入位置")
                    break
            
            self._update_snapshot()
            self._pending_llm_action = {
                "structure_type": "BinaryTree",
                "operation": "build_level",
                "parameters": {"values": list(values)},
            }
            self.log_operation(f"[二叉树] 层序构建: {', '.join(map(str, values))}")
            
        except Exception as e:
            self._show_error("构建失败", str(e))
    
    def insert_binary_tree_with_position(self, value: str, parent_value: str, position: str):
        """插入二叉树节点（指定位置）"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self.structures.get("BinaryTree")
            if not structure:
                self._show_error("插入失败", "二叉树结构不存在")
                return
            
            # 验证position参数
            if position.lower() not in ['left', 'right']:
                self._show_error("插入失败", f"无效的位置参数: {position}，只接受 'left' 或 'right'")
                return
            
            # 查找父节点
            parent_node = structure.find_node_by_value(parent_value)
            if not parent_node:
                self._show_error("插入失败", f"未找到父节点: {parent_value}")
                return
            
            # 检查指定位置是否已有子节点
            position = position.lower()
            if position == 'left' and parent_node.left is not None:
                self._show_error("插入失败", f"节点 {parent_value} 的左子节点已存在")
                return
            if position == 'right' and parent_node.right is not None:
                self._show_error("插入失败", f"节点 {parent_value} 的右子节点已存在")
                return
            
            # 开始插入动画
            structure.start_insert_animation(value, parent_value, position)
            
            # 使用定时器实现平滑动画
            self._restart_animation_timer(lambda: self._update_binary_tree_animation(structure), 50)
            
            # 设置动画总时长
            self._animation_duration = 1000  # 1秒总时长
            self._animation_start_time = 0
            
            self._update_snapshot()
            self._pending_llm_action = {
                "structure_type": "BinaryTree",
                "operation": "insert",
                "parameters": {"value": value, "parent_value": parent_value, "position": position},
            }
            self.log_operation(f"[二叉树] 在节点 {parent_value} 的{position}侧插入 {value}")
            
        except Exception as e:
            self._show_error("插入失败", str(e))
    
    def delete_binary_tree(self, value: str):
        """删除二叉树节点及其子树"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self.structures.get("BinaryTree")
            if not structure:
                self._show_error("删除失败", "二叉树结构不存在")
                return
            
            # 检查节点是否存在
            target_node = structure.find_node_by_value(value)
            if not target_node:
                self._show_error("删除失败", f"未找到节点: {value}")
                return
            
            # 执行删除
            success = structure.delete_node(value)
            if success:
                self._update_snapshot()
                self.hint_updated.emit(f"已删除节点: {value} 及其子树")
                self._pending_llm_action = {
                    "structure_type": "BinaryTree",
                    "operation": "delete",
                    "parameters": {"value": value},
                }
                self.log_operation(f"[二叉树] 删除节点 {value} 及其子树")
            else:
                self._show_error("删除失败", "删除操作失败")
                
        except Exception as e:
            self._show_error("删除失败", str(e))
    
    # ========== BST操作 ==========
    
    def insert_bst(self, value: str):
        """插入BST节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if structure:
                # 开始插入动画
                structure.insert(value)
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_bst_animation(structure), 50)
                
                # 设置动画总时长
                self._animation_duration = 1000  # 1秒总时长
                self._animation_start_time = 0
                
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "BST",
                    "operation": "insert",
                    "parameters": {"value": value},
                }
                self.log_operation(f"[BST] 插入节点 {value}")
        except Exception as e:
            self._show_error("插入失败", str(e))
    
    def search_bst(self, value: str):
        """搜索BST节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if structure:
                # 开始查找动画
                if structure.search_with_animation(value):
                    # 使用定时器实现平滑动画
                    self._restart_animation_timer(lambda: self._update_bst_search_animation(structure), 50)
                    
                    # 设置动画总时长
                    self._animation_duration = 2000  # 2秒总时长（查找需要更多时间）
                    self._animation_start_time = 0
                    
                    self._update_snapshot()
                    self._pending_llm_action = {
                        "structure_type": "BST",
                        "operation": "search",
                        "parameters": {"value": value},
                    }
                    self.log_operation(f"[BST] 搜索节点 {value}")
                else:
                    self._show_warning("树为空或值无效")
        except Exception as e:
            self._show_error("搜索失败", str(e))
    
    def _update_bst_search_animation(self, structure):
        """更新BST查找动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_search_animation(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器
        if progress >= 1.0:
            self._animation_timer.stop()
            structure.complete_search_animation()
            
            # 显示查找结果
            if structure._animation_state == 'search_found':
                self.hint_updated.emit(f"找到节点: {structure._search_value}")
                self.log_operation(f"[BST] 搜索结果：找到 {structure._search_value}")
            elif structure._animation_state == 'search_not_found':
                self.hint_updated.emit(f"未找到节点: {structure._search_value}")
                self.log_operation(f"[BST] 搜索结果：未找到 {structure._search_value}")
            
            # 最终更新显示
            self._update_snapshot()
    
    def _update_bst_delete_animation(self, structure):
        """更新BST删除动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_delete_animation(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器
        if progress >= 1.0:
            self._animation_timer.stop()
            structure.complete_delete_animation()
            
            # 显示删除结果
            if structure._animation_state == 'delete_not_found':
                self.hint_updated.emit(f"未找到节点: {structure._delete_value}")
            else:
                self.hint_updated.emit(f"已删除节点: {structure._delete_value}")
            
            # 最终更新显示
            self._update_snapshot()
    
    def delete_bst(self, value: str):
        """删除BST节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self._get_current_structure()
            if not structure:
                self._show_warning("请先选择BST结构")
                return
            
            # 开始删除动画
            structure.delete(value)
            
            # 使用定时器实现平滑动画
            self._restart_animation_timer(lambda: self._update_bst_delete_animation(structure), 50)
            
            # 设置动画总时长
            self._animation_duration = 2000  # 2秒总时长（删除需要更多时间）
            self._animation_start_time = 0
            
            self._update_snapshot()
            self._pending_llm_action = {
                "structure_type": "BST",
                "operation": "delete",
                "parameters": {"value": value},
            }
            self.log_operation(f"[BST] 删除节点 {value}")
        except Exception as e:
            self._show_error("删除失败", str(e))

    def traverse_bst_preorder(self):
        self._start_bst_traversal('preorder')

    def traverse_bst_inorder(self):
        self._start_bst_traversal('inorder')

    def traverse_bst_postorder(self):
        self._start_bst_traversal('postorder')

    def traverse_bst_levelorder(self):
        self._start_bst_traversal('levelorder')

    def _start_bst_traversal(self, order: str):
        """启动BST遍历动画"""
        try:
            structure = self._get_current_structure()
            if not structure or not hasattr(structure, 'start_traversal'):
                self._show_warning("请先选择BST结构")
                return

            if not structure.start_traversal(order):
                self._show_warning("当前BST为空，无法遍历")
                return

            total_nodes = len(getattr(structure, '_traversal_sequence', []))
            if total_nodes <= 0:
                self._show_warning("没有可遍历的节点")
                return

            self._restart_animation_timer(lambda: self._update_bst_traversal_animation(structure), 50)
            self._animation_duration = max(total_nodes, 1) * 800  # 每个节点约0.8秒
            self._animation_start_time = 0

            order_map = {
                'preorder': '前序',
                'inorder': '中序',
                'postorder': '后序',
                'levelorder': '层序'
            }
            order_text = order_map.get(order, '遍历')

            self._update_snapshot()
            self.hint_updated.emit(f"{order_text}遍历进行中...")
            self._pending_llm_action = {
                "structure_type": "BST",
                "operation": f"traverse_{order}",
                "parameters": {},
            }
            self.log_operation(f"[BST] {order_text}遍历")
        except Exception as e:
            self._show_error("遍历失败", str(e))

    def _update_bst_traversal_animation(self, structure):
        """更新BST遍历动画"""
        import time

        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 毫秒

        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time

        progress = self._calc_progress(elapsed)
        structure.update_traversal_animation(progress)

        self._update_snapshot()

        if progress >= 1.0:
            self._animation_timer.stop()
            structure.complete_traversal_animation()
            self._update_snapshot()
            order_map = {
                'preorder': '前序',
                'inorder': '中序',
                'postorder': '后序',
                'levelorder': '层序'
            }
            order_text = order_map.get(getattr(structure, '_traversal_order', ''), '遍历')
            self.hint_updated.emit(f"{order_text}遍历完成")
            self.log_operation(f"[BST] {order_text}遍历完成")
    
    # ========== 哈夫曼树操作 ==========
    
    def build_huffman_tree(self, freq_text: str):
        """构建哈夫曼树"""
        try:
            freq_dict = self._parse_frequency_mapping(freq_text)
            structure = self._get_current_structure()
            if structure:
                if hasattr(structure, "clear"):
                    structure.clear()
                structure.build(freq_dict)
                self._update_snapshot()
                if isinstance(freq_text, str):
                    freq_repr = freq_text.strip()
                else:
                    freq_repr = str(freq_text)
                self._pending_llm_action = {
                    "structure_type": "HuffmanTree",
                    "operation": "build",
                    "parameters": {"frequencies": freq_repr},
                }
                self.log_operation(f"[哈夫曼树] 构建频率: {freq_repr or '(空)'}")
                
                # 启动全新分阶段动画
                self.start_huffman_animation()
        except Exception as e:
            self._show_error("构建哈夫曼树失败", str(e))
            print(f"构建哈夫曼树错误: {e}")
    
    def start_huffman_animation(self):
        """启动哈夫曼树动画（选择→移动→合并→回队列）"""
        try:
            structure = self.structures.get("HuffmanTree")
            if not structure:
                self._show_error("启动失败", "未选择或未创建哈夫曼结构")
                return
            if not structure.start_animation():
                # 无需动画（为空或单节点）
                self._update_snapshot()
                return
            
            # 进入第一阶段
            self._start_huffman_phase(structure)
        except Exception as e:
            self._show_error("启动失败", str(e))
            print(f"启动哈夫曼树动画错误: {e}")
    
    def _huffman_phase_duration(self, state: str) -> int:
        """阶段时长（毫秒）"""
        return {
            "select": 2200,  # 红色填充 2s
            "move": 1500,
            "merge": 1300,
            "return": 1500,
        }.get(state, 0)

    def _start_huffman_phase(self, structure):
        """进入当前阶段并启动定时器"""
        state = getattr(structure, "_animation_state", "idle")
        duration = self._huffman_phase_duration(state)
        if duration <= 0:
            self._update_snapshot()
            return
        self._animation_duration = duration
        self._animation_start_time = 0
        self._restart_animation_timer(lambda: self._update_huffman_phase(structure), 60)
        self._update_snapshot()
        
    def _update_huffman_phase(self, structure):
        """驱动单阶段动画进度"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000.0
        now = time.time() * 1000.0
        elapsed = now - self._animation_start_time
        progress = self._calc_progress(elapsed)
        
        structure.update_animation(progress)
        self._update_snapshot()
        
        if progress >= 1.0:
            self._animation_timer.stop()
            self._animation_paused = False
            self._paused_elapsed = 0.0
            structure.finish_phase()
            self._update_snapshot()
            if getattr(structure, "_animation_state", "") != "done":
                self._start_huffman_phase(structure)
    
    def pause_huffman_animation(self):
        """暂停哈夫曼树动画"""
        if hasattr(self, '_animation_timer') and self._animation_timer:
            if self._animation_timer.isActive():
                import time
                now = time.time() * 1000.0
                if self._animation_start_time:
                    self._paused_elapsed = now - self._animation_start_time
                else:
                    self._paused_elapsed = 0.0
                self._animation_paused = True
                self._animation_timer.stop()
                self.hint_updated.emit("哈夫曼树动画已暂停")
    
    def resume_huffman_animation(self):
        """恢复哈夫曼树动画"""
        structure = self.structures.get("HuffmanTree")
        if hasattr(self, '_animation_timer') and self._animation_timer and structure:
            if getattr(structure, "_animation_state", "") != "done" and not self._animation_timer.isActive():
                import time
                now = time.time() * 1000.0
                self._animation_start_time = now - (self._paused_elapsed or 0.0)
                self._animation_paused = False
                self._animation_timer.start(self._animation_timer.interval())
                self.hint_updated.emit("哈夫曼树动画已恢复")
    
    def step_huffman_animation(self):
        """哈夫曼树动画单步执行（推动当前阶段一次更新）"""
        structure = self.structures.get("HuffmanTree")
        if structure and hasattr(structure, '_animation_state') and structure._animation_state not in ('done', None):
            self._update_huffman_phase(structure)
    
    # ========== 工具方法 ==========
    
    def _parse_comma_separated_values(self, text: str):
        """解析逗号分隔的值"""
        if not text.strip():
            return []
        
        # 使用生成器避免创建list
        for s in text.split(","):
            s = s.strip()
            if s:
                yield s
    
    def _parse_frequency_mapping(self, text: str) -> dict:
        """解析频率映射"""
        freq = {}
        raw = (text or "").strip()
        if raw:
            # 兼容用户直接输入 DSL 形式：build huffman with a:5,b:9...
            # 避免把 "build huffman with a" 当作字符 key
            import re
            raw = re.sub(r"^\s*build\s+huffman\s+with\s+", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"^\s*create\s+huffman\s+with\s+", "", raw, flags=re.IGNORECASE)

            for pair in raw.split(","):
                pair = pair.strip()
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    try:
                        freq[k] = int(v)
                    except ValueError:
                        print(f"警告: 无法解析 '{pair}'，跳过")
                        continue
                else:
                    print(f"警告: 格式错误 '{pair}'，应为 '字符:频率'")
                    continue
        return freq
    
    def _update_linked_list_animation(self, structure):
        """更新链表平滑动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        structure.update_animation_progress(progress)
        
        # 处理构建动画的逐步显示
        if structure._animation_state == 'building':
            build_values = getattr(structure, '_build_values', [])
            total_nodes = len(build_values)
            if total_nodes > 0:
                # 计算当前应该显示到第几个节点
                current_node_index = int(progress * total_nodes)
                structure._build_index = current_node_index
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            self._animation_paused = False
            self._paused_elapsed = 0.0
            if structure._animation_state == 'building':
                structure.complete_build_animation()
            elif structure._animation_state == 'inserting':
                structure.complete_insert_animation()
            elif structure._animation_state == 'deleting':
                structure.complete_delete_animation()
            self._update_snapshot()
    
    def _show_warning(self, message: str):
        """显示警告消息"""
        # 这里应该通过信号发送到UI层
        self.hint_updated.emit(f"警告: {message}")
    
    def _show_error(self, title: str, message: str):
        """显示错误消息"""
        # 这里应该通过信号发送到UI层
        self.hint_updated.emit(f"错误: {title} - {message}")
    
    def log_operation(self, message: str):
        """记录一条操作日志并发射信号"""
        if not message:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self._operation_logs.append(entry)
        if len(self._operation_logs) > 200:
            self._operation_logs.pop(0)
        self.operation_logged.emit(entry)
        # 附带：尝试将操作写入 LLM 上下文（若已标注结构和动作）
        # 使用统一的暂存键 _pending_llm_action 由调用方设置
        pending = getattr(self, "_pending_llm_action", None)
        if pending and isinstance(pending, dict):
            try:
                self._record_llm_action(
                    pending.get("structure_type"),
                    pending.get("operation"),
                    pending.get("parameters", {}),
                )
            finally:
                self._pending_llm_action = None
    
    def get_operation_logs(self) -> List[str]:
        """获取操作日志历史"""
        return list(self._operation_logs)
    
    def clear_operation_logs(self):
        """清空操作日志"""
        if self._operation_logs:
            self._operation_logs.clear()
        self.operation_log_cleared.emit()

    # 统一写入 LLM 上下文的内部辅助
    def _record_llm_action(self, structure_type: str, operation: str, parameters: Optional[Dict[str, Any]] = None):
        if not structure_type or not operation:
            return
        if not hasattr(self, "llm_context_actions"):
            self.llm_context_actions = []
        action = {
            "structure_type": structure_type,
            "operation": operation,
            "parameters": parameters if isinstance(parameters, dict) else {},
        }
        self.llm_context_actions.append(action)
        # 控制列表长度，防止过大
        if len(self.llm_context_actions) > 300:
            self.llm_context_actions = self.llm_context_actions[-300:]
    
    # ========== DSL功能 ==========
    
    def execute_dsl_command(self, command_text: str) -> Tuple[bool, str]:
        """
        执行单条DSL命令
        
        Args:
            command_text: DSL命令文本
            
        Returns:
            (成功标志, 消息文本)
        """
        try:
            command = self.dsl_parser.parse(command_text)
            if command.type.value == "unknown":
                return True, "跳过注释或空行"  # 注释和空行视为成功
            return self.dsl_executor.execute(command)
        except Exception as e:
            return False, str(e)
    
    def execute_dsl_script(
        self,
        script_text: str,
        sequential: bool = False,
        progress_callback=None,
        finished_callback=None,
    ):
        """
        执行DSL脚本(批量命令)
        
        Args:
            script_text: 脚本文本(每行一条命令)
            
        Returns:
            (成功数, 失败数, 详细消息列表)
        """
        try:
            commands = self.dsl_parser.parse_script(script_text)
            if sequential:
                return self.dsl_executor.execute_script_sequential(
                    commands,
                    progress_callback=progress_callback,
                    finished_callback=finished_callback,
                )
            return self.dsl_executor.execute_script(commands)
        except Exception as e:
            if sequential and finished_callback:
                finished_callback(0, 1, [f"脚本解析失败: {str(e)}"])
            return 0, 1, [f"脚本解析失败: {str(e)}"]
    
    # ========== AVL树操作 ==========
    
    def insert_avl(self, value: str):
        """插入AVL树节点"""
        try:
            if not value:
                self._show_warning("请输入一个值")
                return
            
            structure = self.structures.get("AVL")
            if structure:
                # 开始插入动画
                structure.insert(value)
                
                # 使用定时器实现平滑动画
                self._restart_animation_timer(lambda: self._update_avl_animation(structure), 50)
                
                # 设置动画总时长：缩短非旋转停顿，旋转绝对时长保持原水平
                self._animation_duration = 5000  # 5秒总时长
                self._animation_start_time = 0
                
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "AVL",
                    "operation": "insert",
                    "parameters": {"value": value},
                }
                self.log_operation(f"[AVL] 插入节点 {value}")
        except Exception as e:
            self._show_error("插入失败", str(e))
            # 批量构建时，异常不应中断流程，继续处理队列
            if hasattr(self, '_avl_build_queue') and self._avl_build_queue:
                QTimer.singleShot(100, self._insert_next_avl_value)
    
    def _update_avl_animation(self, structure):
        """更新AVL树动画"""
        import time
        
        if self._animation_start_time == 0:
            self._animation_start_time = time.time() * 1000  # 转换为毫秒
        
        current_time = time.time() * 1000
        elapsed = current_time - self._animation_start_time
        
        # 计算动画进度 (0.0 到 1.0)
        progress = self._calc_progress(elapsed)
        
        # 调用四阶段动画更新方法（关键修改）
        structure.update_insert_animation(progress)
        
        # 更新显示
        self._update_snapshot()
        
        # 如果动画完成，停止定时器并完成操作
        if progress >= 1.0:
            self._animation_timer.stop()
            
            # 执行实际的插入操作
            structure.complete_insert_animation()
            
            # 重置动画计时器，确保下一个节点的动画能正确计时
            self._animation_start_time = 0
            
            # 最终更新显示
            self._update_snapshot()
            
            # 保存队列状态，稍后继续执行队列
            has_next = bool(self._avl_build_queue)
            
            # 清理定时器
            old_timer = self._animation_timer
            self._animation_timer = None  # 先清空引用
            if old_timer is not None:
                old_timer.stop()
            
            # 检查是否有待插入的AVL节点（批量构建）
            # 使用QTimer.singleShot延迟一小段时间，确保前一个定时器完全清理
            if has_next:
                QTimer.singleShot(100, self._insert_next_avl_value)
    
    def clear_avl(self):
        """清空AVL树"""
        try:
            structure = self.structures.get("AVL")
            if structure:
                structure.root = None
                structure._animation_state = None
                structure._animation_progress = 0.0
                structure._new_value = None
                structure._rotation_plan = None
                self._update_snapshot()
                self._pending_llm_action = {
                    "structure_type": "AVL",
                    "operation": "clear",
                    "parameters": {},
                }
                self.log_operation("[AVL] 清空整棵树")
        except Exception as e:
            self._show_error("清空失败", str(e))
    
    def clear_current_structure(self):
        """清空当前选中的数据结构（数据与动画状态）"""
        try:
            # 停止当前动画定时器，避免残留回调
            timer = getattr(self, '_animation_timer', None)
            if timer is not None:
                timer.stop()
                self._animation_timer = None
                self._animation_start_time = 0
            
            structure = self._get_current_structure()
            if not structure:
                return
            
            # 优先使用模型自带的 clear()
            if hasattr(structure, 'clear') and callable(getattr(structure, 'clear')):
                structure.clear()
            else:
                # 兜底：常见字段重置
                if hasattr(structure, 'root'):
                    structure.root = None
                if hasattr(structure, '_animation_state'):
                    structure._animation_state = None
                if hasattr(structure, '_animation_progress'):
                    structure._animation_progress = 0.0
                if hasattr(structure, '_operation_history'):
                    try:
                        structure._operation_history.clear()
                    except Exception:
                        structure._operation_history = []
            
            # 刷新界面
            self._update_snapshot()
            self.log_operation(f"[{self.current_structure_key}] 清空当前结构")
        except Exception as e:
            self._show_error("清空失败", str(e))
    
    # ========== 自然语言处理功能 ==========
    
    def convert_natural_language_to_action(self, user_input: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        将自然语言转换为动作（仅转换，不执行）
        用于在工作线程中调用LLM API
        
        Args:
            user_input: 用户的自然语言输入
            
        Returns:
            (成功标志, 消息文本, 转换后的动作JSON)
        """
        try:
            # 检查API密钥
            if not self.llm_service.check_api_key():
                return False, "未设置OPENROUTER_API_KEY环境变量，请在系统环境变量中设置", None
            
            # 转换为JSON动作
            ctx_for_prompt = self._build_llm_prompt_context()
            try:
                preview = ctx_for_prompt[-3:] if len(ctx_for_prompt) > 3 else ctx_for_prompt
                print(f"[LLM] context_actions={len(ctx_for_prompt)} tail_preview={preview}")
            except Exception:
                pass
            action = self.llm_service.convert_natural_language_to_action(
                user_input,
                model=self.get_llm_model(),
                operations_context=ctx_for_prompt
            )
            action = self._normalize_position_from_user_text(user_input, action)
            
            if action is None:
                return False, "LLM转换失败，请检查输入是否明确，或尝试手动输入DSL命令", None
            
            return True, "转换成功", action
            
        except ValueError as e:
            # API密钥未设置
            return False, str(e), None
        except Exception as e:
            return False, f"转换失败: {str(e)}", None
    
    def execute_natural_language_command(self, user_input: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        执行自然语言命令（完整流程：转换+执行）
        此方法在主线程中调用，确保动画正常
        
        Args:
            user_input: 用户的自然语言输入
            
        Returns:
            (成功标志, 消息文本, 转换后的动作JSON)
        """
        try:
            # 检查API密钥
            if not self.llm_service.check_api_key():
                return False, "未设置OPENROUTER_API_KEY环境变量，请在系统环境变量中设置", None
            
            # 转换为JSON动作
            ctx_for_prompt = self._build_llm_prompt_context()
            try:
                preview = ctx_for_prompt[-3:] if len(ctx_for_prompt) > 3 else ctx_for_prompt
                print(f"[LLM] context_actions={len(ctx_for_prompt)} tail_preview={preview}")
            except Exception:
                pass
            action = self.llm_service.convert_natural_language_to_action(
                user_input,
                model=self.get_llm_model(),
                operations_context=ctx_for_prompt
            )
            action = self._normalize_position_from_user_text(user_input, action)
            
            if action is None:
                return False, "LLM转换失败，请检查输入是否明确，或尝试手动输入DSL命令", None
            
            # 执行动作（在主线程中执行，确保动画正常）
            success, message = self.action_executor.execute_action(action)
            
            return success, message, action
            
        except ValueError as e:
            # API密钥未设置
            return False, str(e), None
        except Exception as e:
            return False, f"执行自然语言命令失败: {str(e)}", None

    # ========== LLM 模型管理 ==========
    def set_llm_model(self, model: Optional[str]):
        """更新当前使用的LLM模型"""
        if model and model.strip():
            self.current_llm_model = model.strip()
        else:
            self.current_llm_model = self.llm_service.default_model

    def get_llm_model(self) -> Optional[str]:
        """获取当前模型，若未设置则返回默认值"""
        return self.current_llm_model or self.llm_service.default_model

    # ========== 动画倍速管理 ==========
    def set_speed_multiplier(self, multiplier: float):
        """设置全局动画倍速（影响统一定时器与进度计算）"""
        try:
            multiplier = float(multiplier)
        except (TypeError, ValueError):
            multiplier = 1.0
        multiplier = max(0.1, multiplier)
        self._speed_multiplier = multiplier
        timer = getattr(self, "_animation_timer", None)
        if timer and self._current_base_interval:
            timer.setInterval(self._apply_speed_interval(self._current_base_interval))

    # ========== LLM 上下文管理 ==========
    def load_llm_context_from_file(self, path: str) -> Tuple[bool, str, int]:
        """
        从JSON文件加载已执行操作列表，作为LLM上下文参考
        支持两种格式：
        1) 纯数组: [{structure_type, operation, parameters}, ...]
        2) 包含 operations/actions 字段的对象: {"operations": [...]} 或 {"actions": [...]}
        """
        try:
            import json
            import os
            if not path or not os.path.exists(path):
                return False, "文件不存在", 0

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            ops = None
            if isinstance(data, list):
                ops = data
            elif isinstance(data, dict):
                ops = data.get("operations") or data.get("actions")

            if not isinstance(ops, list):
                raise ValueError("JSON格式需为数组，或包含 operations/actions 数组字段")

            validated = []
            for op in ops:
                if not isinstance(op, dict):
                    continue
                st = op.get("structure_type")
                op_name = op.get("operation")
                params = op.get("parameters", {})
                if st and op_name:
                    validated.append({
                        "structure_type": st,
                        "operation": op_name,
                        "parameters": params if isinstance(params, dict) else {}
                    })

            self.llm_context_actions = validated
            self.hint_updated.emit(f"已加载 {len(validated)} 条操作作为LLM上下文")
            return True, f"已加载 {len(validated)} 条上下文操作", len(validated)
        except Exception as e:
            return False, f"加载LLM上下文失败: {e}", 0

    def clear_llm_context(self):
        """清空LLM上下文操作列表"""
        self.llm_context_actions = []
        self.hint_updated.emit("已清空LLM上下文操作")

# -*- coding: utf-8 -*-
"""
动作执行器模块
负责将JSON格式的动作转换为控制器方法调用
"""
from typing import Dict, Any, Tuple


class ActionExecutor:
    """动作执行器类，根据JSON动作调用MainController的对应方法"""
    
    def __init__(self, controller):
        """
        初始化执行器
        
        Args:
            controller: MainController实例
        """
        self.controller = controller
    
    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        执行JSON动作
        
        Args:
            action: JSON格式的动作字典
                {
                    "structure_type": "BST",
                    "operation": "create",
                    "parameters": {...}
                }
        
        Returns:
            (成功标志, 消息文本)
        """
        try:
            structure_type = action.get("structure_type")
            operation = action.get("operation")
            parameters = action.get("parameters", {})
            
            if not structure_type or not operation:
                return False, "动作格式错误：缺少structure_type或operation"
            
            # 切换到对应的数据结构
            self.controller.select_structure(structure_type)
            
            # 根据结构和操作调用对应的方法
            method_name = f"{operation}_{structure_type.lower()}"
            
            # 特殊处理：某些操作有特定命名
            if structure_type == "SequentialList":
                return self._execute_sequential_list(operation, parameters)
            elif structure_type == "LinkedList":
                return self._execute_linked_list(operation, parameters)
            elif structure_type == "Stack":
                return self._execute_stack(operation, parameters)
            elif structure_type == "BinaryTree":
                return self._execute_binary_tree(operation, parameters)
            elif structure_type == "BST":
                return self._execute_bst(operation, parameters)
            elif structure_type == "AVL":
                return self._execute_avl(operation, parameters)
            elif structure_type == "HuffmanTree":
                return self._execute_huffman(operation, parameters)
            else:
                return False, f"不支持的数据结构类型: {structure_type}"
                
        except Exception as e:
            return False, f"执行失败: {str(e)}"
    
    def _execute_sequential_list(self, operation: str, params: Dict) -> Tuple[bool, str]:
        """执行顺序表操作"""
        if operation == "create":
            values = ','.join(params.get("values", []))
            self.controller.build_sequential_list(values)
            return True, f"已创建顺序表: {values}"
        elif operation == "insert":
            position = params.get("position")
            value = params.get("value")
            self.controller.insert_at_sequential_list(position, value)
            return True, f"已在位置 {position} 插入值 {value}"
        elif operation == "delete":
            position = params.get("position")
            self.controller.delete_at_sequential_list(position)
            return True, f"已删除位置 {position} 的元素"
        else:
            return False, f"不支持的操作: {operation}"
    
    def _execute_linked_list(self, operation: str, params: Dict) -> Tuple[bool, str]:
        """执行链表操作"""
        if operation == "create":
            values = ','.join(params.get("values", []))
            self.controller.build_linked_list(values)
            return True, f"已创建链表: {values}"
        elif operation == "insert":
            position = params.get("position")
            value = params.get("value")
            self.controller.insert_at_linked_list(position, value)
            return True, f"已在位置 {position} 插入值 {value}"
        elif operation == "delete":
            position = params.get("position")
            self.controller.delete_at_linked_list(position)
            return True, f"已删除位置 {position} 的元素"
        else:
            return False, f"不支持的操作: {operation}"
    
    def _execute_stack(self, operation: str, params: Dict) -> Tuple[bool, str]:
        """执行栈操作"""
        if operation == "create":
            values = params.get("values")
            if isinstance(values, list) and len(values) > 0:
                self.controller.build_stack(",".join(str(v) for v in values))
                return True, f"已创建栈: {','.join(str(v) for v in values)}"
            # 无 values：创建空栈（重置）
            self.controller.clear_stack()
            return True, "已创建空的栈"
        elif operation == "push":
            value = params.get("value")
            self.controller.push_stack(value)
            return True, f"已入栈: {value}"
        elif operation == "pop":
            self.controller.pop_stack()
            return True, "已出栈"
        else:
            return False, f"不支持的操作: {operation}"
    
    def _execute_binary_tree(self, operation: str, params: Dict) -> Tuple[bool, str]:
        """执行二叉树操作"""
        # 兼容多种“构建”别名（LLM/DSL 可能输出 build/build_level 等）
        if operation in ("create", "build", "build_level", "build_level_order", "level_build"):
            values = params.get("values", [])
            self.controller.build_binary_tree(values)
            return True, f"已构建二叉树: {','.join(values)}"
        elif operation == "insert":
            value = params.get("value")
            parent_value = params.get("parent_value")
            position = params.get("position")  # left or right
            self.controller.insert_binary_tree_with_position(value, parent_value, position)
            return True, f"已在节点 {parent_value} 的{position}侧插入 {value}"
        elif operation == "delete":
            value = params.get("value")
            self.controller.delete_binary_tree(value)
            return True, f"已删除二叉树节点: {value}"
        else:
            return False, f"不支持的操作: {operation}"
    
    def _execute_bst(self, operation: str, params: Dict) -> Tuple[bool, str]:
        """执行BST操作"""
        if operation in ("create", "build"):
            values = params.get("values", [])
            self.controller.build_bst(values)
            return True, f"正在构建BST: {','.join(values)}"
        elif operation == "insert":
            value = params.get("value")
            self.controller.insert_bst(value)
            return True, f"已在BST中插入: {value}"
        elif operation == "search":
            value = params.get("value")
            self.controller.search_bst(value)
            return True, f"正在搜索: {value}"
        elif operation == "delete":
            value = params.get("value")
            self.controller.delete_bst(value)
            return True, f"已从BST删除: {value}"
        else:
            return False, f"不支持的操作: {operation}"
    
    def _execute_avl(self, operation: str, params: Dict) -> Tuple[bool, str]:
        """执行AVL树操作"""
        if operation == "create":
            values = params.get("values", [])
            self.controller.build_avl(values)
            return True, f"正在构建AVL树: {','.join(values)}"
        elif operation == "insert":
            value = params.get("value")
            self.controller.insert_avl(value)
            return True, f"已在AVL树中插入: {value}"
        elif operation == "clear":
            self.controller.clear_avl()
            return True, "已清空AVL树"
        else:
            return False, f"不支持的操作: {operation}"
    
    def _execute_huffman(self, operation: str, params: Dict) -> Tuple[bool, str]:
        """执行哈夫曼树操作"""
        if operation == "build":
            frequencies = params.get("frequencies")
            self.controller.build_huffman_tree(frequencies)
            return True, f"正在构建哈夫曼树: {frequencies}"
        else:
            return False, f"不支持的操作: {operation}"


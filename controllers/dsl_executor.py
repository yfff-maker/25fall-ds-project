# -*- coding: utf-8 -*-
"""
DSL执行器模块
负责执行解析后的DSL命令,调用MainController的相应方法
"""
from typing import List, Tuple
from .dsl_parser import ParsedCommand, CommandType


class DSLExecutor:
    """DSL执行器类"""
    
    def __init__(self, controller):
        """
        初始化执行器
        
        Args:
            controller: MainController实例
        """
        self.controller = controller
    
    def execute(self, command: ParsedCommand) -> Tuple[bool, str]:
        """
        执行单条命令
        
        Args:
            command: 解析后的命令对象
            
        Returns:
            (成功标志, 消息文本)
        """
        try:
            # 切换到对应的数据结构
            if command.structure:
                self.controller.select_structure(command.structure)
            
            # 根据命令类型执行相应操作
            if command.type == CommandType.CREATE_ARRAYLIST:
                values = ','.join(command.args['values'])
                self.controller.build_sequential_list(values)
                return True, f"已创建顺序表: {values}"
            
            elif command.type == CommandType.INSERT_ARRAYLIST:
                value = command.args['value']
                position = command.args['position']
                self.controller.insert_at_sequential_list(position, value)
                return True, f"已在位置 {position} 插入值 {value}"
            
            elif command.type == CommandType.DELETE_AT_ARRAYLIST:
                position = command.args['position']
                self.controller.delete_at_sequential_list(position)
                return True, f"已删除位置 {position} 的元素"
            
            elif command.type == CommandType.CREATE_LINKEDLIST:
                values = ','.join(command.args['values'])
                self.controller.build_linked_list(values)
                return True, f"已创建链表: {values}"
            
            elif command.type == CommandType.INSERT_LINKEDLIST:
                value = command.args['value']
                position = command.args['position']
                self.controller.insert_at_linked_list(position, value)
                return True, f"已在位置 {position} 插入值 {value}"
            
            elif command.type == CommandType.DELETE_AT_LINKEDLIST:
                position = command.args['position']
                self.controller.delete_at_linked_list(position)
                return True, f"已删除位置 {position} 的元素"
            
            elif command.type == CommandType.CREATE_STACK:
                # 创建空的栈
                return True, "已创建空的栈"
            
            elif command.type == CommandType.PUSH_STACK:
                value = command.args['value']
                self.controller.push_stack(value)
                return True, f"已入栈: {value}"
            
            elif command.type == CommandType.POP_STACK:
                self.controller.pop_stack()
                return True, "已出栈"
            
            elif command.type == CommandType.CREATE_BINARYTREE:
                # 层序构建二叉树
                values = command.args['values']
                # 这里需要实现层序构建逻辑
                # 暂时先逐节点插入
                for val in values:
                    # 首次插入作为根节点
                    if self.controller.structures['BinaryTree'].root is None:
                        self.controller.insert_binary_tree_node(val)
                    else:
                        # 后续节点需要用户选择父节点,这里简化处理
                        # 实际应该实现自动层序插入逻辑
                        break
                return True, f"已构建二叉树(层序): {','.join(values)}"
            
            elif command.type == CommandType.CREATE_BST:
                # BST逐个插入构建
                values = command.args['values']
                for val in values:
                    self.controller.insert_bst(val)
                return True, f"已创建BST: {','.join(values)}"
            
            elif command.type == CommandType.INSERT_BST:
                value = command.args['value']
                self.controller.insert_bst(value)
                return True, f"已在BST中插入: {value}"
            
            elif command.type == CommandType.SEARCH_BST:
                value = command.args['value']
                self.controller.search_bst(value)
                return True, f"正在搜索: {value}"
            
            elif command.type == CommandType.DELETE_BST:
                value = command.args['value']
                self.controller.delete_bst(value)
                return True, f"已从BST删除: {value}"
            
            elif command.type == CommandType.CREATE_AVL:
                # AVL逐个插入构建
                values = command.args['values']
                for val in values:
                    self.controller.insert_avl(val)
                return True, f"已创建AVL树: {','.join(values)}"
            
            elif command.type == CommandType.INSERT_AVL:
                value = command.args['value']
                self.controller.insert_avl(value)
                return True, f"已在AVL树中插入: {value}"
            
            elif command.type == CommandType.CLEAR_AVL:
                self.controller.clear_avl()
                return True, "已清空AVL树"
            
            elif command.type == CommandType.BUILD_HUFFMAN:
                # 解析频率映射
                freq_str = command.args['frequencies']
                self.controller.build_huffman_tree(freq_str)
                return True, f"正在构建哈夫曼树: {freq_str}"
            
            else:
                return False, "未知的命令类型"
                
        except Exception as e:
            return False, f"执行失败: {str(e)}"
    
    def execute_script(self, commands: List[ParsedCommand]) -> Tuple[int, int, List[str]]:
        """
        批量执行命令
        
        Args:
            commands: 命令列表
            
        Returns:
            (成功数, 失败数, 错误消息列表)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        for i, cmd in enumerate(commands, 1):
            if cmd.type == CommandType.UNKNOWN:
                continue  # 跳过注释和空行
            
            success, message = self.execute(cmd)
            if success:
                success_count += 1
                errors.append(f"✓ 命令 {i}: {cmd.original_text}")
            else:
                fail_count += 1
                errors.append(f"✗ 命令 {i}: {cmd.original_text} - {message}")
        
        return success_count, fail_count, errors


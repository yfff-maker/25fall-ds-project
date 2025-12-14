# -*- coding: utf-8 -*-
"""
DSL执行器模块
负责执行解析后的DSL命令,调用MainController的相应方法
"""
from typing import List, Tuple
from PyQt5.QtCore import QTimer
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
        self._sequential_queue: List[ParsedCommand] = []
        self._seq_total = 0
        self._seq_index = 0
        self._seq_success = 0
        self._seq_fail = 0
        self._seq_messages: List[str] = []
        self._seq_progress_callback = None
        self._seq_finished_callback = None
        self._sequential_running = False
    
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
                # create stack [with ...]
                values = command.args.get('values')
                if values:
                    self.controller.build_stack(','.join(values))
                    return True, f"已创建栈: {','.join(values)}"
                # 未提供 values：重置为空栈
                self.controller.clear_stack()
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
                self.controller.build_binary_tree(values)
                return True, f"已构建二叉树(层序): {','.join(values)}"
            
            elif command.type == CommandType.BUILD_BINARYTREE:
                # 层序构建二叉树
                values = command.args['values']
                self.controller.build_binary_tree(values)
                return True, f"已构建二叉树(层序): {','.join(values)}"
            
            elif command.type == CommandType.INSERT_BINARYTREE:
                value = command.args['value']
                position = command.args['position']  # left or right
                parent_value = command.args['parent_value']
                self.controller.insert_binary_tree_with_position(value, parent_value, position)
                return True, f"已在节点 {parent_value} 的{position}侧插入 {value}"
            
            elif command.type == CommandType.DELETE_BINARYTREE:
                value = command.args['value']
                self.controller.delete_binary_tree(value)
                return True, f"已删除节点: {value} 及其子树"
            
            elif command.type == CommandType.CREATE_BST:
                # BST逐个插入构建
                values = command.args['values']
                for val in values:
                    self.controller.insert_bst(val)
                return True, f"已创建BST: {','.join(values)}"
            
            elif command.type == CommandType.BUILD_BST:
                # BST批量构建（自动顺序插入动画）
                values = command.args['values']
                self.controller.build_bst(values)
                return True, f"正在构建BST: {','.join(values)}"
            
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
                # AVL批量构建（create命令也使用build_avl）
                values = command.args['values']
                self.controller.build_avl(values)
                return True, f"正在构建AVL树: {','.join(values)}"
            
            elif command.type == CommandType.BUILD_AVL:
                # AVL批量构建（自动顺序插入动画）
                values = command.args['values']
                self.controller.build_avl(values)
                return True, f"正在构建AVL树: {','.join(values)}"
            
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

    def execute_script_sequential(
        self,
        commands: List[ParsedCommand],
        progress_callback=None,
        finished_callback=None,
    ) -> bool:
        """按顺序执行命令，等待动画完成后再运行下一条"""
        if self._sequential_running:
            raise RuntimeError("已有DSL批量执行任务正在进行")

        actionable = [cmd for cmd in commands if cmd.type != CommandType.UNKNOWN]
        if not actionable:
            if finished_callback:
                finished_callback(0, 0, [])
            return False

        self._sequential_queue = actionable
        self._seq_total = len(actionable)
        self._seq_index = 0
        self._seq_success = 0
        self._seq_fail = 0
        self._seq_messages = []
        self._seq_progress_callback = progress_callback
        self._seq_finished_callback = finished_callback
        self._sequential_running = True
        self._process_next_command()
        return True

    def _process_next_command(self):
        if not self._sequential_running:
            return

        if self.controller.is_busy():
            QTimer.singleShot(150, self._process_next_command)
            return

        if not self._sequential_queue:
            self._finish_sequential_execution()
            return

        cmd = self._sequential_queue.pop(0)
        self._seq_index += 1
        success, message = self.execute(cmd)
        if success:
            self._seq_success += 1
            entry = f"✓ 命令 {self._seq_index}: {cmd.original_text}"
        else:
            self._seq_fail += 1
            entry = f"✗ 命令 {self._seq_index}: {cmd.original_text} - {message}"
        self._seq_messages.append(entry)

        if self._seq_progress_callback:
            self._seq_progress_callback(
                self._seq_index,
                self._seq_total,
                success,
                entry,
            )

        # 等待可能的动画执行完毕
        QTimer.singleShot(150, self._process_next_command)

    def _finish_sequential_execution(self):
        if not self._sequential_running:
            return
        self._sequential_running = False
        if self._seq_finished_callback:
            self._seq_finished_callback(
                self._seq_success,
                self._seq_fail,
                list(self._seq_messages),
            )
        self._sequential_queue = []
        self._seq_progress_callback = None
        self._seq_finished_callback = None


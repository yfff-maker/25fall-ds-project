# -*- coding: utf-8 -*-
"""
DSL解析器模块
负责将DSL命令文本解析为结构化的命令对象
"""
import re
from typing import Optional, List, Any
from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    """命令类型枚举"""
    # 顺序表操作
    CREATE_ARRAYLIST = "create_arraylist"
    INSERT_ARRAYLIST = "insert_arraylist"
    DELETE_AT_ARRAYLIST = "delete_at_arraylist"
    
    # 链表操作
    CREATE_LINKEDLIST = "create_linkedlist"
    INSERT_LINKEDLIST = "insert_linkedlist"
    DELETE_AT_LINKEDLIST = "delete_at_linkedlist"
    
    # 栈操作
    CREATE_STACK = "create_stack"
    PUSH_STACK = "push_stack"
    POP_STACK = "pop_stack"
    
    # 二叉树操作
    CREATE_BINARYTREE = "create_binarytree"
    BUILD_BINARYTREE = "build_binarytree"
    INSERT_BINARYTREE = "insert_binarytree"
    DELETE_BINARYTREE = "delete_binarytree"
    
    # BST操作
    CREATE_BST = "create_bst"
    BUILD_BST = "build_bst"
    INSERT_BST = "insert_bst"
    SEARCH_BST = "search_bst"
    DELETE_BST = "delete_bst"
    
    # AVL树操作
    CREATE_AVL = "create_avl"
    BUILD_AVL = "build_avl"
    INSERT_AVL = "insert_avl"
    CLEAR_AVL = "clear_avl"
    
    # 哈夫曼树操作
    BUILD_HUFFMAN = "build_huffman"
    
    # 未知命令
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """解析后的命令对象"""
    type: CommandType
    structure: str
    args: dict
    original_text: str


class DSLParser:
    """DSL解析器类"""
    
    # 定义命令模式
    PATTERNS = {
        # 顺序表
        CommandType.CREATE_ARRAYLIST: re.compile(
            r'create\s+arraylist\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.INSERT_ARRAYLIST: re.compile(
            r'insert\s+(\w+)\s+at\s+(\d+)\s+in\s+arraylist$',
            re.IGNORECASE
        ),
        CommandType.DELETE_AT_ARRAYLIST: re.compile(
            r'delete\s+at\s+(\d+)\s+from\s+arraylist$',
            re.IGNORECASE
        ),
        
        # 链表
        CommandType.CREATE_LINKEDLIST: re.compile(
            r'create\s+linkedlist\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.INSERT_LINKEDLIST: re.compile(
            r'insert\s+(\w+)\s+at\s+(\d+)\s+in\s+linkedlist$',
            re.IGNORECASE
        ),
        CommandType.DELETE_AT_LINKEDLIST: re.compile(
            r'delete\s+at\s+(\d+)\s+from\s+linkedlist$',
            re.IGNORECASE
        ),
        
        # 栈
        CommandType.CREATE_STACK: re.compile(
            r'create\s+stack$',
            re.IGNORECASE
        ),
        CommandType.PUSH_STACK: re.compile(
            r'push\s+(\w+)\s+to\s+stack$',
            re.IGNORECASE
        ),
        CommandType.POP_STACK: re.compile(
            r'pop\s+from\s+stack$',
            re.IGNORECASE
        ),
        
        # 二叉树
        CommandType.CREATE_BINARYTREE: re.compile(
            r'create\s+binarytree\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.BUILD_BINARYTREE: re.compile(
            r'build\s+binarytree\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.INSERT_BINARYTREE: re.compile(
            r'insert\s+(\w+)\s+as\s+(left|right)\s+of\s+(\w+)\s+in\s+binarytree$',
            re.IGNORECASE
        ),
        CommandType.DELETE_BINARYTREE: re.compile(
            r'delete\s+(\w+)\s+from\s+binarytree$',
            re.IGNORECASE
        ),
        
        # BST
        CommandType.CREATE_BST: re.compile(
            r'create\s+bst\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.BUILD_BST: re.compile(
            r'build\s+bst\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.INSERT_BST: re.compile(
            r'insert\s+(\w+)\s+in\s+bst$',
            re.IGNORECASE
        ),
        CommandType.SEARCH_BST: re.compile(
            r'search\s+(\w+)\s+in\s+bst$',
            re.IGNORECASE
        ),
        CommandType.DELETE_BST: re.compile(
            r'delete\s+(\w+)\s+from\s+bst$',
            re.IGNORECASE
        ),
        
        # AVL树
        CommandType.CREATE_AVL: re.compile(
            r'create\s+avl\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.BUILD_AVL: re.compile(
            r'build\s+avl\s+with\s+(.+)$',
            re.IGNORECASE
        ),
        CommandType.INSERT_AVL: re.compile(
            r'insert\s+(\w+)\s+in\s+avl$',
            re.IGNORECASE
        ),
        CommandType.CLEAR_AVL: re.compile(
            r'clear\s+avl$',
            re.IGNORECASE
        ),
        
        # 哈夫曼树
        CommandType.BUILD_HUFFMAN: re.compile(
            r'build\s+huffman\s+with\s+(.+)$',
            re.IGNORECASE
        ),
    }
    
    def parse(self, command_text: str) -> ParsedCommand:
        """
        解析单条命令
        
        Args:
            command_text: 原始命令文本
            
        Returns:
            解析后的命令对象
            
        Raises:
            ValueError: 无法识别的命令
        """
        # 去除首尾空白并转为小写
        command_text = command_text.strip()
        
        # 处理注释行
        if command_text.startswith('#'):
            return ParsedCommand(
                type=CommandType.UNKNOWN,
                structure="",
                args={},
                original_text=command_text
            )
        
        # 处理空行
        if not command_text:
            return ParsedCommand(
                type=CommandType.UNKNOWN,
                structure="",
                args={},
                original_text=""
            )
        
        # 尝试匹配各个命令类型
        for cmd_type, pattern in self.PATTERNS.items():
            match = pattern.match(command_text)
            if match:
                args = self._extract_args(cmd_type, match, command_text)
                structure = self._get_structure_name(cmd_type)
                return ParsedCommand(
                    type=cmd_type,
                    structure=structure,
                    args=args,
                    original_text=command_text
                )
        
        # 无法识别的命令
        raise ValueError(f"无法识别的命令: {command_text}")
    
    def _extract_args(self, cmd_type: CommandType, match: re.Match, original_text: str) -> dict:
        """提取命令参数"""
        args = {}
        
        if cmd_type == CommandType.CREATE_ARRAYLIST:
            # create arraylist with 1,2,3
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.INSERT_ARRAYLIST:
            # insert 4 at 1 in arraylist
            args['value'] = match.group(1).strip()
            args['position'] = int(match.group(2))
            
        elif cmd_type == CommandType.DELETE_AT_ARRAYLIST:
            # delete at 0 from arraylist
            args['position'] = int(match.group(1))
            
        elif cmd_type == CommandType.CREATE_LINKEDLIST:
            # create linkedlist with 10,20,30
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.INSERT_LINKEDLIST:
            # insert 15 at 1 in linkedlist
            args['value'] = match.group(1).strip()
            args['position'] = int(match.group(2))
            
        elif cmd_type == CommandType.DELETE_AT_LINKEDLIST:
            # delete at 2 from linkedlist
            args['position'] = int(match.group(1))
            
        elif cmd_type == CommandType.CREATE_STACK:
            # create stack
            args = {}
            
        elif cmd_type == CommandType.PUSH_STACK:
            # push 100 to stack
            args['value'] = match.group(1).strip()
            
        elif cmd_type == CommandType.POP_STACK:
            # pop from stack
            args = {}
            
        elif cmd_type == CommandType.CREATE_BINARYTREE:
            # create binarytree with 1,2,3,4,5
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.BUILD_BINARYTREE:
            # build binarytree with 1,2,3,4,5
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.INSERT_BINARYTREE:
            # insert 6 as left of 3 in binarytree
            args['value'] = match.group(1).strip()
            args['position'] = match.group(2).lower().strip()  # left or right
            args['parent_value'] = match.group(3).strip()
            
        elif cmd_type == CommandType.DELETE_BINARYTREE:
            # delete 4 from binarytree
            args['value'] = match.group(1).strip()
            
        elif cmd_type == CommandType.CREATE_BST:
            # create bst with 50,30,70,20,40,60,80
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.BUILD_BST:
            # build bst with 50,30,70,20,40,60,80
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.INSERT_BST:
            # insert 25 in bst
            args['value'] = match.group(1).strip()
            
        elif cmd_type == CommandType.SEARCH_BST:
            # search 60 in bst
            args['value'] = match.group(1).strip()
            
        elif cmd_type == CommandType.DELETE_BST:
            # delete 30 from bst
            args['value'] = match.group(1).strip()
            
        elif cmd_type == CommandType.CREATE_AVL:
            # create avl with 7,19,16,27,9,5,14,11,17,12
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.BUILD_AVL:
            # build avl with 7,19,16,27,9,5,14,11,17,12
            values_str = match.group(1).strip()
            args['values'] = [v.strip() for v in values_str.split(',')]
            
        elif cmd_type == CommandType.INSERT_AVL:
            # insert 25 in avl
            args['value'] = match.group(1).strip()
            
        elif cmd_type == CommandType.CLEAR_AVL:
            # clear avl
            args = {}
            
        elif cmd_type == CommandType.BUILD_HUFFMAN:
            # build huffman with a:5,b:9,c:12,d:13,e:16,f:45
            freq_str = match.group(1).strip()
            args['frequencies'] = freq_str
            
        return args
    
    def _get_structure_name(self, cmd_type: CommandType) -> str:
        """根据命令类型获取数据结构名称"""
        mapping = {
            CommandType.CREATE_ARRAYLIST: "SequentialList",
            CommandType.INSERT_ARRAYLIST: "SequentialList",
            CommandType.DELETE_AT_ARRAYLIST: "SequentialList",
            
            CommandType.CREATE_LINKEDLIST: "LinkedList",
            CommandType.INSERT_LINKEDLIST: "LinkedList",
            CommandType.DELETE_AT_LINKEDLIST: "LinkedList",
            
            CommandType.CREATE_STACK: "Stack",
            CommandType.PUSH_STACK: "Stack",
            CommandType.POP_STACK: "Stack",
            
            CommandType.CREATE_BINARYTREE: "BinaryTree",
            CommandType.BUILD_BINARYTREE: "BinaryTree",
            CommandType.INSERT_BINARYTREE: "BinaryTree",
            CommandType.DELETE_BINARYTREE: "BinaryTree",
            
            CommandType.CREATE_BST: "BST",
            CommandType.BUILD_BST: "BST",
            CommandType.INSERT_BST: "BST",
            CommandType.SEARCH_BST: "BST",
            CommandType.DELETE_BST: "BST",
            
            CommandType.CREATE_AVL: "AVL",
            CommandType.BUILD_AVL: "AVL",
            CommandType.INSERT_AVL: "AVL",
            CommandType.CLEAR_AVL: "AVL",
            
            CommandType.BUILD_HUFFMAN: "HuffmanTree",
        }
        return mapping.get(cmd_type, "")
    
    def parse_script(self, script_text: str) -> List[ParsedCommand]:
        """
        解析脚本(多条命令)
        
        Args:
            script_text: 脚本文本(每行一条命令)
            
        Returns:
            解析后的命令列表
        """
        commands = []
        lines = script_text.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            try:
                cmd = self.parse(line)
                if cmd.type != CommandType.UNKNOWN:
                    commands.append(cmd)
            except ValueError as e:
                print(f"第 {line_num} 行解析错误: {e}")
        
        return commands


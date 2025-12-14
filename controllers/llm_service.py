# -*- coding: utf-8 -*-
"""
LLM服务模块
负责与OpenRouter API交互，将自然语言转换为结构化的JSON动作
"""
import os
import json
import requests
from typing import Optional, Dict, Any, List


class LLMService:
    """LLM服务类，处理自然语言到JSON动作的转换，使用OpenRouter API"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        # 默认模型，可以在环境变量中覆盖
        self.default_model = os.getenv('OPENROUTER_MODEL', 'openai/gpt-3.5-turbo')
    
    def check_api_key(self) -> bool:
        """检查API密钥是否已设置"""
        return self.api_key is not None and len(self.api_key.strip()) > 0
    
    def convert_natural_language_to_action(
        self,
        user_input: str,
        model: Optional[str] = None,
        operations_context: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        将自然语言转换为JSON动作
        
        Args:
            user_input: 用户的自然语言输入
            model: 要使用的模型（可选，默认使用配置的模型）
            
        Returns:
            JSON格式的动作字典，格式如下：
            {
                "structure_type": "BST",  # 数据结构类型
                "operation": "create",      # 操作类型
                "parameters": {...}        # 操作参数
            }
            如果转换失败返回None
        """
        if not self.check_api_key():
            raise ValueError("未设置OPENROUTER_API_KEY环境变量")
        
        try:
            # 构建prompt，附带可选的历史操作上下文
            prompt = self._build_prompt(user_input, operations_context)
            
            # 使用OpenRouter API
            model_to_use = model or self.default_model
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",  # 可选：用于跟踪
                "X-Title": "Data Structure Visualizer"  # 可选：应用名称
            }
            
            payload = {
                "model": model_to_use,
                "messages": [
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                "response_format": {"type": "json_object"},  # 强制返回JSON格式
                "temperature": 0.3  # 降低随机性，提高准确性
            }
            
            # 发送HTTP请求
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()  # 如果状态码不是200会抛出异常
            
            result = response.json()
            
            # 提取响应内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"].strip()
            else:
                raise ValueError(f"API响应格式异常: {result}")
            
            # 解析JSON
            try:
                action = json.loads(content)
            except json.JSONDecodeError:
                # 兜底：有时模型会输出解释文字+JSON，这里尝试抽取第一个 JSON 对象
                action = self._extract_first_json_object(content)
            
            return action
            
        except requests.exceptions.RequestException as e:
            print(f"OpenRouter API请求错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"错误详情: {error_detail}")
                except:
                    print(f"响应内容: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            if 'content' in locals():
                print(f"响应内容: {content}")
            return None
        except Exception as e:
            print(f"LLM API调用错误: {e}")
            return None
    
    def _build_prompt(self, user_input: str, operations_context: Optional[List[Dict[str, Any]]] = None) -> str:
        """构建系统prompt"""
        base_prompt = """你是一个数据结构可视化系统的AI助手。你的任务是将用户的自然语言描述转换为JSON格式的动作指令。

支持的数据结构类型：
- SequentialList (顺序表)
- LinkedList (链表)
- Stack (栈)
- BinaryTree (二叉树)
- BST (二叉搜索树)
- AVL (AVL平衡树)
- HuffmanTree (哈夫曼树)

支持的操作类型和参数格式：

1. SequentialList (顺序表):
   - create: {"structure_type": "SequentialList", "operation": "create", "parameters": {"values": ["1","2","3"]}}
   - insert: {"structure_type": "SequentialList", "operation": "insert", "parameters": {"position": 1, "value": "4"}}
   - delete: {"structure_type": "SequentialList", "operation": "delete", "parameters": {"position": 0}}

2. LinkedList (链表):
   - create: {"structure_type": "LinkedList", "operation": "create", "parameters": {"values": ["10","20","30"]}}
   - insert: {"structure_type": "LinkedList", "operation": "insert", "parameters": {"position": 1, "value": "15"}}
   - delete: {"structure_type": "LinkedList", "operation": "delete", "parameters": {"position": 2}}

3. Stack (栈):
   - create(空栈): {"structure_type": "Stack", "operation": "create", "parameters": {}}
   - create(非空栈): {"structure_type": "Stack", "operation": "create", "parameters": {"values": ["10","20","30"]}}
   - push: {"structure_type": "Stack", "operation": "push", "parameters": {"value": "100"}}
   - pop: {"structure_type": "Stack", "operation": "pop", "parameters": {}}

4. BinaryTree (二叉树):
   - create: {"structure_type": "BinaryTree", "operation": "create", "parameters": {"values": ["1","2","3","4","5"]}}
   - insert: {"structure_type": "BinaryTree", "operation": "insert", "parameters": {"value": "6", "parent_value": "3", "position": "left"}}

5. BST (二叉搜索树):
   - create: {"structure_type": "BST", "operation": "create", "parameters": {"values": ["50","30","70"]}}
   - build: {"structure_type": "BST", "operation": "build", "parameters": {"values": ["50","30","70"]}}
   - insert: {"structure_type": "BST", "operation": "insert", "parameters": {"value": "25"}}
   - search: {"structure_type": "BST", "operation": "search", "parameters": {"value": "30"}}
   - delete: {"structure_type": "BST", "operation": "delete", "parameters": {"value": "30"}}

6. AVL (AVL平衡树):
   - create: {"structure_type": "AVL", "operation": "create", "parameters": {"values": ["7","19","16"]}}
   - insert: {"structure_type": "AVL", "operation": "insert", "parameters": {"value": "25"}}
   - clear: {"structure_type": "AVL", "operation": "clear", "parameters": {}}

7. HuffmanTree (哈夫曼树):
   - build: {"structure_type": "HuffmanTree", "operation": "build", "parameters": {"frequencies": "a:5,b:9,c:12"}}

注意事项：
- 所有数值都以字符串形式提供（如 "5" 而不是 5）
- position参数是整数（数组索引从0开始）
- 对于二叉树插入，position可以是"left"或"right"
- 只返回JSON对象，不要包含其他文本

操作名约束（BinaryTree，非常重要）：
- 当用户说“构建/创建二叉树，节点值为[...]（层序）”时，一律输出 operation="create"（或兼容 build，但推荐 create）
- 不要输出 build_level / build_level_order / level_build / 其它自造名字

位置口径统一（非常重要）：
- “第N个位置”一律按 **从0开始的下标** 解释，也就是 JSON 中必须写成 `"position": N`，不要做 N-1。
  - 例：“在链表第0个位置插入5” -> position=0（插入到最前）
  - 例：“在链表第4个位置插入25” -> position=4（插入后它会成为从1开始数的第5个元素）
  - 例：“删除第4个位置的元素” -> position=4

上下文推断规则（非常重要）：
- 你会收到“已经执行过的操作历史”（JSON数组，按先后顺序）。你必须按顺序应用这些操作来推断当前状态，不要只看最后一次 create。
- 操作历史末尾可能包含一条 operation="state" 的记录（例如 LinkedList 的 parameters.elements），它表示当前结构的“有效状态”（可能包含动画中尚未提交的插入/删除变化）。若存在，优先以 state 为准推断“最后一个位置/末尾”等相对位置。

示例：
用户输入："创建一个包含数据元素[5,3,7,2,4]的二叉搜索树"
应返回：{"structure_type": "BST", "operation": "create", "parameters": {"values": ["5","3","7","2","4"]}}

用户输入："在BST中插入25"
应返回：{"structure_type": "BST", "operation": "insert", "parameters": {"value": "25"}}

现在请根据用户的输入，返回对应的JSON动作指令："""
        # 如果提供了上下文操作历史，将其追加到 prompt，帮助模型在已有操作基础上继续
        if operations_context:
            try:
                context_json = json.dumps(operations_context, ensure_ascii=False, indent=2)
            except Exception:
                context_json = str(operations_context)
            context_block = (
                "\n\n以下是已经执行过的操作历史（JSON数组，按先后顺序），请基于这些操作后的状态继续规划下一步动作，"
                "不要重复执行已完成的步骤，仅返回下一步的动作JSON：\n"
                f"{context_json}\n"
            )
        else:
            context_block = ""
        return base_prompt + context_block

    @staticmethod
    def _extract_first_json_object(text: str) -> Dict[str, Any]:
        """
        从包含杂散文本的内容中提取第一个 JSON 对象。
        适配：模型输出“解释 + JSON”导致 json.loads 失败的情况。
        """
        decoder = json.JSONDecoder()
        if not isinstance(text, str):
            raise json.JSONDecodeError("content is not str", str(text), 0)
        for i, ch in enumerate(text):
            if ch == "{":
                try:
                    obj, _end = decoder.raw_decode(text[i:])
                    if isinstance(obj, dict):
                        return obj
                except json.JSONDecodeError:
                    continue
        raise json.JSONDecodeError("No JSON object found", text, 0)


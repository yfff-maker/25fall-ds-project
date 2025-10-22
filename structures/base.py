# -*- coding: utf-8 -*-
"""
数据结构基类：提供纯业务逻辑，不包含UI相关代码
"""

class BaseStructure:
    """抽象基类：提供数据结构的基本接口"""
    
    def __init__(self):
        self.active = False

    def set_active(self, is_active: bool):
        """设置激活状态"""
        self.active = is_active

    def is_active(self) -> bool:
        """获取激活状态"""
        return self.active

    # ===== 序列化接口 ===== #
    def to_dict(self) -> dict:
        """导出可序列化的纯数据字典。子类必须实现。"""
        raise NotImplementedError

    def from_dict(self, data: dict) -> None:
        """从字典恢复内部状态。子类必须实现。"""
        raise NotImplementedError
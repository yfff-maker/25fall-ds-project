# -*- coding: utf-8 -*-
import os

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QDockWidget, QFrame, QMessageBox,
    QHBoxLayout, QSpinBox, QDialog, QComboBox, QFileDialog, QAction, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from canvas import Canvas
from widgets.control_panel import ControlPanel
from controllers.main_controller import MainController

'''父节点选择对话框'''
class ParentNodeDialog(QDialog):
    def __init__(self, parent=None, available_nodes=None):
        super().__init__(parent)
        self.setWindowTitle("添加节点")
        self.setModal(True)
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        # 说明文字
        label = QLabel("选择添加节点的父节点：")
        layout.addWidget(label)
        
        # 下拉选择框
        self.combo_box = QComboBox()
        if available_nodes:
            for node_value in available_nodes:
                self.combo_box.addItem(str(node_value))
        layout.addWidget(self.combo_box)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_selected_parent(self):
        return self.combo_box.currentText()

'''初始化整体UI 主窗口类'''
class MainWindow(QMainWindow):
    '''view层'''
    def __init__(self):
        super().__init__()
        try:
            self.setWindowTitle("数据结构可视化模拟器")
            self.resize(1280, 820)

            # central canvas
            self.canvas = Canvas(self) # ← 组合关系：MainWindow 持有 Canvas 实例
            self.setCentralWidget(self.canvas.view)

            # status bar
            self.mode_label = QLabel("准备就绪")
            self.statusBar().addPermanentWidget(self.mode_label, 1)

            # left dock
            self.left_dock = QDockWidget("操作", self)
            self.left_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
            left_widget = QWidget()
            self.left_layout = QVBoxLayout(left_widget)
            self.left_layout.setContentsMargins(8, 8, 8, 8)
            self._build_left_panel()
            self.left_dock.setWidget(left_widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)

            # control panel
            self.ctrl_panel = ControlPanel()
            self.addDockWidget(Qt.BottomDockWidgetArea, self.ctrl_panel)

            # 初始化控制器
            '''控制器层'''
            self.controller = MainController() # ← 组合关系：MainWindow 持有 MainController 实例
            self.current_file_path = None  # 记住当前文件路径
            
            # LLM线程管理
            self._llm_thread = None
            
            # 连接控制器信号
            self.controller.snapshot_updated.connect(self.canvas.render_snapshot)
            self.controller.hint_updated.connect(self.mode_label.setText)
            self.controller.parent_selection_requested.connect(self._handle_parent_selection_request)

            # 选择默认数据结构
            self.select_structure("SequentialList")

            # 构建菜单栏
            self._build_menubar()

            # wire control panel
            self.ctrl_panel.playClicked.connect(self._handle_play_clicked)
            self.ctrl_panel.pauseClicked.connect(self._handle_pause_clicked)
            self.ctrl_panel.stepClicked.connect(self._handle_step_clicked)
            self.ctrl_panel.speedChanged.connect(self.canvas.animator_speed)
        except Exception as e:
            import traceback
            error_msg = f"MainWindow初始化失败:\n{str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
            print(error_msg, file=sys.stderr)
            raise

    '''左侧分组按钮（顺序表/链表/栈/树/BST/哈夫曼）及其点击事件绑定到 select_structure(...)'''
    def _build_left_panel(self):
    # —— DSL命令 —— #
        group_dsl = QGroupBox("DSL命令")
        gdsl = QVBoxLayout(group_dsl)
        
        # DSL命令输入框(多行)
        self.dsl_text_edit = QTextEdit()
        self.dsl_text_edit.setPlaceholderText(
            "# DSL命令示例:\n"
            "# create arraylist with 1,2,3\n"
            "# insert 4 at 1 in arraylist\n"
            "# push 100 to stack\n"
            "# create bst with 50,30,70\n"
        )
        self.dsl_text_edit.setMaximumHeight(150)  # 限制高度
        gdsl.addWidget(self.dsl_text_edit)
        
        # DSL操作按钮
        dsl_btn_layout = QHBoxLayout()
        btn_execute_dsl = QPushButton("执行")
        btn_execute_dsl.clicked.connect(self._handle_execute_dsl)
        btn_clear_dsl = QPushButton("清空")
        btn_clear_dsl.clicked.connect(self._handle_clear_dsl)
        btn_load_dsl = QPushButton("从文件导入")
        btn_load_dsl.clicked.connect(self._handle_load_dsl_file)
        
        dsl_btn_layout.addWidget(btn_execute_dsl)
        dsl_btn_layout.addWidget(btn_clear_dsl)
        dsl_btn_layout.addWidget(btn_load_dsl)
        gdsl.addLayout(dsl_btn_layout)
        
        # 添加DSL结果标签
        self.dsl_result_label = QLabel("")
        self.dsl_result_label.setWordWrap(True)
        self.dsl_result_label.setMaximumHeight(60)
        gdsl.addWidget(self.dsl_result_label)
        
        self.left_layout.addWidget(group_dsl)
    
    # —— 线性表 —— #
        group_list = QGroupBox("线性表")
        gl = QVBoxLayout(group_list)

        btn_seq = QPushButton("顺序表 SequentialList")
        btn_seq.clicked.connect(lambda: self.select_structure("SequentialList"))
        gl.addWidget(btn_seq)

        btn_ll = QPushButton("链表 LinkedList")
        btn_ll.clicked.connect(lambda: self.select_structure("LinkedList"))
        gl.addWidget(btn_ll)

    # —— 栈 —— #
        group_stack = QGroupBox("栈")
        gs = QVBoxLayout(group_stack)

        btn_stack = QPushButton("栈 Stack")
        btn_stack.clicked.connect(lambda: self.select_structure("Stack"))
        gs.addWidget(btn_stack)

    # —— 树 —— #
        group_tree = QGroupBox("树")
        gt = QVBoxLayout(group_tree)

        btn_bt = QPushButton("链式二叉树 BinaryTree")
        btn_bt.clicked.connect(lambda: self.select_structure("BinaryTree"))
        gt.addWidget(btn_bt)

        btn_bst = QPushButton("二叉搜索树 BST")
        btn_bst.clicked.connect(lambda: self.select_structure("BST"))
        gt.addWidget(btn_bst)

        btn_avl = QPushButton("平衡二叉树 AVL")
        btn_avl.clicked.connect(lambda: self.select_structure("AVL"))
        gt.addWidget(btn_avl)

        btn_hf = QPushButton("哈夫曼树 HuffmanTree")
        btn_hf.clicked.connect(lambda: self.select_structure("HuffmanTree"))
        gt.addWidget(btn_hf)

    # —— 动态操作区域容器 —— #
        self.dynamic_container = QFrame()
        self.dynamic_container.setFrameShape(QFrame.StyledPanel)
        self.dynamic_layout = QVBoxLayout(self.dynamic_container)
        self.dynamic_layout.setContentsMargins(8, 8, 8, 8)

    # 左侧栏组合
        self.left_layout.addWidget(group_list)
        self.left_layout.addWidget(group_stack)
        self.left_layout.addWidget(group_tree)
        self.left_layout.addWidget(self.dynamic_container, 1)
        self.left_layout.addStretch(1)

    def _build_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")

        act_open = QAction("打开...", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._action_open)
        file_menu.addAction(act_open)

        act_save = QAction("保存", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._action_save)
        file_menu.addAction(act_save)

        act_save_as = QAction("另存为...", self)
        act_save_as.setShortcut("Ctrl+Shift+S")
        act_save_as.triggered.connect(self._action_save_as)
        file_menu.addAction(act_save_as)
        
        # AI助手菜单
        ai_menu = menubar.addMenu("AI助手")
        
        act_nl_command = QAction("自然语言操作", self)
        act_nl_command.setShortcut("Ctrl+L")
        act_nl_command.triggered.connect(self._action_natural_language)
        ai_menu.addAction(act_nl_command)

    def _action_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开工程", "", "Data Structure Vis (*.dsv);;JSON (*.json);;All Files (*)")
        if not path:
            return
        try:
            self.controller.load_from_file(path)
            self.current_file_path = path  # 记住打开的文件路径
            self.setWindowTitle(f"数据结构可视化模拟器 - {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开失败: {e}")

    def _action_save(self):
        if self.current_file_path:
            # 如果有当前文件路径，直接保存
            try:
                self.controller.save_to_file(self.current_file_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
        else:
            # 否则调用另存为
            self._action_save_as()

    def _action_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存工程", "", "Data Structure Vis (*.dsv);;JSON (*.json);;All Files (*)")
        if not path:
            return
        try:
            # 默认加后缀 .dsv
            if not (path.endswith('.dsv') or path.endswith('.json')):
                path = path + '.dsv'
            self.controller.save_to_file(path)
            self.current_file_path = path  # 记住保存的文件路径
            self.setWindowTitle(f"数据结构可视化模拟器 - {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def _clear_dynamic_panel(self):
        while self.dynamic_layout.count():
            item = self.dynamic_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _make_dynamic_panel_for(self, key: str):
        self._clear_dynamic_panel()
        box = QGroupBox(f"{key} 操作")
        lay = QVBoxLayout(box)

        input_line = QLineEdit()
        input_line.setPlaceholderText("输入一个值，例如 42")

        def get_value():
            text = input_line.text().strip()
            if text == "":
                QMessageBox.warning(self, "提示", "请输入一个值")
                return None
            return text

        if key == "SequentialList":
            build_line = QLineEdit()
            build_line.setPlaceholderText("初始数据：如 1,2,3,4")
            lay.addWidget(build_line)
            btn_build = QPushButton("构建")
            def build_seq():
                self.controller.build_sequential_list(build_line.text().strip())
            btn_build.clicked.connect(build_seq)
            lay.addWidget(btn_build)

            h1 = QHBoxLayout()
            pos_in = QSpinBox(); pos_in.setRange(0, 9999); pos_in.setPrefix("位置 ")
            val_in = QLineEdit(); val_in.setPlaceholderText("值")
            btn_ins = QPushButton("按位插入")
            def do_ins():
                self.controller.insert_at_sequential_list(pos_in.value(), val_in.text().strip())
            btn_ins.clicked.connect(do_ins)
            for wdg in (pos_in, val_in, btn_ins): h1.addWidget(wdg)
            lay.addLayout(h1)

            h2 = QHBoxLayout()
            pos_del = QSpinBox(); pos_del.setRange(0, 9999); pos_del.setPrefix("位置 ")
            btn_del = QPushButton("按位删除")
            btn_del.clicked.connect(lambda: self.controller.delete_at_sequential_list(pos_del.value()))
            h2.addWidget(pos_del); h2.addWidget(btn_del)
            lay.addLayout(h2)

            # 头部和尾部插入按钮
            h3 = QHBoxLayout()
            btn_head = QPushButton("在头部插入")
            btn_head.clicked.connect(lambda: self.controller.insert_at_head_sequential_list(val_in.text().strip()))
            btn_tail = QPushButton("在尾部插入")
            btn_tail.clicked.connect(lambda: self.controller.insert_at_tail_sequential_list(val_in.text().strip()))
            h3.addWidget(btn_head)
            h3.addWidget(btn_tail)
            lay.addLayout(h3)

        elif key == "LinkedList":
            # 添加构建功能
            build_line = QLineEdit()
            build_line.setPlaceholderText("初始数据：如 1,2,3,4")
            lay.addWidget(build_line)
            btn_build = QPushButton("构建")
            def build_ll():
                self.controller.build_linked_list(build_line.text().strip())
            btn_build.clicked.connect(build_ll)
            lay.addWidget(btn_build)

            # 按位插入
            h1 = QHBoxLayout()
            pos_in = QSpinBox(); pos_in.setRange(0, 9999); pos_in.setPrefix("位置 ")
            val_in = QLineEdit(); val_in.setPlaceholderText("值")
            btn_ins = QPushButton("按位插入")
            def do_ins():
                self.controller.insert_at_linked_list(pos_in.value(), val_in.text().strip())
            btn_ins.clicked.connect(do_ins)
            for wdg in (pos_in, val_in, btn_ins): h1.addWidget(wdg)
            lay.addLayout(h1)

            # 按位删除
            h2 = QHBoxLayout()
            pos_del = QSpinBox(); pos_del.setRange(0, 9999); pos_del.setPrefix("位置 ")
            btn_del = QPushButton("按位删除")
            btn_del.clicked.connect(lambda: self.controller.delete_at_linked_list(pos_del.value()))
            h2.addWidget(pos_del); h2.addWidget(btn_del)
            lay.addLayout(h2)

            # 头部和尾部插入
            h3 = QHBoxLayout()
            btn_head = QPushButton("在头部插入")
            btn_head.clicked.connect(lambda: self.controller.insert_at_head_linked_list(val_in.text().strip()))
            btn_tail = QPushButton("在尾部插入")
            btn_tail.clicked.connect(lambda: self.controller.insert_at_tail_linked_list(val_in.text().strip()))
            h3.addWidget(btn_head)
            h3.addWidget(btn_tail)
            lay.addLayout(h3)

            # 按值删除
            lay.addWidget(input_line)
            b1 = QPushButton("按值删除")
            b1.clicked.connect(lambda: self.controller.delete_by_value_linked_list(get_value()))
            lay.addWidget(b1)

        elif key == "Stack":
            # 添加构建功能
            build_line = QLineEdit()
            build_line.setPlaceholderText("初始数据：如 1,2,3,4")
            lay.addWidget(build_line)
            btn_build = QPushButton("构建")
            def build_stack():
                self.controller.build_stack(build_line.text().strip())
            btn_build.clicked.connect(build_stack)
            lay.addWidget(btn_build)
            
            # 添加分隔线
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            lay.addWidget(separator)
            
            # 原有的Push/Pop/Clear功能
            lay.addWidget(input_line)
            b1 = QPushButton("Push")
            b1.clicked.connect(lambda: self.controller.push_stack(get_value()))
            b2 = QPushButton("Pop")
            b2.clicked.connect(lambda: self.controller.pop_stack())
            b3 = QPushButton("Clear Stack")
            b3.clicked.connect(lambda: self.controller.clear_stack())
            lay.addWidget(b1); lay.addWidget(b2); lay.addWidget(b3)

        elif key == "BinaryTree":
            lay.addWidget(input_line)
            b1 = QPushButton("插入节点")
            b1.clicked.connect(lambda: self._insert_binary_tree_node(get_value()))
            lay.addWidget(b1)
            
            # 批量构建功能
            build_line = QLineEdit()
            build_line.setPlaceholderText("批量构建：如 1,2,3,4,5")
            lay.addWidget(build_line)
            btn_build = QPushButton("批量构建")
            btn_build.clicked.connect(lambda: self._build_binary_tree(build_line.text().strip()))
            lay.addWidget(btn_build)
            
            b2 = QPushButton("前序遍历")
            b2.clicked.connect(lambda: self.controller.traverse_binary_tree("pre"))
            b3 = QPushButton("中序遍历")
            b3.clicked.connect(lambda: self.controller.traverse_binary_tree("in"))
            b4 = QPushButton("后序遍历")
            b4.clicked.connect(lambda: self.controller.traverse_binary_tree("post"))
            for b in (b2,b3,b4): lay.addWidget(b)
            
            # 删除功能
            b5 = QPushButton("删除节点")
            b5.clicked.connect(lambda: self._delete_binary_tree_node(get_value()))
            lay.addWidget(b5)

        elif key == "BST":
            # 插入功能
            lay.addWidget(input_line)
            b1 = QPushButton("插入")
            b1.clicked.connect(lambda: self.controller.insert_bst(get_value()))
            lay.addWidget(b1)
            
            # 查找功能 - 单独的输入框和按钮
            search_layout = QHBoxLayout()
            search_input = QLineEdit()
            search_input.setPlaceholderText("输入要查找的值")
            search_btn = QPushButton("查找")
            search_btn.clicked.connect(lambda: self.controller.search_bst(search_input.text().strip()))
            search_layout.addWidget(search_input)
            search_layout.addWidget(search_btn)
            lay.addLayout(search_layout)
            
            # 删除功能
            b3 = QPushButton("删除")
            b3.clicked.connect(lambda: self.controller.delete_bst(get_value()))
            lay.addWidget(b3)

        elif key == "AVL":
            # 插入功能
            lay.addWidget(input_line)
            b1 = QPushButton("插入")
            b1.clicked.connect(lambda: self.controller.insert_avl(get_value()))
            lay.addWidget(b1)
            
            # 批量构建功能
            build_line = QLineEdit()
            build_line.setPlaceholderText("批量插入：如 7,19,16,27,9,5,14,11,17,12")
            lay.addWidget(build_line)
            btn_build = QPushButton("批量构建")
            def build_avl():
                values_str = build_line.text().strip()
                if values_str:
                    self.controller.build_avl(values_str)
            btn_build.clicked.connect(build_avl)
            lay.addWidget(btn_build)
            
            # 清空功能
            b3 = QPushButton("清空树")
            b3.clicked.connect(lambda: self.controller.clear_avl())
            lay.addWidget(b3)

        elif key == "HuffmanTree":
            line = QLineEdit()
            line.setPlaceholderText('输入频率映射，如: A:25,B:15,C:27,D:5,E:30')
            line.setText('A:25,B:15,C:27,D:5,E:30')  # 设置默认值
            lay.addWidget(line)
            b1 = QPushButton("构建哈夫曼树")
            def build():
                self.controller.build_huffman_tree(line.text().strip())
            b1.clicked.connect(build)
            lay.addWidget(b1)

        self.dynamic_layout.addWidget(box)

    @pyqtSlot()
    def select_structure(self, key: str):
        self.controller.select_structure(key)
        self._make_dynamic_panel_for(key)

    def _build_binary_tree(self, values_text: str):
        """批量构建二叉树"""
        try:
            if not values_text:
                QMessageBox.warning(self, "提示", "请输入要构建的节点值")
                return
            
            values = [v.strip() for v in values_text.split(',') if v.strip()]
            if not values:
                QMessageBox.warning(self, "提示", "请输入有效的节点值")
                return
            
            self.controller.build_binary_tree(values)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量构建失败：{str(e)}")
            print(f"Error in _build_binary_tree: {e}")
    
    def _insert_binary_tree_node(self, value):
        """处理二叉树节点插入"""
        try:
            if not value:
                QMessageBox.warning(self, "提示", "请输入一个值")
                return
            
            # 获取当前数据结构
            structure = self.controller.structures.get("BinaryTree")
            if not structure:
                return
            
            # 如果没有根节点，自动创建一个
            if structure.root is None:
                structure.create_root_node(value)
                self.controller._update_snapshot()
                return
            
            # 获取所有现有节点的值
            available_nodes = structure.get_all_node_values()
            
            if not available_nodes:
                QMessageBox.warning(self, "错误", "无法获取现有节点信息")
                return
            
            # 显示父节点选择对话框
            dialog = ParentNodeDialog(self, available_nodes)
            if dialog.exec_() == QDialog.Accepted:
                parent_value = dialog.get_selected_parent()
                if parent_value:
                    self.controller.insert_binary_tree_node(value, parent_value)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"插入节点时发生错误：{str(e)}")
            print(f"Error in _insert_binary_tree_node: {e}")
    
    def _delete_binary_tree_node(self, value):
        """处理二叉树节点删除"""
        try:
            if not value:
                QMessageBox.warning(self, "提示", "请输入要删除的节点值")
                return
            
            # 获取当前数据结构
            structure = self.controller.structures.get("BinaryTree")
            if not structure:
                QMessageBox.warning(self, "错误", "二叉树结构不存在")
                return
            
            # 检查节点是否存在
            target_node = structure.find_node_by_value(value)
            if not target_node:
                QMessageBox.warning(self, "错误", f"未找到节点: {value}")
                return
            
            # 确认删除（因为会删除整个子树）
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除节点 {value} 及其所有子树吗？\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.controller.delete_binary_tree(value)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除节点时发生错误：{str(e)}")
            print(f"Error in _delete_binary_tree_node: {e}")

    def _handle_parent_selection_request(self, value):
        """处理父节点选择请求"""
        # 这个方法会被控制器调用，用于处理需要用户选择父节点的情况
        # 这里可以显示一个对话框让用户选择父节点
        pass
    
    def _handle_play_clicked(self):
        """处理播放按钮点击"""
        if self.controller.current_structure_key == "HuffmanTree":
            # 哈夫曼树动画控制
            self.controller.resume_huffman_animation()
        else:
            # 其他数据结构的动画控制
            self.canvas.animator_play()
    
    def _handle_pause_clicked(self):
        """处理暂停按钮点击"""
        if self.controller.current_structure_key == "HuffmanTree":
            # 哈夫曼树动画控制
            self.controller.pause_huffman_animation()
        else:
            # 其他数据结构的动画控制
            self.canvas.animator_pause()
    
    def _handle_step_clicked(self):
        """处理单步按钮点击"""
        if self.controller.current_structure_key == "HuffmanTree":
            # 哈夫曼树动画控制
            self.controller.step_huffman_animation()
        else:
            # 其他数据结构的动画控制
            self.canvas.animator_step()
    
    def _handle_execute_dsl(self):
        """执行DSL命令"""
        script_text = self.dsl_text_edit.toPlainText().strip()
        if not script_text:
            QMessageBox.warning(self, "提示", "请输入DSL命令")
            return
        
        try:
            # 批量执行DSL脚本
            success_count, fail_count, messages = self.controller.execute_dsl_script(script_text)
            
            # 显示执行结果
            result_msg = f"成功: {success_count}条, 失败: {fail_count}条"
            self.dsl_result_label.setText(result_msg)
            
            # 如果有失败的命令,显示详细消息
            if fail_count > 0:
                error_details = "\n".join([msg for msg in messages if msg.startswith("✗")])
                QMessageBox.warning(self, "执行结果", f"{result_msg}\n\n失败的命令:\n{error_details}")
            else:
                QMessageBox.information(self, "执行成功", result_msg)
                
        except Exception as e:
            QMessageBox.critical(self, "执行失败", f"DSL执行出错: {str(e)}")
            self.dsl_result_label.setText(f"错误: {str(e)}")
    
    def _handle_clear_dsl(self):
        """清空DSL命令输入框"""
        self.dsl_text_edit.clear()
        self.dsl_result_label.clear()
    
    def _handle_load_dsl_file(self):
        """从文件加载DSL脚本"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "打开DSL脚本", 
            "", 
            "DSL Script (*.dsl);;Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.dsl_text_edit.setPlainText(content)
            self.dsl_result_label.setText(f"已加载: {path}")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法读取文件: {str(e)}")
    
    def _action_natural_language(self):
        """打开自然语言操作对话框"""
        dialog = NaturalLanguageDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            user_input = dialog.get_input()
            if user_input:
                self._execute_natural_language(user_input)
    
    def _execute_natural_language(self, user_input: str):
        """执行自然语言命令（异步执行）"""
        # 如果已有线程在运行，先停止
        if self._llm_thread and self._llm_thread.isRunning():
            self._llm_thread.terminate()
            self._llm_thread.wait()
        
        # 显示加载提示（带取消按钮）
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("处理中")
        msg_box.setText("正在调用LLM处理自然语言...\n请稍候，这可能需要几秒钟。")
        msg_box.setStandardButtons(QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Cancel)
        cancel_button = msg_box.button(QMessageBox.Cancel)
        cancel_button.setText("取消")
        
        # 创建并启动工作线程
        self._llm_thread = LLMWorkerThread(self.controller, user_input, self)
        self._llm_thread.finished.connect(
            lambda success, message, action: self._on_llm_finished(success, message, action, msg_box)
        )
        self._llm_thread.error.connect(
            lambda error_msg: self._on_llm_error(error_msg, msg_box)
        )
        
        # 连接取消按钮
        def on_cancel():
            if self._llm_thread and self._llm_thread.isRunning():
                self._llm_thread.terminate()
                self._llm_thread.wait()
            msg_box.close()
        
        cancel_button.clicked.connect(on_cancel)
        
        # 启动线程
        self._llm_thread.start()
        
        # 显示对话框（非阻塞，线程完成后会自动关闭）
        msg_box.show()
        msg_box.raise_()
        msg_box.activateWindow()
    
    def _on_llm_finished(self, success: bool, message: str, action, msg_box: QMessageBox):
        """处理LLM调用完成"""
        # 关闭加载提示
        if msg_box:
            msg_box.accept()  # 使用accept()确保对话框正确关闭
        
        # 清理线程
        if self._llm_thread:
            self._llm_thread.deleteLater()
            self._llm_thread = None
        
        if success and action:
            # 在主线程中执行操作（确保动画正常）
            try:
                exec_success, exec_message = self.controller.action_executor.execute_action(action)
                
                # 显示转换后的JSON动作和执行结果
                import json
                action_json = json.dumps(action, ensure_ascii=False, indent=2) if action else "无"
                
                if exec_success:
                    QMessageBox.information(
                        self, 
                        "执行成功", 
                        f"{exec_message}\n\n转换后的动作：\n{action_json}"
                    )
                else:
                    QMessageBox.warning(
                        self, 
                        "执行失败", 
                        f"{exec_message}\n\n转换后的动作：\n{action_json}\n\n提示：您可以尝试在DSL输入框中手动输入DSL命令。"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "执行错误",
                    f"执行操作时出错: {str(e)}"
                )
        else:
            QMessageBox.warning(
                self, 
                "转换失败", 
                f"{message}\n\n提示：您可以尝试在DSL输入框中手动输入DSL命令。"
            )
    
    def _on_llm_error(self, error_msg: str, msg_box: QMessageBox):
        """处理LLM调用错误"""
        # 关闭加载提示
        if msg_box:
            msg_box.accept()  # 使用accept()确保对话框正确关闭
        
        # 清理线程
        if self._llm_thread:
            self._llm_thread.deleteLater()
            self._llm_thread = None
        
        QMessageBox.critical(self, "错误", f"执行自然语言命令时出错: {error_msg}")


'''LLM调用工作线程'''
class LLMWorkerThread(QThread):
    """LLM调用工作线程"""
    finished = pyqtSignal(bool, str, object)  # (success, message, action)
    error = pyqtSignal(str)  # error_message
    
    def __init__(self, controller, user_input, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.user_input = user_input
    
    def run(self):
        """在后台线程中执行LLM调用（仅转换，不执行操作）"""
        try:
            # 只进行LLM转换，不执行操作（操作必须在主线程中执行以支持动画）
            success, message, action = self.controller.convert_natural_language_to_action(self.user_input)
            self.finished.emit(success, message, action)
        except Exception as e:
            self.error.emit(str(e))


'''自然语言输入对话框'''
class NaturalLanguageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自然语言操作")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel("请输入自然语言描述，系统将自动转换为操作指令：\n例如：创建一个包含数据元素[5,3,7,2,4]的二叉搜索树")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入自然语言描述...")
        self.input_text.setMaximumHeight(150)
        layout.addWidget(self.input_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("执行")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_input(self):
        """获取用户输入"""
        return self.input_text.toPlainText().strip()

def main():
    try:
        print("正在初始化QApplication...", file=sys.stderr)
        app = QApplication(sys.argv)
        print("正在创建MainWindow...", file=sys.stderr)
        win = MainWindow()
        print("正在显示窗口...", file=sys.stderr)
        win.show()
        win.raise_()  # 将窗口提升到最前面
        win.activateWindow()  # 激活窗口
        print("进入事件循环...", file=sys.stderr)
        sys.exit(app.exec_())
    except Exception as e:
        import traceback
        error_msg = f"程序启动失败:\n{str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        
        # 如果GUI已经初始化，尝试显示错误对话框
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("启动错误")
            msg.setText(error_msg)
            msg.exec_()
        except:
            # 如果GUI未初始化，直接打印到控制台
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
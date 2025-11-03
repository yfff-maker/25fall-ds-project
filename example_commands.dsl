# 数据结构自动化测试脚本
# 本文件包含各种数据结构的DSL命令示例

# ========================
# 顺序表操作
# ========================
create arraylist with 1,2,3
insert 4 at 1 in arraylist
delete at 0 from arraylist
delete at 1 from arraylist

# ========================
# 链表操作
# ========================
create linkedlist with 10,20,30
insert 15 at 1 in linkedlist
delete at 2 from linkedlist

# ========================
# 栈操作
# ========================
create stack
push 100 to stack
push 200 to stack
pop from stack

# ========================
# 二叉树操作(层序构建和单个插入)
# ========================

build binarytree with 10,11,12,13,14,15,16
insert 8 as left of 4 in binarytree
insert 9 as right of 4 in binarytree
delete 4 from binarytree

# ========================
# 二叉搜索树操作
# ========================
create bst with 50,30,70,20,40,60,80
insert 25 in bst
search 60 in bst
delete 30 from bst

# ========================
# AVL树操作
# ========================
create avl with 7,19,16,27,9,5,14,11,17,12
insert 25 in avl
clear avl

# ========================
# 哈夫曼树操作
# ========================
build huffman with a:5,b:9,c:12,d:13,e:16,f:45


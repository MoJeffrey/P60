# _*_ coding: utf-8 _*_
# @Time : 2022/6/3 0:18
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : group_view.py
# @desc : 分组显示成绩对话框

from PyQt5.QtWidgets import QDialog, QAbstractItemView, QTableView, QHeaderView, QHBoxLayout, QMessageBox, QVBoxLayout, \
    QPushButton, QSpacerItem, QSizePolicy, QWidget
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from PyQt5.QtCore import Qt

from typing import List

from models import UserObjectGroup

"""
分组显示成绩
"""


class GroupDialog(QDialog):
    def __init__(self, data: UserObjectGroup, parent: QWidget):
        super().__init__()
        self.data = data
        self.parent = parent
        self.init_widget()
        self.load_data()

    # 初始化组件
    def init_widget(self):
        self.setMinimumSize(600, 600)
        self.setWindowTitle('组内设置')
        self.setWindowModality(Qt.ApplicationModal)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        bt_layout = QHBoxLayout()
        main_layout.addLayout(bt_layout)

        bt_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        clear_bt = QPushButton('清空分数')
        bt_layout.addWidget(clear_bt)
        clear_bt.clicked.connect(self.clear_score)

        self.group_table = QTableView()
        main_layout.addWidget(self.group_table)
        self.group_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.model = QStandardItemModel(0, 0)
        self.model.setHorizontalHeaderLabels(('用户名', '用户id', '原积分', '本局积分', '现积分', '兑换分'))
        self.group_table.setModel(self.model)

        self.model.itemChanged.connect(self.modify_data)

    # 加载数据
    def load_data(self):
        for user in self.data.users:
            self.model.appendRow((QStandardItem(user.username), QStandardItem(
                user.id_), QStandardItem(str(user.origin_score)), QStandardItem(str(user.round_score)), QStandardItem(str(user.current_score)), QStandardItem(str(user.points))))

    # 编辑数据
    def modify_data(self):
        self.model.itemChanged.disconnect(self.modify_data)
        row = self.group_table.currentIndex().row()
        col = self.group_table.currentIndex().column()
        current_record = self.data.users[row]

        if col == 0:
            current_record.username = self.model.item(row, col).text()
        elif col == 1:
            current_record.id_ = self.model.item(row, col).text()
        elif col == 2:
            try:
                current_record.origin_score = float(self.model.item(row, col).text())
                current_record.current_score = current_record.origin_score + current_record.round_score
                self.model.item(row, 4).setText(str(current_record.current_score))
                current_record.points = self.parent.factor * current_record.current_score
                self.model.item(row, 5).setText(str(current_record.points))
            except:
                self.model.item(row, col).setText(str(current_record.origin_score))
        elif col == 3:
            try:
                current_record.round_score = float(self.model.item(row, col).text())
                current_record.current_score = current_record.origin_score + current_record.round_score
                self.model.item(row, 4).setText(str(current_record.current_score))
                current_record.points = self.parent.factor * current_record.current_score
                self.model.item(row, 5).setText(str(current_record.points))
            except:
                self.model.item(row, col).setText(str(current_record.round_score))
        elif col == 4:
            try:
                current_record.current_score = float(self.model.item(row, col).text())
                current_record.points = self.parent.factor * current_record.current_score
                self.model.item(row, 5).setText(str(current_record.points))
                current_record.origin_score = 0
                current_record.round_score = 0
                self.model.item(row, 2).setText('0')
                self.model.item(row, 3).setText('0')
            except:
                self.model.item(row, col).setText(str(current_record.current_score))
        elif col == 5:
            try:
                current_record.points = float(self.model.item(row, col).text())
                current_record.current_score = round(current_record.points / self.parent.factor ,2)
                self.model.item(row, 4).setText(str(current_record.current_score))
                current_record.origin_score = 0
                current_record.round_score = 0
                self.model.item(row, 2).setText('0')
                self.model.item(row, 3).setText('0')
            except:
                self.model.item(row, col).setText(str(current_record.points))
        self.model.itemChanged.connect(self.modify_data)

    # 清空分数
    def clear_score(self):
        for user in self.data.users:
            user.points = 0
            user.origin_score = 0
            user.current_score = 0
            user.round_score = 0
        for row in range(self.model.rowCount()):
            self.model.item(row, 2).setText(str(0))
            self.model.item(row, 3).setText(str(0))
            self.model.item(row, 4).setText(str(0))
            self.model.item(row, 5).setText(str(0))

    # 获取数据
    def get_data(self):
        return self.data

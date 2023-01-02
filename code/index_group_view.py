# 根据标签分组详情显示

from PyQt5.QtWidgets import QDialog, QAbstractItemView, QTableView, QHeaderView, QHBoxLayout, QVBoxLayout, QLineEdit, \
    QLabel, QMenu, QAction, QMessageBox, QPushButton
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from PyQt5.QtCore import Qt

from typing import List

from models import IndexGroup, UserObject, UserObjectGroup

from copy import copy

ROUND_FACTOR = 0


class IndexGroupView(QDialog):
    # 初始化对象
    def __init__(self, index_group: IndexGroup, total_list: List[UserObject or UserObjectGroup]):
        super().__init__()
        self.index_group = index_group

        # 总表
        self.total_list = total_list

        self.init_widgets()
        self.update_data()

    # 初始化组件
    def init_widgets(self):
        self.setMinimumSize(600, 600)
        self.setWindowTitle('标签组')
        self.setWindowModality(Qt.ApplicationModal)

        outer_layout = QVBoxLayout()
        self.setLayout(outer_layout)

        # 组名设置
        config_layout = QHBoxLayout()
        outer_layout.addLayout(config_layout)

        _ = QLabel('组标签')
        config_layout.addWidget(_)
        self.index_e = QLineEdit()
        self.index_e.setText(self.index_group.index)
        self.index_e.textChanged.connect(self.update_index)
        config_layout.addWidget(self.index_e)

        _ = QLabel('限制分数1')
        config_layout.addWidget(_)
        self.limit_e = QLineEdit()
        self.limit_e.setText(str(self.index_group.limit))
        config_layout.addWidget(self.limit_e)

        _ = QLabel('限制分数2')
        config_layout.addWidget(_)
        self.limit2_e = QLineEdit()
        self.limit2_e.setText(str(self.index_group.limit2))
        config_layout.addWidget(self.limit2_e)

        clear_bt = QPushButton('清空轮数')
        config_layout.addWidget(clear_bt)
        clear_bt.clicked.connect(self.clear_round_num)

        main_layout = QHBoxLayout()
        outer_layout.addLayout(main_layout)

        self.group_table = QTableView()
        main_layout.addWidget(self.group_table)
        self.group_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.model = QStandardItemModel(0, 0)
        self.model.setHorizontalHeaderLabels(('#', '用户名', '用户id', '当前分数', '游玩次数'))
        self.group_table.setModel(self.model)
        self.group_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.group_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_table.customContextMenuRequested.connect(self.stat_tot_menu)

    # 清空轮数
    def clear_round_num(self):
        for obj in self.index_group.data_list:
            if isinstance(obj, UserObject):
                obj.round_num = 0
            else:
                for o in obj.users:
                    o.round_num = 0

        self.update_data()

    # 更新组名
    def update_index(self):
        index = self.index_e.text()
        if not index:
            return
        self.index_group.index = index
        self.index_group.data_list.clear()

        for obj in self.total_list:
            if obj.index and obj.index[0] == index[0]:
                self.index_group.data_list.append(obj)
        self.update_data()

    # 更新数据
    def update_data(self):
        self.index_group.data_list = IndexGroupView.sort(self.index_group.data_list)
        for _ in range(self.model.rowCount()):
            self.model.removeRow(0)
        for obj in self.index_group.data_list:
            if isinstance(obj, UserObject):
                self.model.appendRow((QStandardItem(obj.index), QStandardItem(obj.username), QStandardItem(obj.id_),
                                      QStandardItem(str(obj.points)), QStandardItem(str(obj.round_num))))
            elif isinstance(obj, UserObjectGroup):
                self.model.appendRow((QStandardItem(obj.index), QStandardItem(obj.group_name),
                                      QStandardItem(obj.get_display_id()), QStandardItem(str(obj.get_total_score())),
                                      QStandardItem(str(obj.get_total_roundnum()))))

    # 关闭时自动保存
    def closeEvent(self, evt):
        try:
            self.index_group.limit = int(self.limit_e.text())
            self.index_group.limit2 = int(self.limit2_e.text())
            self.index_group.index = self.index_e.text()
        except:
            pass
        return super().closeEvent(evt)

    # 获取数据
    def get_data(self):
        return self.index_group

    # 分数求和菜单
    def stat_tot_menu(self, pos):
        menu = QMenu()
        calc_tot_action = QAction('求总和')
        calc_tot_round_action = QAction('求轮数总和')
        menu.addAction(calc_tot_action)
        menu.addAction(calc_tot_round_action)
        action = menu.exec_(self.mapToGlobal(pos))

        if action == calc_tot_action:
            score = 0
            for s in self.index_group.data_list:
                if isinstance(s, UserObject):
                    score += s.points
                elif isinstance(s, UserObjectGroup):
                    score += s.get_total_score()
            QMessageBox.information(self, '提示', '分数总和为: ' + str(round(score, ROUND_FACTOR)))

        elif action == calc_tot_round_action:
            rounds = 0
            for s in self.index_group.data_list:
                if isinstance(s, UserObject):
                    rounds += s.round_num
                elif isinstance(s, UserObjectGroup):
                    rounds += s.get_total_roundnum()
            QMessageBox.information(self, '提示', '轮数总和为: ' + str(round(rounds, ROUND_FACTOR)))

    # 0 放在最后排序
    @staticmethod
    def sort(L: List):
        zero_list = []
        L_copy = copy(L)
        for item in L:
            if item.points == 0:
                L_copy.remove(item)
                zero_list.append(item)
        L_copy = sorted(L_copy, key=lambda x: x.get_total_score(), reverse=True)
        L_copy.extend(zero_list)
        return L_copy

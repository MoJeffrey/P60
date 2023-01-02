# _*_ coding: utf-8 _*_
# @Time : 2022/5/22 0:38
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : main_view.py
# @desc : 主要界面
import os
from copy import copy
from functools import partial
from typing import List

from PIL import Image
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QFileDialog, QHBoxLayout,
                             QHeaderView, QMessageBox, QPushButton, QTableView,
                             QVBoxLayout, QWidget, QMenu, QInputDialog, QComboBox, QAction, QMenuBar,
                             QLineEdit, QLabel)

import config_operator
from digit_api import BaiduAPI, ResultParser
from group_view import GroupDialog
from image_view import ImageView
from index_group_view import IndexGroupView
from models import IndexGroup, UserObject, UserObjectGroup
from score_operator import ScoreOperator

SPECIAL_IDS = ['22290943', '22259876', '22140649', '22230343',
               '22230343', '22262034', '21961105', '22167856', '22212953', '22255970', '22212374', '22227321',
               '22290943', '22216231', '22208876']

# 标签组数量
INDEX_GROUP_NUM = 20

# 四舍五入位数
ROUND_FACTOR = 0


def new_rounding(n, m=0):
    return int(n)


class MainView(QWidget):
    # 初始化主界面
    def __init__(self):
        super().__init__()
        # 当前结果
        self.current_result: List[UserObject] = []
        # 全局结果
        self.record_result: List[UserObject] = []

        # 全局结果备份
        self.record_result_bk: List[UserObject] = []

        # 当前搜索的结果，对应原表中的index
        self.record_result_bk_index: List[int] = []

        # 标签组
        self.index_groups: List[IndexGroup] = []
        self.group_bts: List[QPushButton] = []

        # 分数统计
        self.score_stats: List[int] = []

        # 转换比率
        self.factor = 1

        self.is_first_time_flag = True

        # 减少数量
        self.reduce_factor = 100

        # 排序方法
        self.sort_method = True

        # 初始化api
        self.api = None
        self.init_api()
        self.init_widget()

    # 初始化api调用
    def init_api(self):
        # 获取设置好的factor值
        if os.path.exists('factor'):
            try:
                with open('factor', 'r') as f:
                    self.factor = float(f.read())
            except:
                pass

        # 获取相减系数
        if os.path.exists('reduce_factor'):
            try:
                with open('reduce_factor', 'r') as f:
                    self.reduce_factor = int(f.read())
            except:
                pass

        # 初始化分组
        self.index_groups = []
        for _ in range(INDEX_GROUP_NUM):
            self.index_groups.append(IndexGroup())

        cid, secret = config_operator.read_api_info()
        token = config_operator.get_token()
        if token:
            self.api = BaiduAPI(cid, secret, token)
        else:
            self.api = BaiduAPI(cid, secret, None)
            token = self.api.get_token()
            config_operator.store_token(token)

    # 初始化组件
    def init_widget(self):
        # 界面参数设置
        self.setWindowTitle('分数记录工具')
        self.setMinimumSize(1000, 700)
        self.setAcceptDrops(True)

        # 获取当前菜单
        self.menu_bar = QMenuBar()

        # 最外层布局
        outer_layout = QVBoxLayout()
        self.setLayout(outer_layout)
        outer_layout.addWidget(self.menu_bar)

        top_menu_layout = QHBoxLayout()

        # 筛选条件
        record_filter_e = QLineEdit()
        record_filter_e.setPlaceholderText('搜索')
        top_menu_layout.addWidget(record_filter_e)
        record_filter_e.setFixedWidth(80)

        # 分组按钮
        group_bt_h_layout = QHBoxLayout()
        group_bt_v_layout = QVBoxLayout()
        group_bt_layout = QHBoxLayout()
        top_menu_layout.addLayout(group_bt_layout, 1)
        group_bt_h_layout.addLayout(group_bt_v_layout)

        # 添加最上面菜单栏
        outer_layout.addLayout(top_menu_layout)
        bt_setting = QPushButton("设置")
        bt_clear = QPushButton("清空")
        bt_data = QPushButton("数据")

        # 主要布局
        main_layout = QHBoxLayout()
        outer_layout.addLayout(main_layout)

        score_stat_layout = QVBoxLayout()
        main_layout.addLayout(score_stat_layout, 1)
        # main_layout.setStretchFactor(score_stat_layout, 1)

        # 分数统计表格
        score_clear_bt = QPushButton('清空左侧统计')
        score_clear_bt.clicked.connect(self.clear_score_stat)
        # score_stat_layout.addWidget(score_clear_bt)

        score_table = QTableView()
        score_stat_layout.addWidget(score_table)
        score_table.setFixedWidth(80)
        score_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.stat_model = QStandardItemModel(0, 0)
        self.stat_model.setHorizontalHeaderLabels(('分数',))
        score_table.setModel(self.stat_model)

        # 新增分组按钮
        for _ in range(INDEX_GROUP_NUM):
            current_bt = QPushButton(self.index_groups[_].index)
            group_bt_layout.addWidget(current_bt)
            current_bt.clicked.connect(partial(self.show_index_group, _))
            current_bt.setStyleSheet('background-color: white;')
            self.group_bts.append(current_bt)

        refresh_group_bt = QPushButton('刷新')
        top_menu_layout.addWidget(refresh_group_bt)
        refresh_group_bt.clicked.connect(self.update_index_group)

        # 左侧布局
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)

        # 左侧按钮布局
        left_button_layout = QHBoxLayout()
        left_layout.addLayout(left_button_layout)

        # 合并中间和右侧布局
        right_side_layout = QVBoxLayout()
        right_side_layout.addLayout(group_bt_h_layout)
        right_side_lower_layout = QHBoxLayout()
        right_side_layout.addLayout(right_side_lower_layout)
        main_layout.addLayout(right_side_layout)
        main_layout.setStretchFactor(right_side_layout, 4)
        main_layout.setStretchFactor(left_layout, 4)

        # 中间当前识别数据布局
        center_layout = QVBoxLayout()
        right_side_lower_layout.addLayout(center_layout)
        right_side_lower_layout.setStretchFactor(center_layout, 8)

        # 中间操作按钮
        # center_button_layout = QHBoxLayout()
        # center_layout.addLayout(center_button_layout)

        # 清除数据
        def clear_data():
            self.current_result.clear()
            self.image_view.current_scene.clear()
            update_current_info()
            update_record_info()

        def set_factor():
            # 获取设置好的factor值
            factor = 1.0
            if os.path.exists('factor'):
                try:
                    with open('factor', 'r') as f:
                        factor = float(f.read())
                except:
                    pass
            factor = QInputDialog.getDouble(
                self, '设置转换比率', '转换比率', factor, 0.001, 1.0, 2)[0]
            if not factor:
                return

            self.factor = factor
            # 刷新 重算分数
            for obj in self.record_result:
                if isinstance(obj, UserObject):
                    obj.points = new_rounding(obj.current_score * self.factor, ROUND_FACTOR)
                elif isinstance(obj, UserObjectGroup):
                    for user in obj.users:
                        user.points = new_rounding(user.current_score * self.factor, ROUND_FACTOR)
            self.update_record_info()

            with open('factor', 'w') as f:
                f.write(str(self.factor))

        # 设置转换按钮
        factor_button = QPushButton('设置转换率')
        factor_button.clicked.connect(set_factor)
        # center_button_layout.addWidget(factor_button)

        reduce_factor_button = QPushButton('设置相减系数')
        reduce_factor_button.clicked.connect(self.edit_reduce_factor)
        # center_button_layout.addWidget(reduce_factor_button)

        # 清除数据按钮
        clear_button = QPushButton('清空右侧新增')
        clear_button.clicked.connect(clear_data)
        # center_button_layout.addWidget(clear_button)

        current_table = QTableView()
        center_layout.addWidget(current_table)
        current_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.current_model = QStandardItemModel(0, 0)
        self.current_model.setHorizontalHeaderLabels(('用户名', '用户id', '当前分数'))
        current_table.setModel(self.current_model)

        # 设置菜单栏
        setting_menu = QMenu()
        action_factor_button = QAction('设置转换率', setting_menu)
        action_factor_button.triggered.connect(set_factor)
        setting_menu.addAction(action_factor_button)

        action_reduce_factor_button = QAction('设置相减系数', setting_menu)
        action_reduce_factor_button.triggered.connect(self.edit_reduce_factor)
        setting_menu.addAction(action_reduce_factor_button)
        bt_setting.setMenu(setting_menu)

        # 数据菜单栏
        data_menu = QMenu()
        action_factor_button = QAction('读取数据', data_menu)
        action_factor_button.triggered.connect(self.read_data)
        data_menu.addAction(action_factor_button)

        action_reduce_factor_button = QAction('保存数据', data_menu)
        action_reduce_factor_button.triggered.connect(self.store_data)
        data_menu.addAction(action_reduce_factor_button)
        bt_data.setMenu(data_menu)

        # current_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 更新当前信息
        def update_current_info():
            # 清空原始数据
            for _ in range(self.current_model.rowCount()):
                self.current_model.removeRow(0)

            count = 0
            for result in self.current_result:
                is_colored = False
                # 如果score为None 则为识别可能出现错误
                if result.points is None:
                    result.points = 0
                    is_colored = True
                self.current_model.appendRow((QStandardItem(result.username), QStandardItem(
                    result.id_), QStandardItem(str(result.points))))
                if is_colored:
                    self.current_model.item(self.current_result.index(
                        result), 2).setBackground(Qt.red)

                # 是否是特殊的 需要提醒 标注绿色
                if result.id_ in SPECIAL_IDS:
                    self.current_model.item(self.current_result.index(
                        result), 0).setBackground(Qt.green)

                # 设置高度
                self.current_table.setRowHeight(count, 4)
                count += 1

        # 显示房间号
        self.room_num_lb = QLabel('房间号：')
        left_layout.addWidget(self.room_num_lb)
        self.room_num_lb.setAlignment(Qt.AlignCenter)
        self.room_num_lb.setStyleSheet('color: red;')

        # 左左侧全部数据设置
        record_table = QTableView()
        left_layout.addWidget(record_table)
        # record_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.record_model = QStandardItemModel(0, 0)
        self.record_model.setHorizontalHeaderLabels(
            ('#', '限制', '用户id', '用户名', '原积分', '本局积分', '现积分', '兑换分'))
        record_table.setModel(self.record_model)

        # 不可编辑
        # record_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # record_table.setSelectionBehavior(QAbstractItemView.Select)

        # 更新记录显示
        def update_record_info():
            for _ in range(self.record_model.rowCount()):
                self.record_model.removeRow(0)

            for record in self.record_result:
                if isinstance(record, UserObject):
                    # 单独用户的处理
                    self.record_model.appendRow(
                        (QStandardItem(str(record.index)), QStandardItem(str(record.point_limit)),
                         QStandardItem(record.id_), QStandardItem(record.username),
                         QStandardItem(str(record.origin_score)), QStandardItem(str(record.round_score)),
                         QStandardItem(str(record.current_score)), QStandardItem(str(record.points))))
                    if record.points <= record.point_limit:
                        self.record_model.item(self.record_result.index(
                            record), 7).setBackground(Qt.yellow)
                elif isinstance(record, UserObjectGroup):
                    # 用户组的处理
                    self.record_model.appendRow(
                        (QStandardItem(str(record.index)), QStandardItem(str(record.point_limit)),
                         QStandardItem(record.get_display_id()), QStandardItem(record.group_name),
                         QStandardItem(str(record.get_total_origin())), QStandardItem(str(record.get_total_round())),
                         QStandardItem(str(record.get_total_current())), QStandardItem(str(record.get_total_score()))))
                    if record.get_total_score() <= record.point_limit:
                        self.record_model.item(self.record_result.index(
                            record), 7).setBackground(Qt.yellow)

                item = self.record_model.item(
                    self.record_result.index(record), 0)
                if item:
                    # 表头编码全部设置成灰色
                    item.setBackground(Qt.gray)
            record_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            record_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
            record_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            record_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            record_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
            record_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
            record_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
            record_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
            #
            # 设置标号列宽度
            record_table.setColumnWidth(0, 35)
            record_table.setColumnWidth(1, 55)
            record_table.setColumnWidth(2, 85)
            record_table.setColumnWidth(3, 110)

            for _ in range(self.record_model.rowCount()):
                record_table.setRowHeight(_, 15)

        def sort_items():
            self.record_result = sorted(
                self.record_result, key=lambda x: x.index, reverse=self.sort_method)
            self.sort_method = not self.sort_method
            update_record_info()

        record_table.horizontalHeader().setSectionsClickable(True)
        record_table.horizontalHeader().sectionClicked.connect(sort_items)

        # 双击显示组内详细信息
        def show_group_info(index):
            row = index.row()
            record = self.record_result[row]
            if isinstance(record, UserObjectGroup):
                dialog = GroupDialog(record, self)
                dialog.exec_()
                new_record = dialog.get_data()
                old_index = self.record_result.index(record)
                self.record_result.remove(record)
                self.record_result.insert(old_index, new_record)

                update_record_info()

        # record_table.clicked.connect(show_group_info)
        # 设置分数菜单
        def show_calc_menu(pos):
            if current_table.selectionModel().selection().indexes():
                menu = QMenu()
                action_x9 = menu.addAction(u'x0.9')
                action_x9mf = menu.addAction(u'x0.9 - ' + str(self.reduce_factor))
                action_mf = menu.addAction(u'- ' + str(self.reduce_factor))
                action_x9mu = menu.addAction(u'x0.9 - 用户数x' + str(self.reduce_factor))
                action_mu = menu.addAction(u'- 用户数x' + str(self.reduce_factor))
                action_tot = menu.addAction(u'全部总和')
                action = menu.exec_(
                    QPoint(current_table.x() + current_table.width(), current_table.mapToGlobal(pos).y()))

                if action == action_x9:
                    for index in current_table.selectionModel().selection().indexes():
                        row = index.row()
                        original_score = int(
                            self.current_model.item(row, 2).text())
                        new_score = new_rounding(original_score * 0.9, ROUND_FACTOR)
                        self.current_model.item(row, 2).setText(str(new_score))
                        self.current_result[row].points = new_score
                elif action == action_x9mu:
                    for index in current_table.selectionModel().selection().indexes():
                        row = index.row()
                        original_score = int(
                            self.current_model.item(row, 2).text())
                        user_number = 0
                        for _ in range(self.current_model.rowCount()):
                            score = int(self.current_model.item(_, 2).text())
                            if score != 0:
                                user_number += 1

                        new_score = new_rounding(original_score * 0.9 - user_number * self.reduce_factor, ROUND_FACTOR)
                        self.current_model.item(row, 2).setText(str(new_score))
                        self.current_result[row].points = new_score
                elif action == action_mu:
                    for index in current_table.selectionModel().selection().indexes():
                        row = index.row()
                        original_score = int(
                            self.current_model.item(row, 2).text())
                        user_number = 0
                        for _ in range(self.current_model.rowCount()):
                            score = int(self.current_model.item(_, 2).text())
                            if score != 0:
                                user_number += 1
                        new_score = new_rounding(original_score - user_number * self.reduce_factor, ROUND_FACTOR)
                        self.current_model.item(row, 2).setText(str(new_score))
                        self.current_result[row].points = new_score
                elif action == action_tot:
                    tot = 0
                    for r in range(self.current_model.rowCount()):
                        tot += float(self.current_model.item(r, 2).text())
                    QMessageBox.information(
                        self, '求和', f'当前全部分数总和为:{str(new_rounding(tot, ROUND_FACTOR))}', QMessageBox.Yes,
                        QMessageBox.Yes)
                elif action == action_x9mf:
                    for index in current_table.selectionModel().selection().indexes():
                        row = index.row()
                        original_score = int(
                            self.current_model.item(row, 2).text())
                        new_score = new_rounding(original_score * 0.9 - self.reduce_factor, ROUND_FACTOR)
                        self.current_model.item(row, 2).setText(str(new_score))
                        self.current_result[row].points = new_score
                elif action == action_mf:
                    for index in current_table.selectionModel().selection().indexes():
                        row = index.row()
                        original_score = int(
                            self.current_model.item(row, 2).text())
                        new_score = original_score - self.reduce_factor
                        self.current_model.item(row, 2).setText(str(new_score))
                        self.current_result[row].points = new_score
            self.update_index_group()

        # 当右键表格的时候弹出合并选项
        current_table.setContextMenuPolicy(Qt.CustomContextMenu)
        current_table.customContextMenuRequested.connect(show_calc_menu)

        # 当进行多个人合并的时候 显示菜单
        def show_merge_menu(pos):
            # 如果有选择
            if record_table.selectionModel().selection().indexes():
                menu = QMenu()
                group_item = menu.addAction(u'分组')
                dismiss_item = menu.addAction(u'解散')
                view_item = menu.addAction(u'详情')
                menu.addSeparator()
                tot_item = menu.addAction(u'局部总和')
                tot_all_item = menu.addAction(u'全部总和')
                action = menu.exec_(QPoint(record_table.x() + record_table.width(), record_table.mapToGlobal(pos).y()))

                if action == group_item:
                    # 进行分组
                    users = []
                    group_name = ''
                    past_row = []
                    remove_queue = []
                    for model_index in record_table.selectionModel().selection().indexes():
                        row = model_index.row()
                        if row in past_row:
                            continue
                        past_row.append(row)
                        record = self.record_result[row]
                        # 判断是否是用户组
                        if isinstance(record, UserObject):
                            users.append(record)
                            remove_queue.append(record)
                            # 初始化一个组名
                            group_name += record.username + ','
                        else:
                            users.extend(record.users)
                            group_name = record.group_name.replace(
                                '<', '').replace('>', '')
                            remove_queue.append(record)
                    # 计算分数
                    total_points = 0
                    for user in users:
                        total_points += user.points
                    # group name两边有尖括号
                    group_name = f'<{group_name}>'
                    user_group = UserObjectGroup(
                        group_name, users, total_points)

                    # 移除列队中的UserObject替换为UserObjectGroup
                    self.record_result.append(user_group)
                    for record in remove_queue:
                        self.record_result.remove(record)

                    update_record_info()
                    self.record_table.verticalScrollBar().setSliderPosition(
                        self.record_model.rowCount() - 1)

                elif action == dismiss_item:
                    # 解散
                    for model_index in record_table.selectionModel().selection().indexes():
                        row = model_index.row()
                        record = self.record_result[row]
                        if isinstance(record, UserObjectGroup):
                            # 新建单独用户
                            for user in record.users:
                                username = user.username
                                points = user.points
                                id_ = user.id_
                                limit = record.point_limit // len(record.users)
                                user_obj = UserObject(
                                    username, id_, points, limit)
                                user_obj.current_score = user.current_score
                                user_obj.origin_score = user.origin_score
                                user_obj.round_score = user.round_score
                                user_obj.round_num = user.round_num
                                self.record_result.append(user_obj)
                            self.record_result.remove(record)
                        else:
                            continue
                    update_record_info()
                    self.record_table.verticalScrollBar().setSliderPosition(
                        self.record_model.rowCount() - 1)
                elif action == tot_item:
                    # 计算分数总和
                    tot = 0
                    for model_index in record_table.selectionModel().selection().indexes():
                        row = model_index.row()
                        record = self.record_result[row]
                        if isinstance(record, UserObject):
                            tot += record.points
                        else:
                            tot += record.get_total_score()
                    QMessageBox.information(
                        self, '求和', f'当前选中分数总和为:{str(new_rounding(tot, ROUND_FACTOR))}', QMessageBox.Yes,
                        QMessageBox.Yes)
                elif action == tot_all_item:
                    tot = 0
                    for record in self.record_result:
                        if isinstance(record, UserObject):
                            tot += record.points
                        else:
                            tot += record.get_total_score()
                    QMessageBox.information(
                        self, '求和', f'当前全部分数总和为:{str(new_rounding(tot, ROUND_FACTOR))}', QMessageBox.Yes,
                        QMessageBox.Yes)

                elif action == view_item:
                    if record_table.selectionModel().selection().indexes():
                        index = record_table.selectionModel().selection().indexes()[0]
                        show_group_info(index)
                else:
                    return
            else:
                return

        # 当右键表格的时候弹出合并选项
        record_table.setContextMenuPolicy(Qt.CustomContextMenu)
        record_table.customContextMenuRequested.connect(show_merge_menu)

        # 当表格进行修改的时候
        def modify_record_info():
            self.record_model.itemChanged.disconnect(modify_record_info)
            row = record_table.currentIndex().row()
            col = record_table.currentIndex().column()
            current_record = self.record_result[row]

            # 如果是用户组
            if isinstance(current_record, UserObjectGroup):
                # 判断是否修改当前分数 或者 限制分数
                if col == 1 or col == 0:
                    pass
                elif col == 3:
                    # 修改组名
                    current_record.group_name = self.record_model.item(
                        row, col).text()
                else:
                    try:
                        self.record_model.item(row, col).setText(
                            str(current_record.points))
                    except:
                        pass
                    self.record_model.itemChanged.connect(modify_record_info)
                    return

            if col == 0:
                # 修改标号
                current_record.index = self.record_model.item(
                    row, col).text()
            elif col == 3:
                # 修改用户名
                current_record.username = self.record_model.item(
                    row, col).text()
            elif col == 2:
                # 修改用户id
                current_record.id_ = self.record_model.item(row, col).text()
            elif col == 4:
                # 修改原积分
                try:
                    current_record.origin_score = int(self.record_model.item(row, col).text())
                    # 更新现积分和转换分
                    current_record.current_score = current_record.origin_score + current_record.round_score
                    current_record.points = new_rounding(current_record.current_score * self.factor, ROUND_FACTOR)
                    self.record_model.item(
                        record_table.currentIndex().row(), 6).setText(str(current_record.current_score))
                    self.record_model.item(
                        record_table.currentIndex().row(), 7).setText(str(current_record.points))

                    if current_record.points <= current_record.point_limit:
                        self.record_model.item(
                            record_table.currentIndex().row(), 7).setBackground(Qt.yellow)
                    else:
                        self.record_model.item(
                            record_table.currentIndex().row(), 7).setBackground(Qt.white)
                    # 根据兑换分和比率算出原积分
                except:
                    self.record_model.setItem(
                        row, col, QStandardItem(str(current_record.points)))
            elif col == 1:
                # 修改当前分数极值
                try:
                    current_record.point_limit = int(
                        self.record_model.item(row, col).text())
                    if current_record.points <= current_record.point_limit:
                        self.record_model.item(
                            record_table.currentIndex().row(), 7).setBackground(Qt.yellow)
                    else:
                        self.record_model.item(
                            record_table.currentIndex().row(), 7).setBackground(Qt.white)
                except:
                    self.record_model.setItem(row, col, QStandardItem(
                        str(current_record.point_limit)))
            elif col == 5:
                # 修改本局分数
                try:
                    current_record.round_score = int(self.record_model.item(row, col).text())
                    # 更新现积分和转换分
                    current_record.current_score = current_record.origin_score + current_record.round_score
                    current_record.points = new_rounding(current_record.current_score * self.factor, ROUND_FACTOR)
                    self.record_model.item(
                        record_table.currentIndex().row(), 6).setText(str(current_record.current_score))
                    self.record_model.item(
                        record_table.currentIndex().row(), 7).setText(str(current_record.points))

                    if current_record.points <= current_record.point_limit:
                        self.record_model.item(
                            record_table.currentIndex().row(), col).setBackground(Qt.yellow)
                    else:
                        self.record_model.item(
                            record_table.currentIndex().row(), col).setBackground(Qt.white)
                    # 根据兑换分和比率算出原积分
                except:
                    self.record_model.setItem(
                        row, col, QStandardItem(str(current_record.points)))
            elif col == 6:
                try:
                    current_record.current_score = int(self.record_model.item(
                        record_table.currentIndex().row(), 6).text())
                    current_record.origin_score = 0
                    current_record.round_score = 0
                    self.record_model.setItem(row, 4, QStandardItem('0'))
                    self.record_model.setItem(row, 5, QStandardItem('0'))
                    # 更新兑换分
                    current_record.points = new_rounding(current_record.current_score * self.factor, ROUND_FACTOR)
                    self.record_model.item(
                        record_table.currentIndex().row(), 7).setText(str(current_record.points))
                except:
                    self.record_model.setItem(row, col, QStandardItem(
                        str(current_record.current_score)))
            elif col == 7:
                try:
                    current_record.points = int(self.record_model.item(
                        record_table.currentIndex().row(), 7).text())
                    current_record.origin_score = 0
                    current_record.round_score = 0
                    self.record_model.setItem(row, 4, QStandardItem('0'))
                    self.record_model.setItem(row, 5, QStandardItem('0'))
                    # 更新现积分
                    current_record.current_score = new_rounding(current_record.points / self.factor, ROUND_FACTOR)
                    self.record_model.item(
                        record_table.currentIndex().row(), 6).setText(str(current_record.current_score))
                except:
                    self.record_model.setItem(row, col, QStandardItem(
                        str(current_record.points)))
            self.record_model.itemChanged.connect(modify_record_info)

        self.record_model.itemChanged.connect(modify_record_info)

        def append_record_info(data: List[UserObject]):
            # 用户上一局的现分数就是这一局的原分数
            for record in self.record_result:
                if isinstance(record, UserObject):
                    record.round_score = 0
                    record.origin_score = record.current_score
                else:
                    for user in record.users:
                        user.round_score = 0
                        user.origin_score = user.current_score

            if self.record_result:
                for d in data:
                    already_exist = False
                    for record in self.record_result:
                        if isinstance(record, UserObject):
                            # 单一用户
                            if d.id_ == record.id_:
                                # 判断为同一个人
                                # 根据转换比率计算
                                record.round_score = new_rounding(d.points, ROUND_FACTOR)
                                if record.round_score != 0:
                                    record.round_num += 1
                                record.current_score = new_rounding(record.origin_score + record.round_score,
                                                                    ROUND_FACTOR)
                                record.points = new_rounding(self.factor * record.current_score, ROUND_FACTOR)
                                already_exist = True
                                # 挪动到最前
                                self.record_result.remove(record)
                                self.record_result.insert(0, record)
                                break
                        elif isinstance(record, UserObjectGroup):
                            # 用户组
                            for user in record.users:
                                if user.id_ == d.id_:
                                    user.round_score = new_rounding(d.points, ROUND_FACTOR)
                                    if user.round_score != 0:
                                        user.round_num += 1
                                    user.current_score = new_rounding(user.origin_score + user.round_score,
                                                                      ROUND_FACTOR)
                                    user.points = new_rounding(self.factor * user.current_score, ROUND_FACTOR)
                                    already_exist = True
                                    self.record_result.remove(record)
                                    self.record_result.insert(0, record)
                                    break
                            # 挪到前面
                            # if already_exist:
                            #     self.record_result.remove(record)
                            #     self.record_result.insert(0, record)
                    if not already_exist:
                        # 此人不存在
                        d.round_score = new_rounding(d.points, ROUND_FACTOR)
                        d.current_score = new_rounding(d.round_score, ROUND_FACTOR)
                        if d.round_score != 0:
                            d.round_num += 1
                        d.points = new_rounding(d.current_score * self.factor, ROUND_FACTOR)
                        self.record_result.insert(0, d)

            else:
                for d in data:
                    # 此人不存在
                    d.round_score = new_rounding(d.points, ROUND_FACTOR)
                    d.current_score = new_rounding(d.round_score, ROUND_FACTOR)
                    if d.round_score != 0:
                        d.round_num += 1
                    d.points = new_rounding(d.current_score * self.factor, ROUND_FACTOR)
                    self.record_result.insert(0, d)
                # self.record_result.extend(data)

            self.image_view.current_scene.clear()
            update_record_info()

        # 右侧图片选框
        right_layout = QVBoxLayout()
        right_side_lower_layout.addLayout(right_layout)
        right_side_lower_layout.setStretchFactor(right_layout, 8)

        # 右上按钮
        right_button_layout = QHBoxLayout()
        right_layout.addLayout(right_button_layout)

        self.image_view = ImageView()
        # self.image_view.setFixedWidth(460)
        right_layout.addWidget(self.image_view)

        # 导入照片
        def import_image():
            self.image_view.current_scene.clear()
            filename = QFileDialog.getOpenFileName(
                self, '选择图片', '.', '图像文件(*.jpg *.png)')[0]
            if not filename:
                return
            image = Image.open(filename)
            # 预处理图像
            # image = BaiduAPI.preprocess(image)
            if type_cb.currentIndex() == 0:
                id_count = 30
            else:
                id_count = 20
            # print('有效用户数量:' + str(id_count))
            result = self.api.template_ocr(image, id_count)
            # 选框中显示
            boxes, room_id = ResultParser.get_data_tuple_template(result)
            print("jingru")
            print(boxes, room_id)
            self.room_num_lb.setText(f'房间号：{room_id}')
            self.image_view.current_scene.set_boxes(boxes)
            self.image_view.current_scene.set_image(image)
            self.image_view.current_scene.update_image()

            # 解析结果数据
            result = ResultParser.parse_template(result, id_count)

            print(result)
            # 将数据加载到当前表格
            self.current_result = result
            update_current_info()

        type_cb = QComboBox()
        type_cb.addItems(['双列', '单列'])
        type_cb.setEditable(False)
        right_button_layout.addWidget(type_cb)

        import_bt = QPushButton('导入图片')
        import_bt.clicked.connect(import_image)
        right_button_layout.addWidget(import_bt)

        # 确认数据
        def confirm_info():
            # 重新封装修改之后的数据
            new_info = []
            score = 0
            for i in range(self.current_model.rowCount()):
                username = self.current_model.item(i, 0).text()
                user_id = self.current_model.item(i, 1).text()
                try:
                    round_score = float(self.current_model.item(i, 2).text())
                    score += round_score
                    print(score, ':', round_score)
                except:
                    round_score = 0
                obj = UserObject(username, user_id, round_score)
                obj.origin_score = 0
                obj.round_score = 0
                obj.current_score = 0
                new_info.append(obj)
            # 自动规整数据， 将数据存入全局
            append_record_info(new_info)
            print('score:', score)
            self.append_score_stat(score)

            # 删除当前数据表格中的显示
            self.current_result = []
            update_current_info()

        right_down_bt_layout = QHBoxLayout()
        right_layout.addLayout(right_down_bt_layout)

        # 确认当前数据正确
        store_bt = QPushButton('确认数据')
        store_bt.clicked.connect(confirm_info)
        right_down_bt_layout.addWidget(store_bt)

        def add_current():
            self.current_result.insert(0, UserObject('玩家', '', 0))
            update_current_info()

        center_botton_bt_layout = QHBoxLayout()
        center_layout.addLayout(center_botton_bt_layout)
        # 新增数据
        add_current_button = QPushButton('新增数据')
        add_current_button.clicked.connect(add_current)
        center_botton_bt_layout.addWidget(add_current_button)

        # 清空分数
        def clear_score():
            for record in self.record_result:
                if isinstance(record, UserObject):
                    record.points = 0
                    record.current_score = 0
                    record.round_score = 0
                    record.origin_score = 0
                    record.round_num = 0
                else:
                    for user in record.users:
                        user.points = 0
                        user.current_score = 0
                        user.round_score = 0
                        user.origin_score = 0
                        user.round_num = 0

            for _ in range(self.stat_model.rowCount()):
                self.stat_model.removeRow(0)

            self.score_stats.clear()

            update_record_info()
            self.update_index_group()

        record_filter_e.textChanged.connect(self.filter_record)
        # 清空分数按钮
        clear_score_button = QPushButton('清空中间历史')
        clear_score_button.clicked.connect(clear_score)
        # left_button_layout.addWidget(clear_score_button, 5)

        # 保存数据按钮
        left_botton_bt_layout = QHBoxLayout()
        left_layout.addLayout(left_botton_bt_layout)
        dump_data_button = QPushButton('保存数据')
        dump_data_button.clicked.connect(self.store_data)
        left_botton_bt_layout.addWidget(dump_data_button)

        # 读取保存数据按钮
        read_data_button = QPushButton('读取数据')
        read_data_button.clicked.connect(self.read_data)
        # left_button_layout.addWidget(read_data_button, 5)

        # 将两个表格也修改为全局变量
        self.current_table = current_table
        self.record_table = record_table

        # 类型选框
        self.type_cb = type_cb

        top_menu_layout.addWidget(bt_setting)
        top_menu_layout.addWidget(bt_clear)
        top_menu_layout.addWidget(bt_data)

        # 上部菜单栏
        # reduce_factor_action = QAction('&设置相减比率', self.menu_bar)
        # setting_menu = self.menu_bar.addMenu('&设置')
        #
        # setting_menu.addAction(reduce_factor_action)
        # reduce_factor_action.triggered.connect(self.edit_reduce_factor)

        # 分数求和菜单
        def stat_tot_menu(pos):
            menu = QMenu()

            calc_tot_action = QAction('求总和')
            menu.addAction(calc_tot_action)
            action = menu.exec_(QPoint(score_table.x() + score_table.width(), score_table.mapToGlobal(pos).y()))

            if action == calc_tot_action:
                score = 0
                for s in self.score_stats:
                    score += float(s)
                QMessageBox.information(self, '提示', '分数总和为: ' + str(score))

        score_table.setContextMenuPolicy(Qt.CustomContextMenu)
        score_table.customContextMenuRequested.connect(stat_tot_menu)

        self.update_record_info = update_record_info

        # 清空菜单栏
        clear_menu = QMenu()
        action_clear_left = QAction('清空左侧统计', clear_menu)
        action_clear_left.triggered.connect(self.clear_score_stat)
        clear_menu.addAction(action_clear_left)

        action_clear_center = QAction('清空中间分数', clear_menu)
        action_clear_center.triggered.connect(clear_score)
        clear_menu.addAction(action_clear_center)
        bt_clear.setMenu(clear_menu)

        action_clear_right = QAction('清空右侧新增', clear_menu)
        action_clear_right.triggered.connect(clear_data)
        clear_menu.addAction(action_clear_right)
        bt_clear.setMenu(clear_menu)

    # 读取数据
    def read_data(self):
        _ = ScoreOperator.read_data()
        if _:
            # 判断是否为旧版本
            for sample in _:
                if isinstance(sample, UserObject) and sample.origin_score is None:
                    # 旧版
                    QMessageBox.information(self, '提示', '导入的数据为旧版数据，将只保留用户数据', QMessageBox.Yes,
                                            QMessageBox.Yes)
                    for obj in _:
                        if isinstance(obj, UserObject):
                            obj.round_score = 0
                            obj.origin_score = 0
                            obj.points = 0
                            obj.current_score = 0
                        elif isinstance(obj, UserObjectGroup):
                            for user in obj.users:
                                user.round_score = 0
                                user.origin_score = 0
                                user.points = 0
                                user.current_score = 0
                    break
            # 新版直接导入
            self.record_result = _

        self.update_record_info()

        if os.path.exists('index_groups.pkl'):
            self.index_groups = ScoreOperator.read_data('index_groups.pkl')
            for g in self.index_groups:
                if not hasattr(g, 'limit2'):
                    g.limit2 = -1
                    # 因为是旧版本导入 所以只保留用户基本信息
                    for obj in g.data_list:
                        if isinstance(obj, UserObject):
                            obj.round_score = 0
                            obj.origin_score = 0
                            obj.points = 0
                            obj.current_score = 0
                        elif isinstance(obj, UserObjectGroup):
                            for user in obj.users:
                                user.round_score = 0
                                user.origin_score = 0
                                user.points = 0
                                user.current_score = 0
            self.update_index_group()

        if os.path.exists('score_stats.pkl'):
            self.score_stats = ScoreOperator.read_data('score_stats.pkl')
            for index in range(len(self.score_stats)):
                self.score_stats[index] = new_rounding(self.score_stats[index], ROUND_FACTOR)

            for _ in range(self.stat_model.rowCount()):
                self.stat_model.removeRow(0)
            for score in self.score_stats:
                self.stat_model.appendRow((QStandardItem(str(score)),))

    # 按键点击事件
    def keyPressEvent(self, evt):
        super().keyPressEvent(evt)
        # 按下删除键
        if evt.key() == Qt.Key_Delete:
            record_index = self.record_table.currentIndex().row()
            if record_index > 0:
                self.record_result.remove(self.record_result[record_index])
                self.record_model.removeRow(record_index)

            current_index = self.current_table.currentIndex().row()
            if current_index > 0:
                self.current_model.removeRow(current_index)
                self.current_result.remove(self.current_result[current_index])

    # 保存数据
    def store_data(self):
        try:
            ScoreOperator.dump_data(self.record_result)
            ScoreOperator.dump_data(self.index_groups, 'index_groups.pkl')
            ScoreOperator.dump_data(self.score_stats, 'score_stats.pkl')
            QMessageBox.information(
                self, '提示', '保存成功', QMessageBox.Yes, QMessageBox.Yes)
        except Exception as e:
            print(e)
            QMessageBox.warning(self, '警告', '保存失败',
                                QMessageBox.Yes, QMessageBox.Yes)

    # 修改相减数据
    def edit_reduce_factor(self):
        reduce_factor = self.reduce_factor

        if os.path.exists('reduce_factor'):
            with open('reduce_factor', 'r') as f:
                reduce_factor = int(f.readline())
        reduce_factor = QInputDialog.getInt(self, '设置相减系数', '相减系数', reduce_factor, 0, 9999999, 1)[0]
        with open('reduce_factor', 'w') as f:
            f.write(str(reduce_factor))
        self.reduce_factor = reduce_factor

    # 拖入事件
    def dragEnterEvent(self, evt):
        file_path = evt.mimeData().urls()[0].toLocalFile()
        if file_path.endswith('.jpg') or file_path.endswith('.png'):
            evt.accept()
        else:
            evt.ignore()

    # 拖入释放事件
    def dropEvent(self, evt):
        filename = evt.mimeData().urls()[0].toLocalFile()
        self.image_view.current_scene.clear()
        if not filename:
            return
        image = Image.open(filename)
        # 预处理图像
        # image = BaiduAPI.preprocess(image)
        # result = self.api.image_ocr(image)

        # id_count = self.api.get_user_count(image)
        if self.type_cb.currentIndex() == 0:
            id_count = 30
        else:
            id_count = 20
        # print('有效用户数量:' + str(id_count))
        result = self.api.template_ocr(image, id_count)

        # 选框中显示
        print("进入")
        boxes, room_id = ResultParser.get_data_tuple_template(result)
        print("退出")
        self.room_num_lb.setText(f'房间号：{room_id}')

        print("进入1")
        self.image_view.current_scene.set_boxes(boxes)

        print("进入2")
        self.image_view.current_scene.set_image(image)

        print("进入3")
        self.image_view.current_scene.update_image()

        print("进入4")
        # 解析结果数据
        result = ResultParser.parse_template(result, id_count)

        print("进入5")
        # 将数据加载到当前表格
        self.current_result = result
        self.update_current_info()
        print("进入6")

    # 更新当前信息
    def update_current_info(self):
        # 清空原始数据
        for _ in range(self.current_model.rowCount()):
            self.current_model.removeRow(0)

        count = 0
        for result in self.current_result:
            is_colored = False
            # 如果score为None 则为识别可能出现错误
            if result.points is None:
                result.points = 0
                is_colored = True
            self.current_model.appendRow((QStandardItem(result.username), QStandardItem(
                result.id_), QStandardItem(str(result.points))))
            if is_colored:
                self.current_model.item(self.current_result.index(
                    result), 2).setBackground(Qt.red)

            if len(result.id_) != 8:
                self.current_model.item(self.current_result.index(
                    result), 1).setBackground(Qt.red)

            # 设置高度
            self.current_table.setRowHeight(count, 4)
            count += 1

    # 展示标签组
    def show_index_group(self, index: int):
        group = self.index_groups[index]
        view = IndexGroupView(group, self.record_result)
        view.exec_()
        self.index_groups[index] = view.get_data()
        self.update_index_group()

    # 更新标签分组显示
    def update_index_group(self):
        for i in range(len(self.index_groups)):
            # 如果没有设置标签，则跳过
            if not self.index_groups[i].index:
                continue

            # 重新更新分数
            self.index_groups[i].data_list.clear()
            for obj in self.record_result:
                if obj.index and obj.index[0] == self.index_groups[i].index[0]:
                    self.index_groups[i].data_list.append(obj)
                # self.index_groups[i].data_list = sorted(self.index_groups[i].data_list, key=lambda x: x.points,
                #                                         reverse=True)
                self.index_groups[i].data_list = IndexGroupView.sort(self.index_groups[i].data_list)

            score = 0
            for obj in self.index_groups[i].data_list:
                if isinstance(obj, UserObject):
                    score += obj.points
                elif isinstance(obj, UserObjectGroup):
                    score += obj.get_total_score()
            if hasattr(self.index_groups[i], 'limit2'):
                if self.index_groups[i].limit2 < score <= self.index_groups[i].limit:
                    self.group_bts[i].setStyleSheet('background-color: yellow')
                elif score <= self.index_groups[i].limit2:
                    self.group_bts[i].setStyleSheet('background-color: red;')
                else:
                    self.group_bts[i].setStyleSheet('background-color: white;')
            else:
                self.index_groups[i].limit2 = -1
                if score <= self.index_groups[i].limit:
                    self.group_bts[i].setStyleSheet('background-color: yellow;')
                else:
                    self.group_bts[i].setStyleSheet('background-color: white;')
            self.group_bts[i].setText(self.index_groups[i].index)

    # 更新分数统计信息
    def append_score_stat(self, score: float):
        score = new_rounding(score * self.factor, ROUND_FACTOR)
        self.stat_model.insertRow(0, [QStandardItem(str(score))])
        self.score_stats.insert(0, score)

    # 清空分数
    def clear_score_stat(self):
        for _ in range(self.stat_model.rowCount()):
            self.stat_model.removeRow(0)

        self.score_stats.clear()

    # 筛选条件
    def filter_record(self, condition: str):
        if condition:
            filtered_list = []
            if self.is_first_time_flag:
                self.record_result_bk = copy(self.record_result)
                self.is_first_time_flag = False
            for obj in self.record_result:
                if isinstance(obj, UserObject):
                    if condition in obj.username:
                        filtered_list.append(obj)
                elif isinstance(obj, UserObjectGroup):
                    if condition in obj.group_name:
                        filtered_list.append(obj)

            # 显示到列表
            self.record_result = filtered_list
            self.update_record_info()
        else:
            if not self.is_first_time_flag:
                # 更新数据
                # for obj in self.record_result:
                #     index = self.record_result.index(obj)
                #     mapped_index = self.record_result_bk_index[index]
                #     print(mapped_index)
                #     self.record_result_bk[mapped_index] = obj
                self.record_result = self.record_result_bk
                self.record_result_bk_index.clear()

            self.update_record_info()


# 当前数据 表格项目
class CurrentTableItem(QStandardItem):
    def __init__(self):
        super().__init__()
        self.setFont(QFont('宋体', 4, QFont.Black))

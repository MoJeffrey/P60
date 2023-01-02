# _*_ coding: utf-8 _*_
# @Time : 2022/5/22 12:03
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : models.py
# @desc : 数据模型类

"""
记录类
"""

from datetime import datetime
from typing import List


class UserObject:
    # 用户名称
    username = ''
    # 兑换分
    points = 0
    # 分数提醒线
    point_limit = -1
    # 用户id
    id_ = ''
    # 编码
    index = ''
    # 原积分
    origin_score = None
    # 本局积分
    round_score = None
    # 现积分
    current_score = None

    # 记录轮数
    round_num = 0

    def __init__(self, username: str, id_: str, points: float, point_limit: int = -1):
        self.username = username
        self.points = points
        self.id_ = id_
        self.point_limit = point_limit

    def add_point(self, delta: float):
        """
        添加分数
        :param delta: 增量
        :return: 
        """
        self.points += delta

    def __str__(self):
        return f'|username: {self.username} id: {self.id_}, score: {self.points}|'

    def __repr__(self):
        return f'|username: {self.username} id: {self.id_}, score: {self.points}|'

    def __eq__(self, other):
        if type(other) == type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def get_total_score(self):
        """
        获取总分
        """
        return self.points


"""
用户数据组
"""


class UserObjectGroup:
    # 组名
    group_name = ''

    # 组内用户
    users = []

    # 组分数
    points = 0

    # 组分数限制
    points_limit = -1

    # 组内编码
    index = ''

    def __init__(self, group_name: str, users: List[UserObject], points: float, point_limit: int = -1):
        self.group_name = group_name
        self.users = users
        self.points = points
        self.point_limit = point_limit

    def add_point(self, delta: float):
        """
        添加分数
        :param delta: 增量
        :return: 
        """
        self.points += delta

    def __str__(self):
        return f'<groupname: {self.group_name} users:{self.users}, score: {self.points}>'

    def __repr__(self):
        return f'<groupname: {self.group_name} users:{self.users}, score: {self.points}>'

    def __eq__(self, other):
        if type(other) == type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def get_display_username(self):
        """
        获取显示的用户名
        :return: 显示的用户名
        """
        username_list = []
        for user in self.users:
            username_list.append(user.username)
        return str(username_list).replace('[', '<').replace(']', '>').replace("'", '')

    def get_display_id(self):
        """
        获取显示的id
        :return: 显示的id
        """
        id_list = []
        for user in self.users:
            id_list.append(user.id_)
        return str(id_list).replace('[', '').replace(']', '').replace("'", '')
        # return str(id_list)

    def get_total_score(self):
        """
        获取总分
        """
        tot = 0

        for user in self.users:
            tot += user.points
        self.points = tot
        return int(tot)

    def get_total_current(self):
        """
        获取当前分数
        :return: 当前分数
        """
        tot = 0
        for user in self.users:
            tot += user.current_score
        return int(tot)

    def get_total_origin(self):
        """
        获取当前原始分数
        :return:
        """
        tot = 0
        for user in self.users:
            tot += user.origin_score
        return int(tot)

    def get_total_round(self):
        """
        获取全部当局分数
        :return:
        """
        tot = 0
        for user in self.users:
            tot += user.round_score
        return int(tot)

    def get_total_roundnum(self):
        """
        获取全部局数
        :return:
        """
        tot = 0
        for user in self.users:
            tot += user.round_num
        return int(tot)


"""
数据分页
"""


class DataSheet:
    def __init__(self, data_list: List):
        # 数据对象
        self.data_list = data_list

        # 当前日期
        self.time = datetime.now()

    # 更新数据
    def update_datalist(self, data_list: List):
        self.data_list = data_list


class IndexGroup:
    def __init__(self, data_list: List = [], index: str = '', limit: int = -1, limit2: int = -1):
        # 数据对象
        self.data_list = data_list

        # 标签
        self.index = index

        # 分数限制
        self.limit = limit

        # 分数限制2
        self.limit2 = limit2

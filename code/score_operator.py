# _*_ coding: utf-8 _*_
# @Time : 2022/5/30 19:16
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : score_operator.py
# @desc : 分数记录器

from models import UserObjectGroup, UserObject
import os
from typing import List
import pickle


class ScoreOperator:

    # 从保存的文件中读取分数信息
    @staticmethod
    def read_data(file_path='data.pkl'):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            return None

    # 保存分数信息
    @staticmethod
    def dump_data(data: List[UserObject or UserObjectGroup], file_path='data.pkl'):
        if data or file_path == 'score_stats.pkl':
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)

# _*_ coding: utf-8 _*_
# @Time : 2022/5/21 19:21
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : digit_api.py
# @desc : 百度api对接 识别数字
import base64
import enum
import io
import re
from typing import List, Tuple

import requests
from PIL import Image

import math

from models import UserObject

import config_operator

# 缩放比例
SCALE = 1.7


"""
BAIDU API caller module class.
"""


class BaiduAPI:
    def __init__(self, client_id, client_secret, token=None):
        """
        初始化api调用
        :param token: 可以传入token也可以从get_token函数进行获取
        :param client_id: api key
        :param client_secret: Secret Key
        """
        # 百度accessToken
        self.token = token
        # API Key
        self.client_id = client_id
        # secret
        self.client_secret = client_secret

    def get_token(self):
        """
        通过接口获取百度access token
        :return: token
        """
        host = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.client_id}&client_secret={self.client_secret}'
        response = requests.get(host)
        if response:
            self.token = response.json()['access_token']
            print(self.token)
            if self.token:
                # 存储token
                config_operator.store_token(self.token)
            return self.token

    @staticmethod
    def preprocess(img: Image):
        """
        预处理图片
        :param img: 图片PIL.Image类型
        :return: 处理完成的图片
        """
        # 边缘裁剪
        img = img.crop((100 * SCALE, 0, img.size[0], img.size[1] - 400))
        if SCALE != 1:
            img = img.resize(
                (int(img.size[0] * SCALE), int(img.size[1] * SCALE)))
        # img = img.convert('L')
        return img

    def image_ocr(self, img: Image):
        """
        上传图片并且获取信息
        :param img: 图片PIL.Image类型
        :return: 接口返回的Json数据
        """
        if not self.token:
            import os
            if os.path.exists('token.conf'):
                self.token = config_operator.get_token()
            else:
                self.get_token()
        request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general"
        # 将 PIL 格式转换为二进制
        byte_stream = io.BytesIO()
        img.save(byte_stream, format='PNG')
        img = base64.b64encode(byte_stream.getvalue())

        params = {"image": img}
        access_token = self.token
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        if response:
            # 接口是否报错
            if 'error_code' in response.json():
                print(response.json().get('error_msg', ''))
                raise APIError(response.json().get('error_msg', ''))
            print(response.json())
            return response.json()
        return None

    def get_user_count(self, img: Image):
        """
        获取用户数量
        :param img: 图片
        :return: 接口返回的用户数量
        """
        img = img.resize((int(img.size[0] * SCALE), int(img.size[1] * SCALE)))
        json_dict = self.image_ocr(img)
        if json_dict:

            # 封装成标准数据格式
            data_list: List[DataTuple] = []
            root = json_dict['words_result']
            for data in root:
                _ = DataTuple(data)
                _.get_type()
                data_list.append(_)

            # 根据id的值进行判断是单列还是双列
            # id_count = 0
            # for data in data_list:
            #     if data.word_type == WordTypeEnum.ID:
            #         id_count += 1
            return math.ceil((len(data_list) - 5) / 3)
        else:
            raise APIError('获取信息为空')

    def template_ocr(self, img: Image, id_count: int):
        """
        上传图片并且根据模板获取信息
        :param img: 图片PIL.Image类型
        :return: 接口返回的Json数据
        """
        if not self.token:
            import os
            if os.path.exists('token.conf'):
                self.token = config_operator.get_token()
            else:
                self.get_token()
        request_url = "https://aip.baidubce.com/rest/2.0/solution/v1/iocr/recognise"
        # 将 PIL 格式转换为二进制
        byte_stream = io.BytesIO()
        img.save(byte_stream, format='PNG')
        img = base64.b64encode(byte_stream.getvalue())

        if 10 < id_count < 21:
            # 单列
            params = {"image": img, "templateSign": '0d46e8a97d831ed93aab22532f30013a'}
        else:
            # 双列
            params = {"image": img, "templateSign": '309ea7c6e816ca2622d8b660f540832d'}

        # 构建数据
        access_token = self.token
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        if response:
            # 接口是否报错
            print(response.json())
            return response.json()
        return None


"""
文字类型枚举类
"""


class WordTypeEnum(enum.Enum):
    # 分数
    SCORE = 0
    # 用户id
    ID = 1
    # 其他无用信息
    OTHER = 2


"""
接口错误类
"""


class APIError(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg

    def __repr__(self):
        return f'API接口错误{self.msg}'


"""
数据元组
"""


class DataTuple:

    def __init__(self, json_dict=None, word=None, x=None, y=None, width=None, height=None):
        if json_dict:
            self.word = json_dict['words']
            self.x = json_dict['location']['left']
            self.y = json_dict['location']['top']
            self.width = json_dict['location']['width']
            self.height = json_dict['location']['height']
        else:
            self.word = word
            self.x = x
            self.y = y
            self.width = width
            self.height = height

        # 字符可能表示含义
        self.word_type = None

    def __str__(self) -> str:
        return f'|{self.word}|'

    def __repr__(self) -> str:
        return f'|{self.word}|'

    def get_type(self):
        """
        识别字符对应的类别
        :return: 类别
        """
        ID_PATTERN = '^[1D|lD|ID|iD|D|31D]+:[0-9]+'
        ID_PATTERN2 = '^[D]+[0-9]+'
        SCORE_PATTERN = '^[+|-][0-9]+$'
        self.word = self.word.replace(".", ":")
        _ = self.word[1:]
        if re.match(ID_PATTERN, _) or re.match(ID_PATTERN2, _) or re.match(ID_PATTERN, self.word) or re.match(ID_PATTERN2, self.word):
            self.word_type = WordTypeEnum.ID
        elif re.match(SCORE_PATTERN, self.word):
            self.word_type = WordTypeEnum.SCORE
        # elif self.word.replace('D.', '').isalnum():
        #     self.word_type = WordTypeEnum.ID
        elif len(self.word) - 11 >= 0:
            _ = self.word[len(self.word) - 11:]
            print('*****' + _)
            if re.match(ID_PATTERN, _) or re.match(ID_PATTERN2, _):
                self.word_type = WordTypeEnum.ID
            else:
                self.word_type = WordTypeEnum.OTHER
        else:
            self.word_type = WordTypeEnum.OTHER


"""
结果解析
"""


class ResultParser:
    def __init__(self):
        pass

    @staticmethod
    def _is_closed(data_tuple1: DataTuple, data_tuple2: DataTuple, threshold: Tuple):
        """
        判断两个数据元组是否接近
        :param data_tuple1: 第一个数据
        :param data_tuple2: 第二个数据
        :param threshold: 阈值(x轴阈值, y轴阈值)
        :return 是否临近
        """
        threshold = (threshold[0] * SCALE + 20, threshold[1] * SCALE + 20)
        if abs(data_tuple1.x - data_tuple2.x) <= threshold[0] and abs(data_tuple1.y - data_tuple2.y) <= threshold[1]:
            return True

        return False

    @staticmethod
    def _search_name_by_id(id_data: DataTuple, data: List[DataTuple]):
        """
        根据id数据信息寻找对应的人名
        :param id_data: id数据信息
        :param data: 其他数据信息
        :return: 返回解析好的数据对象 返回None
        """
        for d in data:
            # 为其他类型才进行判断
            if d.word_type == WordTypeEnum.OTHER:
                # 位于id坐标上方
                if d.y < id_data.y:
                    pass
                else:
                    continue
                # 是否在搜索范围内
                if ResultParser._is_closed(id_data, d, (50, 50)):
                    return d

    @staticmethod
    def _search_score_by_id(id_data: DataTuple, data: List[DataTuple], xd=220, yd=20):
        """
        根据id数据寻找对应分数数据
        :param id_data: id数据信息
        :param data: 其他数据信息
        :return: 返回找到的DataTuple
        """
        for d in data:
            # 遍历所有数据进行检索
            # 判断正则过滤是否通过
            if d.word_type == WordTypeEnum.SCORE:
                # 首先判断分数位置是否在id位置的右侧
                if id_data.x < d.x:
                    pass
                else:
                    continue
                # 是否在搜索范围内
                if ResultParser._is_closed(id_data, d, (xd, yd)):
                    return d
            else:
                continue

    @staticmethod
    def _chop_id(id_str: str):
        """
        切割字符串
        :param id_str: 带切割id字符串
        :return 切割完成的字符串
        """
        try:
            result = id_str[id_str.index(':') + 1:].replace(' ', '')
        except:
            result = ''.join(list(filter(str.isdigit, id_str)))
        return result

    @staticmethod
    def parse(json_dict):
        """
        解析json数据
        :param json_dict: json字典数据
        :return: 返回解析好的数据对象
        """
        # 封装成标准数据格式
        data_list: List[DataTuple] = []
        root = json_dict['words_result']
        for data in root:
            _ = DataTuple(data)
            _.get_type()
            data_list.append(_)

        # 根据id的值进行判断是单列还是双列
        id_count = 0
        for data in data_list:
            if data.word_type == WordTypeEnum.ID:
                id_count += 1

        # 单列
        dx = 220
        dy = 20
        if 10 < id_count <= 20:
            dx = 460
            dy = 30
        else:
            # 双列直接跳过
            pass

        # 首先获取ID的word result
        id_list: List[DataTuple] = []

        # 对data_list进行双键排序
        print('*' * 30)
        print(data_list)
        data_list = sorted(data_list, key=lambda item: (
            item.y, item.x), reverse=False)

        # 封装成的userObj对象
        user_object_list = []
        for data in data_list:
            # 如果是word result 进行获取
            if data.word_type == WordTypeEnum.ID:
                id_list.append(data)
                username = ResultParser._search_name_by_id(data, data_list)
                score = ResultParser._search_score_by_id(
                    data, data_list, dx, dy)
                # 防止空值
                username = username if username else DataTuple(word='')
                score = score if score else DataTuple(word=None)

                user_obj = UserObject(
                    username.word, ResultParser._chop_id(data.word), score.word)
                user_object_list.append(user_obj)
            else:
                continue

        return user_object_list

    @staticmethod
    def get_data_tuple(json_dict):
        """
        根据json数据获取data tuple
        :param json_dict: json字典数据
        :return: 返回解析好的数据对象
        """
        root = json_dict['words_result']
        data_list = []
        for data in root:
            data_list.append(DataTuple(data))
        return data_list

    @staticmethod
    def get_data_tuple_template(json_dict):
        """
        根据模板识别json数据获取data tuple
        :param json_dict: json字典数据
        :return: 返回解析好的数据对象
        """
        root = json_dict['data']['ret']
        data_list = []
        room_id = None
        for data in root:
            data_list.append(DataTuple(word=data['word'], x=data['location']['left'], y=data['location']
                             ['top'], width=data['location']['width'], height=data['location']['height']))
            if data['word_name'] == 'room_id':
                room_id = data['word']
        return data_list, room_id

    @staticmethod
    def parse_template(json_dict, user_counts):
        """
        解析模板识别生成的json数据
        :param json_dict: json数据生成
        :param user_counts: 用户数量
        :return: UserObjects
        """

        if user_counts > 20:
            user_counts = 30
        else:
            user_counts = 20

        # user_counts = 30

        root = json_dict['data']['ret']
        user_list = []
        for count in range(1, user_counts + 1, 1):
            is_break = False
            current_userobj = UserObject('', None, 0)
            # 遍历数组 寻找对应信息
            id_str = 'id' + str(count)
            username_str = 'username' + str(count)
            score_str = 'score' + str(count)
            for data in root:
                word = data['word']
                word_name = data['word_name']
                if word_name == id_str:
                    if word:
                        current_userobj.id_ = ResultParser._chop_id(word)
                    else:
                        is_break = True
                        break
                elif word_name == username_str:
                    current_userobj.username = word
                elif word_name == score_str:
                    try:
                        current_userobj.points = int(word)
                    except:
                        # 标记为错误
                        current_userobj.points = None
                # else:
                #     is_break = True
            if not is_break:
                user_list.append(current_userobj)
        return user_list


# 测试方法
if __name__ == '__main__':
    # api_key = 'WK1OMGhyqSWMOfDxKabUHeXY'
    # secret_key = 'TMFD2gPgzAgsOx4zAvQFNr5XsiUmL1Gn'
    # token = '24.fbdbb75cbb591db7bb80541acc63d72c.2592000.1655742299.282335-26286905'
    # api = BaiduAPI(api_key, secret_key, token)
    # image = Image.open('test.jpg')
    # api.image_ocr(image)
    import json
    with open('sample.json', 'r', encoding='utf-8') as sample_json:
        result = ResultParser.parse(json.load(sample_json))
        print(result)
        print(len(result))

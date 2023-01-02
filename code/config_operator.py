# _*_ coding: utf-8 _*_
# @Time : 2022/5/22 0:16
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : config_operator.py
# @desc : 配置文件操作

import configparser
import os

# 配置文件位置
CONFIG_PATH = 'config.conf'


def store_api_info(client_id: str, client_secret: str):
    """
    存储token值
    :param client_id: 客户端id
    :param client_secret: 客户端密钥
    :return:
    """
    parser = configparser.ConfigParser()
    # baidu_api section
    parser.add_section('baidu_api')
    parser.set('baidu_api', 'client_id', client_id)
    parser.set('baidu_api', 'client_secret', client_secret)
    with open(CONFIG_PATH, 'w') as f:
        parser.write(f)


def read_api_info():
    """
    读取配置信息
    :return: (client_id, client_secret)
    """
    if os.path.exists(CONFIG_PATH):
        parser = configparser.ConfigParser()
        parser.read(CONFIG_PATH)
        return parser.get('baidu_api', 'client_id'), parser.get('baidu_api', 'client_secret')
    else:
        return None, None


def store_token(token: str):
    """
    存数获取到的token
    :return:
    """
    with open('token.conf', 'w') as f:
        f.write(token)


def get_token():
    """
    从文件中读取储存的token
    :return:
    """
    token = None
    if os.path.exists('token.conf'):
        with open('token.conf', 'r') as f:
            token = f.read()
    return token

if __name__ == '__main__':
    store_api_info('WK1OMGhyqSWMOfDxKabUHeXY', 'TMFD2gPgzAgsOx4zAvQFNr5XsiUmL1Gn')

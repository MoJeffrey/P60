from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

import os
import sys

from datetime import datetime

import uuid

import random

# 加密秘钥
IV = '!@sa#$*()Tk%^&'

KEY = 'username is password'


# 获取本机mac地址
def get_mac():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


# 如果text不足16位的倍数就用空格补足为16位的倍数
def add_to_16(text):
    if len(text.encode('utf-8')) % 16:
        add = 16 - (len(text.encode('utf-8')) % 16)
    else:
        add = 0
    text = text + ('\0' * add)
    return text.encode('utf-8')


# 加密函数
def encrypt(text):
    key = add_to_16(KEY)
    mode = AES.MODE_CBC
    iv = add_to_16(IV)
    text = add_to_16(text)
    cryptos = AES.new(key, mode, iv)
    cipher_text = cryptos.encrypt(text)
    # 因为AES加密后的字符串不一定是ascii字符集的，输出保存可能存在问题，所以这里转为16进制字符串
    return str(b2a_hex(cipher_text), 'utf-8')


# 解密后，去掉补足的空格用strip() 去掉
def decrypt(text):
    key = add_to_16(get_mac())
    iv = add_to_16(IV)
    mode = AES.MODE_CBC
    cryptos = AES.new(key, mode, iv)
    plain_text = cryptos.decrypt(a2b_hex(text))
    return bytes.decode(plain_text).rstrip('\0')


# 设备是否被信任
def is_device_trusted():
    if os.path.exists(os.path.dirname(os.path.realpath(sys.argv[0])) + '/device_secret.dat'):
        with open(os.path.dirname(os.path.realpath(sys.argv[0])) + '/device_secret.dat', 'r') as f:
            text = f.readline()
            if encrypt(get_mac()) == text:
                return True, '验证通过'
            else:
                return False, '密钥错误'
    else:
        return False, '未找到认证文件'


# 保存证书
def write_certificate():
    secret = encrypt(get_mac())
    with open(os.path.dirname(os.path.realpath(sys.argv[0])) + '/device_secret.dat', 'w+') as f:
        f.writelines(secret)


# 验证输入的验证码是否正确
def check(string):
    text = decrypt(string)
    time = datetime.strptime(text[:text.find('.')], '%Y-%m-%d %H:%M:%S')
    if (datetime.now() - time).seconds / 3600 <= 48:
        write_certificate()
        return True
    else:
        return False


# 生成验证码
def generate_verification_code():
    time_str = str(datetime.now())
    return encrypt('.' + time_str)

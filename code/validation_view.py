# 首次进入程序验证是否有权限
# PYQT5 编写

from typing import Callable
import validation
from PyQt5.QtWidgets import QWidget, QPushButton, QTextEdit, QMessageBox, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel

# 验证窗口
class ValidationView(QWidget):
    # 初始化对象
    def __init__(self, success_func: Callable):
        super().__init__()
        self.success_func = success_func
        self.init_widgets()
        self.update_data()

    # 初始化组件
    def init_widgets(self):
        self.setWindowTitle('注册')
        self.setMaximumSize(400, 400)
        self.setMinimumSize(400, 400)

        # 主要布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 文本域布局
        text_layout = QVBoxLayout()
        main_layout.addLayout(text_layout)

        # 文本域
        text_area = QTextEdit()
        main_layout.addWidget(text_area)

        code_layout = QHBoxLayout()
        main_layout.addLayout(code_layout)

        # 按钮布局
        bt_layout = QHBoxLayout()
        main_layout.addLayout(bt_layout)

        confirm_bt = QPushButton('确定')
        confirm_bt.clicked.connect(self.confirm)
        bt_layout.addWidget(confirm_bt)

        cancel_bt = QPushButton('取消')
        cancel_bt.clicked.connect(ValidationView.cancel)
        bt_layout.addWidget(cancel_bt)

        # 提示输入密码
        ignored_l = QLabel('验证码:')
        code_layout.addWidget(ignored_l)
        # 验证框
        code_e = QLineEdit()
        code_layout.addWidget(code_e)

        self.text_area = text_area
        self.code_e = code_e


    # 确认
    def confirm(self):
        if (self.code_e.text() == validation.encrypt(validation.get_mac())):
            QMessageBox.information(self, '提示', '验证通过', QMessageBox.Yes, QMessageBox.Yes)
            validation.write_certificate()
            # 调用验证成功的方法
            self.success_func()
        else:
            QMessageBox.information(self, '提示', '验证失败', QMessageBox.Yes, QMessageBox.Yes)

    # 取消
    @staticmethod
    def cancel():
        # 直接退出程序
        exit(0)

    # 更新界面显示
    def update_data(self):
        # 清空
        self.text_area.clear()

        """
        加密算法：
        key为本机mac地址 全球唯一
        content为当前时间
        """
        self.text_area.append('请复制以下代码，发送给管理员之后获取验证码:\n')
        self.text_area.append(validation.get_mac())


        





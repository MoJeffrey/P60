# _*_ coding: utf-8 _*_
# @Time : 2022/5/27 20:47
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : main.py
# @desc : 程序入口
import datetime
import sys

from PyQt5.QtWidgets import QApplication

from main_view import MainView

from validation_view import ValidationView

import validation

# 程序主入口
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainView()
    if validation.is_device_trusted()[0]:
        main_win.show()
    else:
        v_win = ValidationView(main_win.show)
        v_win.show()
    sys.exit(app.exec_())

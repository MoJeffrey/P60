# 注册机

from PyQt5.QtWidgets import QWidget, QPushButton, QFormLayout, QMessageBox, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel
import pyperclip
import validation


import sys

from PyQt5.QtWidgets import QApplication

from main_view import MainView


class CodeGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.init_widgets()

    # 初始化组件
    def init_widgets(self):
        self.setWindowTitle('注册机')
        self.setMaximumSize(500, 150)
        self.setMinimumSize(500, 150)

        # 主要布局
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 表单布局
        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        # 信息码
        code_e = QLineEdit()
        code_e.textChanged.connect(self.update_code)
        code_lb = QLabel('信息码')
        form_layout.addRow(code_lb, code_e)

        result_e = QLineEdit()
        result_lb = QLabel('结果码')
        form_layout.addRow(result_lb, result_e)

        copy_bt = QPushButton('复制')
        copy_bt.clicked.connect(self.copy)
        main_layout.addWidget(copy_bt)

        self.code_e = code_e
        self.result_e = result_e

    def copy(self):
        if not self.result_e.text():
            return
        pyperclip.copy(self.result_e.text())

    def update_code(self):
        self.result_e.setText(validation.encrypt(self.code_e.text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = CodeGenerator()
    win.show()
    sys.exit(app.exec_())

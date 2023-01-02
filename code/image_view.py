# _*_ coding: utf-8 _*_
# @Time : 2022/5/22 0:38
# @Author : 李明昊 Richard Li
# @Version：V 0.1
# @File : image_view.py
# @desc : 显示图片主要界面
from typing import List

from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem

from digit_api import DataTuple

"""
图片显示组件
"""


class ImageView(QGraphicsView):
    def __init__(self):
        super().__init__()
        # 当前场景
        self.current_scene = BoxesDisplayScene(self)
        self.setScene(self.current_scene)

    def update(self):
        super().update()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        self.current_scene.update_image()
        super().resizeEvent(event)


"""
显示选框的Scene
"""


class BoxesDisplayScene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__()
        # 当前显示的image
        self.image = None
        # 当前显示的框
        self.boxes = []

        # 当前pixmap对象
        self.current_pixmap = QGraphicsPixmapItem()
        self.addItem(self.current_pixmap)

        # 当前显示的选框
        self.rect_list = []

        # 子对象
        self.parent = parent


    # 设置图像
    def set_image(self, img: Image):
        self.image = img

    # 设置选框
    def set_boxes(self, boxes: List[DataTuple]):
        # 清空
        self.boxes = boxes

    # 跟新数据显示
    def update_image(self):
        if not self.image:
            return
        # 设置图像
        self.current_pixmap = QGraphicsPixmapItem()
        self.current_pixmap.setPixmap(self.image.toqpixmap())
        self.addItem(self.current_pixmap)
        # 设置选框
        for box in self.boxes:
            rect_item = RegionRectItem(box)
            self.rect_list.append(rect_item)
            self.addItem(rect_item)
        self.parent.fitInView(self.current_pixmap, Qt.KeepAspectRatio)
        self.update()



"""
选框组件
"""


class RegionRectItem(QGraphicsRectItem):
    def __init__(self, data_tuple: DataTuple):
        super().__init__(data_tuple.x, data_tuple.y, data_tuple.width, data_tuple.height)
        # 设置颜色
        self.brush_ = QBrush()
        self.pen_ = QPen(Qt.green, 2)

        # 保持在最前
        super().setZValue(100)

    def paint(self, painter: QtGui.QPainter, *args):
        painter.setPen(self.pen_)
        painter.setBrush(self.brush_)
        painter.drawRect(self.rect())

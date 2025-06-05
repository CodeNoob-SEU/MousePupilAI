import os
import warnings

import cv2
from PIL import ImageColor
import colorcet as cc
import config
def get_pretrain_models():
    """
    获取 pretrain_model 文件夹下的所有模型子目录名称。

    :return: list, 包含模型名称的列表，列表的第一个元素是空字符串 ""。
             如果 'pretrain_model' 目录不存在或其中没有子目录，
             将返回一个只包含空字符串的列表 [""]。
    """
    model_root_dir = config.model_root_dir
    model_name = ["请选择模型"]


    if os.path.exists(model_root_dir) and os.path.isdir(model_root_dir):
        for item in os.listdir(model_root_dir):
            item_path = os.path.join(model_root_dir, item)
            if os.path.isdir(item_path):
                model_name.append(item)
    else:
        warnings.warn("模型根目录不存在，即将为你创建一个新目录pretrain_model。")
        os.mkdir(model_root_dir)
    # print(model_name)
    return model_name

def draw_keypoints(frame, pose, radius=4, pcutoff=0.5):
    cmap = "bmy"
    all_colors = getattr(cc, cmap)
    colors = [
        ImageColor.getcolor(c, "RGB")[::-1]
        for c in all_colors[:: int(len(all_colors) / pose.shape[0])]
    ]
    for j in range(pose.shape[0]):
        if pose[j, 2] > pcutoff:
            x = int(pose[j, 0])
            y = int(pose[j, 1])
            frame = cv2.circle(
                frame, (x, y), radius, colors[j], thickness=-1
            )
    return frame
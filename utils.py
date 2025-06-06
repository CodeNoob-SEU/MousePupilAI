import os
import warnings

import cv2
import numpy as np
from PIL import ImageColor
import colorcet as cc

def get_pretrain_models():
    """
    获取 pretrain_model 文件夹下的所有模型子目录名称。

    :return: list, 包含模型名称的列表，列表的第一个元素是空字符串 ""。
             如果 'pretrain_model' 目录不存在或其中没有子目录，
             将返回一个只包含空字符串的列表 [""]。
    """
    model_root_dir = "pretrain_model"
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


def estimate_pupil_diameter(frame_data: np.ndarray, point_names=None):
    """
    根据追踪的8个关键点坐标估算瞳孔直径（取多个对角点对的欧几里得距离平均）

    参数：
        frame_data: numpy array, shape (8, 3)，每行为[x, y, confidence]
        point_names: 可选，对应8个点的名称，默认如下顺序

    返回：
        estimated_diameter: float
    """
    if point_names is None:
        point_names = ['Lpupil', 'LDpupil', 'Dpupil', 'DRpupil',
                       'Rpupil', 'RVupil', 'Vpupil', 'VLpupil']

    name_to_index = {name: idx for idx, name in enumerate(point_names)}

    # 配对列表（对角/轴向）
    pairs = [
        ('Lpupil', 'Rpupil'),
        ('LDpupil', 'RVupil'),
        ('Dpupil', 'Vpupil'),
        ('DRpupil', 'VLpupil')
    ]

    distances = []
    for p1, p2 in pairs:
        idx1, idx2 = name_to_index[p1], name_to_index[p2]
        x1, y1 = frame_data[idx1][:2]
        x2, y2 = frame_data[idx2][:2]
        dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        distances.append(dist)

    # 平均距离作为估算直径
    estimated_diameter = np.mean(distances)
    return estimated_diameter

def check_tensorrt_available():
    """
    Checks if NVIDIA TensorRT is available in the current Python environment.

    Returns:
        bool: True if TensorRT can be imported, False otherwise.
    """
    try:
        import tensorrt as trt
        print(f"🎉 TensorRT found and available! Version: {trt.__version__}")
        return True
    except ImportError:
        print("❌ TensorRT module not found. It might not be installed or configured correctly.")
        print("   Please ensure you have installed the `tensorrt` Python package and its dependencies.")
        return False
    except Exception as e:
        # Catch other potential runtime errors during import (e.g., missing CUDA libraries)
        print(f"⚠️ An error occurred while trying to import TensorRT: {e}")
        print("   This might indicate an issue with your TensorRT installation or underlying CUDA/cuDNN setup.")
        return False
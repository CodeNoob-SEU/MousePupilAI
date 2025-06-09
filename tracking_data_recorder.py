from datetime import datetime

import numpy as np
import pandas as pd
from numpy.core.records import record
from tensorflow import timestamp
import cv2
from utils import *


class TrackingDataRecorder:
    def __init__(self,fps, point_names=None):
        if point_names is None:
            point_names = ['Lpupil', 'LDpupil', 'Dpupil', 'DRpupil', 'Rpupil', 'RVupil', 'Vpupil', 'VLpupil']
        self.point_names = point_names
        self.pose_records = []  # 存储每一帧的数据（列表嵌套字典）
        self.frame_records = []
        self.fps = fps
        self.save_data_root = get_absolute_path("output")
        if not os.path.exists(self.save_data_root):
            os.mkdir(self.save_data_root)

    def add_frame(self, frame):
        """
        收集绘制好的帧（如OpenCV的ndarray图像）
        """
        self.frame_records.append(frame)

    def add_frame_pose(self, pose_data: np.ndarray):
        """
        添加一帧追踪结果 (shape: 8x3), 每一行为 [x, y, confidence]
        """
        if pose_data.shape != (len(self.point_names), 3):
            raise ValueError(f"Expected frame shape ({len(self.point_names)}, 3), got {pose_data.shape}")

        frame_dict = {}
        for i, name in enumerate(self.point_names):
            x, y, conf = pose_data[i]
            frame_dict[f"{name}_x"] = x
            frame_dict[f"{name}_y"] = y
            frame_dict[f"{name}_conf"] = conf
        frame_dict[f"diameter"] = estimate_pupil_diameter(pose_data)
        self.pose_records.append(frame_dict)

    def to_dataframe(self):
        """
        将记录转为 pandas DataFrame
        """
        return pd.DataFrame(self.pose_records)

    def save_csv(self, file_name="tracking_output"):
        """
        保存数据到 CSV 文件
        """
        df = self.to_dataframe()
        df.to_csv(file_name, index=False)
        print(f"[INFO] Tracking data saved to {file_name}")

    def save_video(self, file_name="tracking_output"):
        if not self.frame_records:
            print("没有帧可保存！")
            return

        # 假设 video_loader 是你的视频加载器实例
        fps = self.fps  # 或者用 cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FPS)
        height, width, _ = self.frame_records[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(file_name, fourcc, fps, (width, height))

        for frame in self.frame_records:
            video_writer.write(frame)
        video_writer.release()
        print(f"视频已保存到 {file_name}")

    def save(self,file_name="tracking_output"):
        record_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = file_name+"_"+record_time
        dir_name = os.path.join(self.save_data_root, dir_name)
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        csv_path = os.path.join(dir_name, f"{file_name}.csv")
        video_path = os.path.join(dir_name, f"{file_name}.mp4")
        self.save_csv(csv_path)
        self.save_video(video_path)

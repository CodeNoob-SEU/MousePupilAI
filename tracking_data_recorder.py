import numpy as np
import pandas as pd


class TrackingDataRecorder:
    def __init__(self, point_names=None):
        if point_names is None:
            point_names = ['Lpupil', 'LDpupil', 'Dpupil', 'DRpupil', 'Rpupil', 'RVupil', 'Vpupil', 'VLpupil']
        self.point_names = point_names
        self.records = []  # 存储每一帧的数据（列表嵌套字典）

    def add_frame_pose(self, frame_data: np.ndarray):
        """
        添加一帧追踪结果 (shape: 8x3), 每一行为 [x, y, confidence]
        """
        if frame_data.shape != (len(self.point_names), 3):
            raise ValueError(f"Expected frame shape ({len(self.point_names)}, 3), got {frame_data.shape}")

        frame_dict = {}
        for i, name in enumerate(self.point_names):
            x, y, conf = frame_data[i]
            frame_dict[f"{name}_x"] = x
            frame_dict[f"{name}_y"] = y
            frame_dict[f"{name}_conf"] = conf
        self.records.append(frame_dict)

    def to_dataframe(self):
        """
        将记录转为 pandas DataFrame
        """
        return pd.DataFrame(self.records)

    def save_csv(self, path="tracking_output.csv"):
        """
        保存数据到 CSV 文件
        """
        df = self.to_dataframe()
        df.to_csv(path, index=False)
        print(f"[INFO] Tracking data saved to {path}")

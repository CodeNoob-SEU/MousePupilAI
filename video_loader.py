import cv2
from tqdm import tqdm


class BasicVideoLoader():
    def __init__(self):
        self.cap = None
        self.frame_count = 0

    def load_video(self, source):
        """
        加载视频源。
        对于 LocalVideoLoader，source 是文件路径。
        对于 CameraVideoLoader，source 是摄像头索引 (通常是 0)。
        """
        pass

    def get_frame(self):
        """
        获取当前帧。
        返回:
            tuple: (bool, frame) 其中 bool 表示是否成功读取，frame 是图像帧。
        """
        pass

    def draw_labeled_frame(self, frame, point_list):
        """
        在帧上绘制标签。
        参数:
            frame: 要绘制的图像帧。
            point_list: 追踪关键点的坐标。
        返回:
            frame: 绘制了标签的图像帧。
        """
        pass

    def release(self):
        """释放视频捕捉对象。"""
        if self.cap is not None:
            self.cap.release()
        self.frame_count = 0

    def __del__(self):
        self.release()

class LocalVideoLoader(BasicVideoLoader):
    def __init__(self, video_path: str):
        """
        初始化本地视频加载器。
        所有帧将被预加载到内存中。
        参数:
            video_path (str): 本地视频文件的路径。
        """
        super().__init__()  # 调用基类构造函数
        self.video_path = video_path
        self.current_frame_idx = 0  # 当前要提供的帧的索引
        self.frame_list = []  # 存储所有加载的帧
        self.metadata_frame_count = 0  # 从视频元数据获取的总帧数
        self.fps = 0
        self.load_video(video_path)

    def load_video(self, source: str):
        """
        从指定路径加载视频的所有帧到内存中。
        参数:
            source (str): 视频文件的路径。
        """
        self.video_path = source
        self.cap = cv2.VideoCapture(self.video_path)

        if not self.cap.isOpened():
            # 如果视频无法打开，清空列表并重置计数器
            self.frame_list = []
            self.current_frame_idx = 0
            self.metadata_frame_count = 0
            self.cap.release()  # 确保释放
            raise IOError(f"无法打开视频文件: {self.video_path}")

        self.metadata_frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 重置/清空列表和索引，以支持可能的重载操作
        self.frame_list = []
        self.current_frame_idx = 0
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        print(f"正在加载视频 '{self.video_path}' (元数据总帧数: {self.metadata_frame_count})...")

        # 使用 tqdm 创建进度条
        # 我们将迭代 metadata_frame_count 次，但只添加成功读取的帧
        for i in tqdm(range(self.metadata_frame_count), desc=f"加载 {self.video_path}"):
            ret, frame = self.cap.read()
            if ret:
                self.frame_list.append(frame)
            else:
                # 如果读取失败（例如视频提前结束或损坏）
                print(f"\n警告: 在索引 {i} 处读取帧失败 (元数据总帧数: {self.metadata_frame_count})。")
                print("视频可能已损坏或实际帧数少于元数据。停止加载。")
                break  # 停止尝试读取更多帧

        self.cap.release()  # 所有帧已加载到列表，释放 VideoCapture 对象

        num_loaded_frames = len(self.frame_list)
        if num_loaded_frames == 0 and self.metadata_frame_count > 0:
            print(f"警告: 视频 '{self.video_path}' 元数据表明有 {self.metadata_frame_count} 帧, 但未能成功加载任何帧。")
        elif num_loaded_frames < self.metadata_frame_count:
            print(
                f"提示: 视频 '{self.video_path}' 成功加载了 {num_loaded_frames} 帧 (元数据总帧数: {self.metadata_frame_count})。")
        else:
            print(f"视频 '{self.video_path}' 加载成功，共 {num_loaded_frames} 帧。")

    def get_frame(self):
        """
        从预加载的帧列表中获取下一帧。
        返回:
            list frame 如果成功获取帧，，frame 是图像帧；
                           否则 (已到达列表末尾或列表为空)  frame 为 None。
        """
        # 检查当前索引是否在已加载帧列表的有效范围内
        if self.current_frame_idx < len(self.frame_list):
            # 获取当前帧
            frame_to_return = self.frame_list[self.current_frame_idx]
            # 移动到下一帧的索引，为下一次调用做准备
            self.current_frame_idx += 1
            return frame_to_return
        else:
            # 没有更多帧可供读取 (已到达列表末尾，或列表为空)
            return None

    def draw_labeled_frame(self, frame, point_list):
        """
        在帧上绘制标记点。
        参数:
            frame: 要绘制的图像帧 (numpy array)。
            point_list: 一个包含 (x, y) 坐标元组的列表。
        返回:
            绘制了标记的图像帧。如果输入帧为None或point_list为空，则返回原始帧。
        """
        if frame is None:
            return None

        # 创建帧的副本以避免修改原始列表中的帧
        labeled_frame = frame.copy()

        if point_list:  # 确保 point_list 不为 None 或空
            for point in point_list:
                try:
                    # 确保坐标是整数
                    center_x = int(point[0])
                    center_y = int(point[1])
                    cv2.circle(labeled_frame, (center_x, center_y), radius=5, color=(0, 0, 255), thickness=-1)  # 红色实心圆点
                except IndexError:
                    print(f"警告: 点 {point} 的格式不正确，应为 (x, y)。")
                except Exception as e:
                    print(f"警告: 绘制点 {point} 时出错: {e}")

        return labeled_frame

    def get_total_loaded_frames(self):
        """返回实际加载到内存中的帧数。"""
        return len(self.frame_list)

    def get_metadata_frame_count(self):
        """返回从视频文件元数据中读取的总帧数。"""
        return self.metadata_frame_count

    def reset_frame_counter(self):
        """重置帧计数器，以便从头开始重新遍历已加载的帧。"""
        self.current_frame_idx = 0
        print("帧计数器已重置，将从第一帧开始读取。")


class CameraVideoLoader(BasicVideoLoader):
    #TODO 摄像头采集实现
    def __init__(self, camera_index: int = 0):
        """
        初始化摄像头视频加载器。
        参数:
            camera_index (int): 摄像头的索引 (通常从 0 开始)。
        """
        super().__init__()
        self.camera_index = camera_index
        self.load_video(camera_index)

    def load_video(self, source: int):
        """
        打开指定的摄像头。
        参数:
            source (int): 摄像头的索引。
        """
        self.camera_index = source
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise IOError(f"无法打开摄像头索引: {self.camera_index}")
        self.frame_count = 0
        print(f"摄像头 {self.camera_index} 打开成功。")

    def get_frame(self):
        """
        从摄像头捕获当前帧。
        返回:
            tuple: (bool, frame) 如果成功捕获帧，则 bool 为 True，frame 为图像帧；否则为 False, None。
        """
        if self.cap is None or not self.cap.isOpened():
            # print("错误：摄像头未初始化。请先调用 load_video。")
            print("摄像头未初始化。已默认调用 load_video。")
            self.load_video(self.camera_index)
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
        return ret, frame

    def draw_labeled_frame(self, frame, point_list):
        #TODO 绘制标注帧
        pass

if __name__ == '__main__':
    import numpy as np
    video_path = "example.mp4"
    loader = LocalVideoLoader(video_path)
    frame_list = []
    while frame :=loader.get_frame():
        frame_list.append(np.array(frame))
    print(frame_list[-1].shape)



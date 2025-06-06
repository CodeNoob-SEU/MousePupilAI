import warnings
from typing import Optional

import numpy as np  # For creating a dummy frame if needed for init
from dlclive import DLCLive, Processor  # Assuming Processor is correctly importable or defined
from dlclive.exceptions import DLCLiveError  # For error handling


class ModelLoader:
    def __init__(self,
                 model_path: str,
                 processor: Optional[Processor] = None,
                 model_type: str = "base",
                 # Explicit parameters with defaults for DLCLive
                 resize: float = 1.0,  # 1.0 means no resize, pass directly to DLCLive
                 pcutoff: float = 0.5,
                 display_frames: bool = False, # Maps to DLCLive's 'display'
                 display_radius: int = 3,
                 display_cmap: str = "bmy",
                 # For any other DLCLive parameters
                 **other_dlc_live_kwargs):
        self.model_path = model_path
        self.processor = processor
        self.model_type = model_type

        self.resize_factor = resize # 0.5 0.75 1
        self.pcutoff_value = pcutoff
        self.show_display = display_frames
        self.marker_radius = display_radius
        self.marker_cmap = display_cmap

        self.live: Optional[DLCLive] = None
        self.is_initialized: bool = False
        dlc_constructor_args = {
            "model_path": self.model_path,
            "model_type": self.model_type,
            "processor": self.processor,  # Pass the (potentially None) processor
            "resize": self.resize_factor,
            "pcutoff": self.pcutoff_value,
            "display": self.show_display,
            "display_radius": self.marker_radius,
            "display_cmap": self.marker_cmap,
            **other_dlc_live_kwargs  # Other args like 'precision', 'cropping', 'dynamic', 'convert2rgb'
        }
        print("-"*8+"当前模型参数"+"-"*8)
        print(dlc_constructor_args)
        self.live = DLCLive(**dlc_constructor_args)

    def infer_pose(self, frame: np.ndarray) -> Optional[np.ndarray]:
        if not self.is_initialized:
            pose = self.live.init_inference(frame)
            self.is_initialized = True
        else:
            pose = self.live.get_pose(frame)
        return pose


if __name__ == '__main__':
    from video_loader import LocalVideoLoader
    videoloader = LocalVideoLoader("13.mp4")

    model_path = "pretrain_model/DLC_MiceEyeTracking_resnet_50_iteration-1_shuffle-1"
    model = ModelLoader(model_path, model_type="base")
    pose = model.infer_pose(videoloader.get_frame())
    print(pose.shape)
    print(pose)
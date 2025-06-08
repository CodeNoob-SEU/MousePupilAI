import time
import warnings
import colorcet as cc
from PIL import ImageColor
import numpy as np
from dlclive import DLCLive, Processor, benchmark_videos
import cv2
import os

from tqdm.auto import tqdm

# 检查视频文件是否存在
video_path = "../13.mp4"
model_path = "../pretrain_model/DLC_MiceEyeTracking_resnet_50_iteration-1_shuffle-1"
resize = 1
save_video = False
output = None
pcutoff = 0.4
display_radius=3
print_rate = True

cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()
n_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)-1
n_frames = int(n_frames)
im_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
print(n_frames, im_size)
if resize is not None:
    im_size = (int(im_size[0] * resize), int(im_size[1] * resize))

if save_video:
        colors = None
        out_dir = (
            output
            if output is not None
            else os.path.dirname(os.path.realpath(video_path))
        )
        out_vid_base = os.path.basename(video_path)
        out_vid_file = os.path.normpath(
            f"{out_dir}/{os.path.splitext(out_vid_base)[0]}_DLCLIVE_LABELED.mp4"
        )
        fourcc = cv2.VideoWriter_fourcc(*"MP4V")
        fps = cap.get(cv2.CAP_PROP_FPS)
        vwriter = cv2.VideoWriter(out_vid_file, fourcc, fps, im_size)

dlc_proc = Processor()
live = DLCLive(model_path=model_path, processor=dlc_proc)

inf_times = np.zeros(n_frames)
poses = []
poses.append(live.init_inference(frame))

TFGPUinference = True if len(live.outputs) == 1 else False
iterator = tqdm(range(n_frames))
for i in iterator:

    ret, frame = cap.read()

    if not ret:
        warnings.warn(
            "Did not complete {:d} frames. There probably were not enough frames in the video {}.".format(
                n_frames, video_path
            )
        )
        break

    start_pose = time.time()
    poses.append(live.get_pose(frame))
    inf_times[i] = time.time() - start_pose

    if save_video:

        cmap = "bmy"
        all_colors = getattr(cc, cmap)
        colors = [
            ImageColor.getcolor(c, "RGB")[::-1]
            for c in all_colors[:: int(len(all_colors) / poses[-1].shape[0])]
        ]

        this_pose = poses[-1]
        for j in range(this_pose.shape[0]):
            if this_pose[j, 2] > pcutoff:
                x = int(this_pose[j, 0])
                y = int(this_pose[j, 1])
                frame = cv2.circle(
                    frame, (x, y), display_radius, colors[j], thickness=-1
                )

        if resize is not None:
            frame = cv2.resize(frame, im_size)
        vwriter.write(frame)

        if print_rate:
            print("pose rate = {:d}".format(int(1 / inf_times[i])))
if save_video:
    vwriter.release()

if save_poses:

        cfg_path = os.path.normpath(f"{model_path}/pose_cfg.yaml")
        ruamel_file = ruamel.yaml.YAML()
        dlc_cfg = ruamel_file.load(open(cfg_path, "r"))
        bodyparts = dlc_cfg["all_joints_names"]
        poses = np.array(poses)


        poses = poses.reshape((poses.shape[0], poses.shape[1] * poses.shape[2]))
        pdindex = pd.MultiIndex.from_product(
            [bodyparts, ["x", "y", "likelihood"]], names=["bodyparts", "coords"]
        )
        pose_df = pd.DataFrame(poses, columns=pdindex)

        out_dir = (
            output
            if output is not None
            else os.path.dirname(os.path.realpath(video_path))
        )
        out_vid_base = os.path.basename(video_path)
        out_dlc_file = os.path.normpath(
            f"{out_dir}/{os.path.splitext(out_vid_base)[0]}_DLCLIVE_POSES.h5"
        )
        pose_df.to_hdf(out_dlc_file, key="df_with_missing", mode="w")

live.close()
cap.release()

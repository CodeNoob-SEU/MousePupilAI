import gradio as gr
# NumPy 的导入已移至 video_processing_logic.py，如果 Gradio-Test.py 不直接使用它，可以移除
# import numpy as np
from model_loader import load_model_placeholder # 从 model_loader.py 导入
from video_processing_logic import video_processor # 从 video_processing_logic.py 导入

# 1. 加载模型
# 模型现在从 model_loader.py 加载
model = load_model_placeholder()

# video_processor 函数已移至 video_processing_logic.py

# 创建一个包装函数，以适应 Gradio Interface 的 fn 参数签名
# Gradio 的 fn 需要一个只接受输入组件对应参数的函数
def gradio_video_processor_wrapper(model_params, video_input): # video_input 会是视频路径或摄像头流
    return video_processor(model, model_params, video_input)

# 新的输入组件
model_param_selector = gr.Dropdown(
    choices=["config_A", "config_B", "default_config"],
    value="default_config",
    label="选择模型参数配置"
)

video_input_component = gr.Video(
    label="输入视频 (上传或使用摄像头)",
    sources=["upload", "webcam"] # 允许文件上传和摄像头
)

demo = gr.Interface(
    fn=gradio_video_processor_wrapper, # 使用包装函数
    inputs=[
        model_param_selector,
        video_input_component
    ],
    outputs=gr.Video(label="输出视频"),
    title="MouseEyeTracker",
    description="上传视频或使用摄像头，选择模型配置，然后进行处理。模型和处理逻辑从单独的文件加载。"
)

if __name__ == "__main__":
    demo.launch()

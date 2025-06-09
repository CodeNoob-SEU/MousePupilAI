import os
import time
from datetime import datetime
import gradio as gr
from tqdm import tqdm

from model_loader import ModelLoader
from utils import *
from video_loader import LocalVideoLoader
from tracking_data_recorder import TrackingDataRecorder

class MainWindow:
    def __init__(self):
        # print("strat loading backend...")
        # 参数选择模块
        print(get_absolute_path("pretrain_model"))
        self.loaded_model_instance : ModelLoader = None
        self.data_recorder_instance :TrackingDataRecorder= None
        self.is_tensorrt_available = check_tensorrt_available()
        self.current_model_names = get_pretrain_models()
        self.display = True

        with gr.Blocks(title="MouseEyeTracker Demo", theme=gr.themes.Soft()) as self.demo:
            # 第1行：标题
            with gr.Row():
                with gr.Column(scale=4): # 标题占据更多空间
                    gr.Markdown("# MouseEyeTracker 演示程序", latex_delimiters=[]) # 应用主标题
                with gr.Column(scale=1, min_width=180): # 给按钮固定一些最小宽度
                    self.refresh_models_button = gr.Button("🔄 更新模型列表")

            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                    # TensorRT 加速勾选框
                        self.tensorrt_checkbox = gr.Checkbox(
                            label="启用 TensorRT 加速",
                            value=False,  # 默认不选中
                            interactive=self.is_tensorrt_available
                        )
                    with gr.Row():
                        self.slidingwindow_checkbox = gr.Checkbox(
                            label="启用滑动窗口绘图",
                            value=False,  # 默认不选中
                            interactive=True
                        )
                with gr.Column(scale=1):
                    # Resize 下拉框
                    self.resize_dropdown = gr.Dropdown(
                        label="图像缩放比例 (Resize)",
                        choices=[0.5, 0.75, 1.0],  # 注意这里用浮点数
                        value=1.0,  # 默认值为1.0
                        interactive=True
                    )
                with gr.Column(scale=1):
                    # Pcutoff 下拉框
                    self.pcutoff_dropdown = gr.Dropdown(
                        label="置信度阈值 (Pcutoff)",
                        choices=[0.3,0.4,0.5,0.6],
                        value=0.5,  # 默认值
                        interactive=True
                    )

            # 第2行：模型参数选择
            self.model_param_selector = gr.Dropdown(
                choices=self.current_model_names,
                value=self.current_model_names[0] if self.current_model_names else "", # 默认选择第一个（通常是空字符串）
                label="选择模型参数配置 (Select Model Configuration)"
            )
            self.status_textbox = gr.Textbox(
                label="状态信息 (Status)",
                value="请选择一个模型或执行操作。",  # 初始消息
                interactive=False,  # 用户不可编辑
                lines=1,  # 可以根据需要调整行数，如果消息较长可以增加
                max_lines=3  # 最多显示3行，然后出现滚动条
            )

            # 第3行：输入视频 和 输出视频 (并排)
            gr.Markdown("### 视频处理模块 (Video Processing Area)")
            with gr.Row():
                with gr.Column(scale=1):  # 输入占一半
                    self.video_input_component = gr.Video(
                        label="输入视频 (Input Video)",
                        sources=["upload", "webcam"],  # 允许文件上传和摄像头
                        height=360  # 可以调整显示高度
                    )
                with gr.Column(scale=1):  # 输出占一半
                    self.video_output_component = gr.Image(
                        label="实时处理帧 (Live Processed Frame)",
                        type="numpy",
                        interactive=False,
                        streaming=True,
                        height=360  # 可以调整显示高度
                    )

            # 第4行：处理按钮
            self.process_button = gr.Button("开始处理视频 (Process Video)", variant="primary")

            with gr.Row(height=300):
                self.plot_component = gr.Plot(
                    label="瞳孔直径变化图 (Pupil Diameter over Time)",
                )

            # --- 定义组件的交互行为 ---

            # 刷新模型列表按钮的行为
            self.refresh_models_button.click(
                fn=self.handle_refresh_models,
                inputs=None,  # 无需从UI获取输入
                outputs=[self.model_param_selector]  # 更新模型下拉列表
            )

            self.model_param_selector.change(
                fn=self.load_model_by_name,
                inputs=[self.model_param_selector,self.resize_dropdown, self.pcutoff_dropdown],
                outputs=[self.status_textbox]
            )

            # 处理视频按钮的行为
            self.process_button.click(
                fn=self.gradio_video_processor_wrapper,
                inputs=[self.video_input_component],
                outputs=[self.video_output_component,self.plot_component]
            )

    def gradio_video_processor_wrapper(self,video_path):

        if self.loaded_model_instance is None:
            self.status_textbox.value = "模型未加载，请加载模型后重试"
            return
        video_loader = LocalVideoLoader(video_path)
        model = self.loaded_model_instance
        frame_indices = []
        diameters = []
        self.data_recorder_instance = TrackingDataRecorder(fps=video_loader.fps)
        it = tqdm(range(len(video_loader.frame_list)))
        for i in it:
            frame = video_loader.get_frame()
            if frame is None:
                return
            pose = model.infer_pose(frame)
            if self.display:
                frame = draw_keypoints(frame, pose)
            self.data_recorder_instance.add_frame(frame)
            self.data_recorder_instance.add_frame_pose(pose)
            diameter = estimate_pupil_diameter(pose)  # 你已有的函数
            diameters.append(diameter)
            frame_indices.append(i)
            plot_fig = generate_plotly_lineplot(frame_indices, diameters, window_size=50)
            yield frame,plot_fig

        base_name = os.path.basename(video_path)
        filename, _ = os.path.splitext(base_name)
        self.data_recorder_instance.save(filename)
        self.status_textbox.value = f"{base_name}处理完成"
        return

    def handle_refresh_models(self):
        """
        当“更新模型列表”按钮被点击时调用。
        它会重新获取模型列表并更新下拉框的选项。
        """
        print("UI事件：正在更新模型列表...")
        self.current_model_names = get_pretrain_models()

        new_value = self.current_model_names[0] if self.current_model_names else ""
        print(f"UI事件：模型列表已更新为 {self.current_model_names}，将默认选中 '{new_value}'")
        return gr.update(choices=self.current_model_names, value=new_value)

    def load_model_by_name(self, model_name_to_load,resize, pcutoff):
        """
        根据选择的模型名称加载模型。
        这个函数会被 Dropdown 的 change 事件调用。
        """
        if not model_name_to_load or model_name_to_load == "请选择模型":
            self.loaded_model_instance = None
            status_message = "没有选择模型。"
            print(status_message)
            return status_message  # 返回状态给 UI

        base_path = get_absolute_path("pretrain_model")
        model_path = os.path.join(base_path, model_name_to_load)
        if os.path.exists(model_path):
            print(f"开始加载模型: {model_name_to_load}...")
            self.loaded_model_instance = ModelLoader(model_path,resize=resize, pcutoff=pcutoff)
            status_message = f"模型 '{model_name_to_load}' 加载成功！"
        else :
            print(f"模型{model_name_to_load}不存在")

        return status_message
    
    def run(self):
        self.demo.launch(server_name="127.0.0.1", server_port=28989, share=False, inbrowser=False)



if __name__ == '__main__':
    MainWindow().run()
import os
import shutil
import subprocess
from utils import get_absolute_path
import sys
def remove_if_exists(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def build_backend():
    # 1. 清理残余目录和文件
    for name in ['build', 'dist', '_internal', 'MousePupilAIbackend']:
        remove_if_exists(name)

    # 2. 执行 pyinstaller
    result = subprocess.run(['pyinstaller', 'mainwindow.spec'])
    if result.returncode != 0:
        print('PyInstaller 构建失败')
        exit(1)

    # 3. 移动 _internal 目录和 MousePupilAImain 可执行文件到项目根目录
    dist_dir = 'dist/mainwindow'
    # 先处理 _internal 目录
    src_internal = os.path.join(dist_dir, '_internal')
    if os.path.isdir(src_internal):
        dst_internal = os.path.join(os.getcwd(), '_internal')
        remove_if_exists(dst_internal)
        shutil.move(src_internal, dst_internal)
    # 再处理 MousePupilAImain 可执行文件
    src_exec = os.path.join(dist_dir, 'MousePupilAIbackend')
    if os.path.isfile(src_exec):
        dst_exec = os.path.join(os.getcwd(), 'MousePupilAIbackend')
        remove_if_exists(dst_exec)
        shutil.move(src_exec, dst_exec)

def build_frontend():
    # 1. 定位 web 目录
    project_root = get_absolute_path(".")
    web_dir = os.path.join(project_root, 'web')
    if not os.path.isdir(web_dir):
        raise FileNotFoundError(f"'web' 目录未找到: {web_dir}")

    # 2. 执行 npm run make
    print("正在构建 Electron 前端（npm run make）...")
    process = subprocess.Popen(
        ['npm run make'],
        cwd=web_dir,
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"构建失败，npm run make 返回码: {return_code}")

    print("构建完成，正在查找生成的应用产物...")

    # 3. 查找构建产物
    out_dir = os.path.join(web_dir, 'out')
    if not os.path.isdir(out_dir):
        raise FileNotFoundError(f"构建输出目录不存在: {out_dir}")

    # 支持的产物后缀
    executable_exts = ('.exe', '.app', '.AppImage', '.dmg')

    target_path = None
    for subdir_name in os.listdir(out_dir):
        subdir_path = os.path.join(out_dir, subdir_name)
        if os.path.isdir(subdir_path) and subdir_name.startswith("web-"):
            for item in os.listdir(subdir_path):
                item_path = os.path.join(subdir_path, item)
                if item.endswith(executable_exts) or "MousePupilAI" in item:
                    target_path = item_path
                    break
        if target_path:
            break

    if not target_path or not os.path.exists(target_path):
        raise FileNotFoundError("未能找到构建生成的可执行文件（MousePupilAI）")

    # 4. 移动产物到项目根目录
    dest_path = os.path.join(project_root, os.path.basename(target_path))

    print(f"正在将构建产物移动到项目根目录: {dest_path}")

    # 如果目标已存在，先删除
    if os.path.exists(dest_path):
        if os.path.isfile(dest_path):
            os.remove(dest_path)
        else:
            shutil.rmtree(dest_path)

    # 拷贝或移动文件/目录
    if os.path.isfile(target_path):
        shutil.move(target_path, dest_path)
    else:
        shutil.copytree(target_path, dest_path)

    print(f"✅ 构建完成：{os.path.basename(target_path)} 已移动到项目根目录。")

if __name__ == '__main__':
    # build_backend()
    build_frontend()
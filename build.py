import os
import shutil
import subprocess

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
    # TODO 有bug无法完成编译
    # 1: 定位到 web 目录
    web_dir = os.path.join(os.getcwd(), 'web')
    if not os.path.isdir(web_dir):
        raise FileNotFoundError(f"'web' 目录未找到: {web_dir}")

    # 2: 运行 npm run make
    print("正在执行 npm run make ...")
    subprocess.run(["npm", "run", "make"], cwd=web_dir, check=True)
    print("make 执行完成")

    # 3: 查找 /out/web-*/MousePupilAI 目录
    out_dir = os.path.join(web_dir, 'out')
    if not os.path.isdir(out_dir):
        raise FileNotFoundError(f"构建输出目录未找到: {out_dir}")

    # 获取 web-架构目录名称
    target_dir = None
    for name in os.listdir(out_dir):
        if name.startswith('web-'):
            possible_path = os.path.join(out_dir, name, 'MousePupilAI')
            if os.path.isfile(possible_path) or os.path.isdir(possible_path):
                target_dir = possible_path
                break

    if not target_dir:
        raise FileNotFoundError("未找到生成的 MousePupilAI 可执行文件")

    #4: 移动到项目根目录
    root_path = os.getcwd()
    target_name = os.path.basename(target_dir)
    dest_path = os.path.join(root_path, target_name)

    if os.path.isfile(target_dir):
        shutil.move(target_dir, dest_path)
    elif os.path.isdir(target_dir):
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(target_dir, dest_path)
    print(f"已将 {target_name} 移动到项目根目录")

if __name__ == '__main__':
    build_backend()
    # build_frontend()
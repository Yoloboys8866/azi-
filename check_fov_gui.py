import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# 尝试导入tkinterdnd2库，为了实现拖拽功能
DND_AVAILABLE = False
try:
    import tkinterdnd2
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


# 全局变量，用于存储当前选择的文件路径
current_path = ""

def check_file(filepath):
    errors = []
    results = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        # 匹配多种可能的azimuth格式："azimuth:" 或 "Azi:"后面跟数字
        azi_match = re.search(r"(?:azimuth|Azi):\s*([-\d.]+)", line)
        
        # 找FOV Status（可能是"FOV Status:"或"TV_FOV Status:"）
        if azi_match:
            for j in range(i, min(i + 3, len(lines))):
                # 匹配多种可能的FOV Status格式
                fov_match = re.search(r"(?:TV_)?FOV Status:\s*(\d+)", lines[j])
                if fov_match:
                    azi = float(azi_match.group(1))
                    fov = int(fov_match.group(1))

                    if azi == 60.0 and fov != 1:
                        errors.append((j, f"错误: 第{j}行 -> azi=60, FOV={fov} (应为1) | {lines[j].strip()}"))
                    elif azi == -60.0 and fov != 0:
                        errors.append((j, f"错误: 第{j}行 -> azi=-60, FOV={fov} (应为0) | {lines[j].strip()}"))

                    results.append((azi, fov, j))
                    break
        
        # 另一种情况：直接在同一条中找FOV Status
        fov_match = re.search(r"(?:TV_)?FOV Status:\s*(\d+)", line)
        if fov_match and not azi_match:
            # 如果找到了FOV但没有对应的azimuth，往上找azimuth
            for j in range(max(0, i-3), i):
                azi_match_prev = re.search(r"(?:azimuth|Azi):\s*([-\d.]+)", lines[j])
                if azi_match_prev:
                    azi = float(azi_match_prev.group(1))
                    fov = int(fov_match.group(1))
                    
                    if azi == 60.0 and fov != 1:
                        errors.append((i, f"错误: 第{i}行 -> azi=60, FOV={fov} (应为1) | {lines[i-1].strip()}"))
                    elif azi == -60.0 and fov != 0:
                        errors.append((i, f"错误: 第{i}行 -> azi=-60, FOV={fov} (应为0) | {lines[i-1].strip()}"))
                    
                    results.append((azi, fov, i))
                    break

    # 检查是否有重复冲突
    for azi_value in [60.0, -60.0]:
        fovs = {f for a, f, _ in results if a == azi_value}
        if len(fovs) > 1:
            errors.append((0, f"错误: azi={azi_value} 出现多个 FOV 值 {fovs}"))

    return errors


def run_check(path):
    global current_path
    output_box.delete(1.0, tk.END)
    
    # 存储当前选择的路径
    current_path = path
    
    # 更新状态标签
    status_label.config(text=f"当前选择: {os.path.basename(path) if len(path) > 50 else path}")
    
    if os.path.isdir(path):
        txt_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".txt")]
        if not txt_files:
            output_box.insert(tk.END, f"[目录] {path} 中未找到 txt 文件\n")
            return

        for f in txt_files:
            errors = check_file(f)
            if errors:
                output_box.insert(tk.END, f"[文件] {f} 检测到错误:\n", "error")
                for line_num, msg in errors:
                    output_box.insert(tk.END, f"   {msg}\n", "error")
            else:
                output_box.insert(tk.END, f"[文件] {f} 检测通过 ✅\n", "ok")

    elif os.path.isfile(path):
        errors = check_file(path)
        if errors:
            output_box.insert(tk.END, f"[文件] {path} 检测到错误:\n", "error")
            for line_num, msg in errors:
                output_box.insert(tk.END, f"   {msg}\n", "error")
        else:
            output_box.insert(tk.END, f"[文件] {path} 检测通过 ✅\n", "ok")


# 开始检测功能

def start_detection():
    global current_path
    if current_path:
        run_check(current_path)
    else:
        messagebox.showwarning("警告", "请先选择要检测的文件或文件夹！")


def open_file():
    filepath = filedialog.askopenfilename(
        title="选择文件",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if filepath:
        global current_path
        current_path = filepath
        status_label.config(text=f"当前选择: {os.path.basename(filepath) if len(filepath) > 50 else filepath}")


def open_folder():
    folderpath = filedialog.askdirectory(title="选择文件夹")
    if folderpath:
        global current_path
        current_path = folderpath
        status_label.config(text=f"当前选择: {os.path.basename(folderpath) if len(folderpath) > 50 else folderpath}")


def drop_event(event):
    path = event.data.strip("{}")
    if os.path.exists(path):
        run_check(path)


# GUI 主界面
# 创建基础ttkbootstrap窗口
root = ttk.Window(themename="cosmo")
root.title("FOV 检测工具")
root.geometry("600x450")  # 缩小窗口尺寸

# 设置窗口图标和最小尺寸
root.minsize(550, 400)

# 如果tkdnd可用，应用拖拽功能到root窗口
if DND_AVAILABLE:
    # 创建一个支持拖拽的窗口包装器
    import tkinterdnd2
    # 重新创建一个支持拖拽的窗口
    root.destroy()  # 先销毁原窗口
    root = tkinterdnd2.Tk()
    # 应用ttkbootstrap主题
    style = ttk.Style()
    style.theme_use("cosmo")
    root.title("FOV 检测工具")
    root.geometry("600x450")
    root.minsize(550, 400)

frame = ttk.Frame(root, padding=15)
frame.pack(fill=BOTH, expand=True)

# 标题标签
label = ttk.Label(frame, text="FOV状态检测工具", font= "微软雅黑 14 bold")
label.pack(pady=(5, 10))

sub_label = ttk.Label(frame, text="拖拽文件/文件夹到窗口，或使用按钮选择", font="微软雅黑 10", foreground="#555555")
sub_label.pack(pady=(0, 10))

# 按钮框架
btn_frame = ttk.Frame(frame)
btn_frame.pack(pady=8)

# 美化按钮样式
btn_file = ttk.Button(btn_frame, text="选择文件", command=open_file, bootstyle="primary-outline", width=10)
btn_file.pack(side=LEFT, padx=8)

btn_folder = ttk.Button(btn_frame, text="选择文件夹", command=open_folder, bootstyle="info-outline", width=10)
btn_folder.pack(side=LEFT, padx=8)

# 添加开始检测按钮
btn_start = ttk.Button(btn_frame, text="开始检测", command=start_detection, bootstyle="success", width=10)
btn_start.pack(side=LEFT, padx=8)

# 添加状态标签
status_label = ttk.Label(frame, text="未选择文件或文件夹", font="微软雅黑 10", foreground="#666666", wraplength=500)
status_label.pack(pady=(5, 8))

# 使用scrolledtext代替普通Text，添加滚动条
output_box = scrolledtext.ScrolledText(
    frame, 
    wrap="word", 
    height=15, 
    bg="white", 
    fg="black",
    font="微软雅黑 9",
    relief="solid",
    bd=1,
    highlightthickness=0
)
output_box.pack(fill=BOTH, expand=True, pady=10)

# 样式 tag
output_box.tag_config("error", foreground="red")
output_box.tag_config("ok", foreground="#008000")  # 深绿色，在白色背景上更清晰

# 拖拽支持
if DND_AVAILABLE:
    try:
        # 设置拖拽功能
        root.drop_target_register(tkinterdnd2.DND_FILES)
        root.dnd_bind("<<Drop>>", drop_event)
        # 在界面上显示拖拽提示
        drag_label = ttk.Label(frame, text="拖拽文件/文件夹到此处", font="微软雅黑 9 italic", foreground="#888888")
        drag_label.pack(pady=(5, 0))
    except Exception as e:
        # 处理任何拖拽相关错误
        status_label.config(text=f"未选择文件或文件夹 (拖拽功能初始化失败: {str(e)[:30]}...)")
else:
    # 当tkinterdnd2未安装时
    status_label.config(text="未选择文件或文件夹 (拖拽功能需要安装: pip install tkinterdnd2)")

root.mainloop()

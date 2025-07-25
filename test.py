import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import random
import math

class CircleCloudApp:
    def __init__(self, master):
        self.master = master
        master.title("Circle Cloud Generator")

        # 参数输入
        self.params = {
            "canvas_width": tk.IntVar(value=222),
            "canvas_height": tk.IntVar(value=640),
            "cloud_count": tk.IntVar(value=3),
            "point_count": tk.IntVar(value=5),
            "max_dist": tk.IntVar(value=40),
            "min_dist": tk.IntVar(value=10),
            "circle_radius": tk.IntVar(value=25),
        }

        row = 0
        for label, var in self.params.items():
            tk.Label(master, text=label.replace("_", " ").title() + ":")\
              .grid(row=row, column=0, sticky="e", padx=4, pady=2)
            tk.Entry(master, textvariable=var, width=10)\
              .grid(row=row, column=1, sticky="w", padx=4, pady=2)
            row += 1

        # 生成按钮
        btn = tk.Button(master, text="Generate", command=self.generate_image)
        btn.grid(row=row, column=0, columnspan=2, pady=8)

        # 用于显示生成结果的 Canvas
        self.image_canvas = tk.Canvas(master, width=512, height=512, bg="gray")
        self.image_canvas.grid(row=0, column=2, rowspan=row+1, padx=10, pady=10)

        self.tk_image = None  # 保持 PhotoImage 引用，防止被回收

    def generate_image(self):
        # 读取参数
        w = self.params["canvas_width"].get()
        h = self.params["canvas_height"].get()
        clouds = self.params["cloud_count"].get()
        n = self.params["point_count"].get()
        maxd = self.params["max_dist"].get()
        mind = self.params["min_dist"].get()
        rad = self.params["circle_radius"].get()

        # 参数合法性检查
        if any(v < 0 for v in (w, h, clouds, n, maxd, mind, rad)):
            messagebox.showerror("参数错误", "请输入非负整数参数。")
            return
        if clouds < 1 or n < 1:
            messagebox.showerror("参数错误", "云朵数量和点的个数至少为 1。")
            return
        if mind > maxd:
            messagebox.showerror("参数错误", "最小距离不能大于最大距离。")
            return

        # 新建黑底图像
        image = Image.new("RGB", (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 为每一朵云生成一组点并绘制圆
        failed = False
        for ci in range(clouds):
            pts = self._generate_points(w, h, n, maxd, mind, rad)
            if pts is None:
                failed = True
                break
            for (x, y) in pts:
                bbox = [x - rad, y - rad, x + rad, y + rad]
                draw.ellipse(bbox, fill=(255, 255, 255))

        if failed:
            messagebox.showwarning(
                "生成失败",
                f"第 {ci+1} 朵云无法满足距离约束。\n"
                "请调整参数后再试。"
            )
            return

        # 显示到界面
        self.tk_image = ImageTk.PhotoImage(image)
        self.image_canvas.config(width=w, height=h)
        self.image_canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        # 保存提示
        # if messagebox.askyesno("保存", "是否将生成的图片保存为 PNG？"):
        #     file_path = filedialog.asksaveasfilename(defaultextension=".png",
        #                                              filetypes=[("PNG 文件", "*.png")])
        #     if file_path:
        #         image.save(file_path, "PNG")
        #         messagebox.showinfo("已保存", f"图片已保存到：\n{file_path}")

    def _generate_points(self, w, h, n, maxd, mind, rad, max_attempts=1000):
        """
        在画布(w,h)内生成 n 个点，满足：
          - 任意两点距离 <= maxd 且 >= mind
          - 以它们为圆心、半径 rad 的圆，都不超出画布边界
        失败时返回 None。
        """
        for attempt in range(max_attempts):
            # 随机选簇中心 C（保证圆不超界）
            cx = random.uniform(rad, w - rad)
            cy = random.uniform(rad, h - rad)
            cluster_r = maxd / 2.0

            pts = []
            for i in range(n):
                theta = random.random() * 2 * math.pi
                r = cluster_r * math.sqrt(random.random())
                x = cx + r * math.cos(theta)
                y = cy + r * math.sin(theta)
                pts.append((x, y))

            # 检查最小/最大距离约束
            good = True
            for i in range(n):
                for j in range(i + 1, n):
                    d = math.hypot(pts[i][0] - pts[j][0],
                                   pts[i][1] - pts[j][1])
                    if d < mind or d > maxd:
                        good = False
                        break
                if not good:
                    break

            if good:
                return pts
        return None  # 超过尝试次数仍未满足

if __name__ == "__main__":
    root = tk.Tk()
    app = CircleCloudApp(root)
    root.mainloop()

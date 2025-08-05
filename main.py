from PIL import Image, ImageDraw, ImageTk
import random
import math
import os
import requests
import time
# 设置参数
image_width = 222
image_height = 640  
point_count = 5
max_dist = 40
min_dist = 10
circle_radius = 25



def generate_image(cloud_count, color):
    # 读取参数
    w = image_width
    h = image_height
    n = point_count
    maxd = max_dist
    mind = min_dist
    rad = circle_radius

    # 参数合法性检查
    if any(v < 0 for v in (w, h, cloud_count, n, maxd, mind, rad)):
        print("参数错误", "请输入非负整数参数。")
        return
    if cloud_count < 1 or n < 1:
        print("参数错误", "云朵数量和点的个数至少为 1。")
        return
    if mind > maxd:
        print("参数错误", "最小距离不能大于最大距离。")
        return

    # 新建透明图像
    image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 为每一朵云生成一组点并绘制圆
    failed = False
    for ci in range(cloud_count):
        pts = _generate_points(w, h, n, maxd, mind, rad)
        if pts is None:
            failed = True
            break
        for (x, y) in pts:
            bbox = [x - rad, y - rad, x + rad, y + rad]
            draw.ellipse(bbox, fill=color)

    if failed:
        print("生成失败",f"第 {ci+1} 朵云无法满足距离约束。\n请调整参数后再试。")
        return

    # 保存
    os.makedirs(os.path.join(os.path.dirname(__file__), "output"), exist_ok=True)
    path_png = os.path.join(os.path.dirname(__file__), "output", "daily.png")
    path_webp = os.path.join(os.path.dirname(__file__), "output", "daily.webp")
    image.save(path_png, "PNG")
    image.save(path_webp, "WEBP")


def _generate_points(w, h, n, maxd, mind, rad, max_attempts=1000):
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

    return None


def get_weather_info(city):
    # 获取城市
    url = f"https://weatherapi.market.xiaomi.com/wtr-v3/location/city/search?name={city}&locale=zh_cn"
    response = requests.get(url)
    city_info = response.json()[0]
    # locationKey = response.json()[0]["locationKey"]
    # 获取城市信息
    # url = f"https://weatherapi.market.xiaomi.com/wtr-v3/location/city/info?locationKey={locationKey}&locale=zh_cn"
    # response = requests.get(url)
    # city_info = response.json()[0]

    print("城市名称:", city_info["name"])
    print("隶属:", city_info["affiliation"])

    # 获取天气信息
    url = "https://weatherapi.market.xiaomi.com/wtr-v3/weather/all"
    # thanks to classisland
    params = {
        "latitude": city_info["latitude"],
        "longitude": city_info["longitude"],
        "locationKey": city_info["locationKey"],
        "days": 15,
        "appKey": "weather20151024",
        "sign": "zUFJoAR2ZVrDy1vF3D07",
        "isGlobal": "false", # 是否使用国际标准
        "locale": "zh_cn",
        "ts": int(time.time())
    }
    response = requests.get(url, params=params)
    # print(response.json())
    weather_code = int(response.json()["current"]["weather"])
    # 参考 https://weather.easyapi.com/code.html
    return weather_code

def get_color(weather_code):
    match weather_code:
        case 0:
            return "#dbdbdb"
        case 1:
            return "#d2d2d2"
        case 2:
            return "#c8c8c8"
        case 3:
            return "#bfbfbf"
        case 4:
            return "#b6b6b6"
        case 5:
            return "#adadad"
        case 6:
            return "#a4a4a4"
        case 7:
            return "#949494"
        case 8:
            return "#838383"
        case 9:
            return "#737373"
        case 10:
            return "#626262"
        case 11:
            return "#525252"
        case _:
            return "#424242"

            



if __name__ == "__main__":
    weather_code = get_weather_info("湛江")
    color = get_color(weather_code)
    cloud_count = weather_code + 2
    print("云朵数量：", cloud_count)
    print("云朵颜色：", color)
    generate_image(cloud_count, color)

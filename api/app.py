# -*- coding:utf-8 -*-
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw
import random
import math
import io
import requests
import api.util
import time

app = FastAPI(docs_url=None, redoc_url=None)

# 设置参数
image_width = 222
image_height = 640  
point_count = 5
max_dist = 40
min_dist = 10
circle_radius = 25

origins = [
    "",
    "blog.hzchu.top",
    "hzchu.top",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _generate_points(w, h, n, maxd, mind, rad, max_attempts=1000):
    """
    在画布(w,h)内生成 n 个点，满足：
      - 任意两点距离 <= maxd 且 >= mind
      - 以它们为圆心、半径 rad 的圆，都不超出画布边界
    失败时返回 None。
    """
    for attempt in range(max_attempts):
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

def generate_image_bytes(cloud_count: int, color: str, fmt: str = "PNG") -> io.BytesIO:
    """
    生成指定数量、指定颜色的“云朵”图片，返回 BytesIO。

    参数:
      cloud_count: 云朵数量
      color: 云朵填充颜色（PIL 能识别的格式）
      fmt: "PNG" or "WEBP"
    """
    # 参数合法性检查
    if any(v < 0 for v in (image_width, image_height, cloud_count, point_count, max_dist, min_dist, circle_radius)):
        raise ValueError("请输入非负整数参数")
    if cloud_count < 1 or point_count < 1:
        raise ValueError("云朵数量和点的个数至少为 1")
    if min_dist > max_dist:
        raise ValueError("最小距离不能大于最大距离")

    # 新建透明图像
    img = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 为每一朵云生成一组点并绘制圆
    for ci in range(cloud_count):
        pts = _generate_points(image_width, image_height, point_count, max_dist, min_dist, circle_radius)
        if pts is None:
            raise RuntimeError(f"第 {ci+1} 朵云无法满足距离约束，请调整参数。")
        for (x, y) in pts:
            bbox = [x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius]
            draw.ellipse(bbox, fill=color)

    # 保存到内存
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf

def get_weather_info(city: str) -> int:
    url = f"https://weatherapi.market.xiaomi.com/wtr-v3/location/city/search?name={city}&locale=zh_cn"
    response = requests.get(url)
    response.raise_for_status()
    city_info = response.json()[0]
    # locationKey = response.json()[0]["locationKey"]
    # 获取城市信息
    # url = f"https://weatherapi.market.xiaomi.com/wtr-v3/location/city/info?locationKey={locationKey}&locale=zh_cn"
    # response = requests.get(url)
    # city_info = response.json()[0]

    url = "https://weatherapi.market.xiaomi.com/wtr-v3/weather/all"
    params = {
        "latitude": city_info["latitude"],
        "longitude": city_info["longitude"],
        "locationKey": city_info["locationKey"],
        "days": 15,
        "appKey": "weather20151024",
        "sign": "zUFJoAR2ZVrDy1vF3D07",
        "isGlobal": "false",
        "locale": "zh_cn",
        "ts": int(time.time())
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    print(response.json())
    weather_code = int(response.json()["current"]["weather"])

    return weather_code

def get_color(weather_code: int) -> str:
    return {
        0: "#dbdbdb",
        1: "#d2d2d2", 
        2: "#c8c8c8", 
        3: "#bfbfbf",
        4: "#b6b6b6", 
        5: "#adadad", 
        6: "#a4a4a4", 
        7: "#949494",
        8: "#838383", 
        9: "#737373", 
        10: "#626262", 
        11: "#525252"
    }.get(weather_code, "#424242")

@app.get("/v1/image")
async def get_image(
    city: str = "",
    format: str = "webp",
    level: str = "city",
    request: Request = None
    ):

    if not city:
        # 如果没传 city，则尝试从 IP 获取
        ip = request.headers.get("x-forwarded-for")
        print("ip:", ip)
        country, region_name, city = api.util.get_city_from_ip(ip)
        print("country:", country)
        print("region_name:", region_name)
        # city = city if city != "" else region_name
        print("city:", city)
    scan_target = {
        "city": city,
        "region": region_name,
        "country": country
    }.get(level, city)

    # 获取天气和配色
    try:
        print("scan_target:", scan_target)
        weather_code = get_weather_info(scan_target)
    except Exception as e:
        raise HTTPException(status_code=502, detail="无法获取天气信息")
    color = get_color(weather_code)
    cloud_count = weather_code + 2

    # 返回 JSON 或 图片
    if format == "json":
        return JSONResponse({
            "scan_target": scan_target,
            "level": level,
            "weather_code": weather_code,
            "color": color,
            "cloud_count": cloud_count
        })
    
    # 直接生成内存图片
    fmt = format.upper()
    if fmt not in ("PNG", "WEBP"):
        fmt = "PNG"

    try:
        img_io = generate_image_bytes(cloud_count, color, fmt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    media_type = "image/png" if fmt == "PNG" else "image/webp"
    return StreamingResponse(img_io, media_type=media_type)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)

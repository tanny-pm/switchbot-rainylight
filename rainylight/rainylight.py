import logging
import os
import re

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

from .switchbot import Switchbot

# Logging
formatter = "[%(levelname)-8s] %(asctime)s %(funcName)s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger(__name__)

load_dotenv(".env")

ACCESS_TOKEN = os.environ["SWITCHBOT_ACCESS_TOKEN"]
SECRET = os.environ["SWITCHBOT_SECRET"]
DEVICE_ID = os.environ["SWITCHBOT_DEVICE_ID"]
CITY_CODE = os.environ["WEATHER_CITY_CODE"]

WEATHER_URL = "https://weather.tsukumijima.net/api/forecast/city"


def get_pm_rainy_percent(city_code: str) -> int:
    """指定した地点の降水確率を取得する"""

    try:
        url = f"{WEATHER_URL}/{city_code}"
        r = requests.get(url)
        r.raise_for_status()
    except RequestException as e:
        logger.error(e)
        return 200

    weather_json = r.json()
    # forecasts 0:今日 1:明日 2:明後日
    rain = weather_json["forecasts"][0]["chanceOfRain"]
    logger.info(f"Chance of rain: {rain}")

    # 降水確率の「%」部分を除去する
    rain_12 = int(re.sub("\\D", "", rain["T12_18"]) or 0)
    rain_18 = int(re.sub("\\D", "", rain["T18_24"]) or 0)

    return max(rain_12, rain_18)


def turn_on_light(
    device_id: str,
    color: tuple[int, int, int] = (0, 0, 0),
    brightness: int = 100,
):
    """指定したパラメーターでカラーライトをオンにする"""

    (r, g, b) = color
    bot = Switchbot(ACCESS_TOKEN, SECRET)

    logger.info(f"Post command: id: {device_id}, rgb: {r}:{g}:{b}")
    try:
        bot.post_command(device_id, "setBrightness", str(brightness))
        res = bot.post_command(device_id, "setColor", f"{r}:{g}:{b}")
        bot.post_command(device_id, "turnOn")
    except Exception as e:
        logger.error(f"Post command error: {e}")

    logger.info(f"Turned on light: {res.json()}")


def main() -> bool:
    """降水確率に基づいてカラーライトの色を変更する"""

    color_list = {
        0: (255, 128, 0),
        10: (210, 148, 0),
        20: (190, 200, 0),
        30: (170, 255, 0),
        40: (153, 204, 255),
        50: (102, 178, 255),
        60: (51, 153, 255),
        70: (0, 128, 255),
        80: (0, 0, 255),
        90: (0, 0, 204),
        100: (0, 0, 153),
    }

    rain = get_pm_rainy_percent(CITY_CODE)
    turn_on_light(DEVICE_ID, color_list.get(rain, (255, 0, 0)))

    return True


if __name__ == "__main__":
    main()

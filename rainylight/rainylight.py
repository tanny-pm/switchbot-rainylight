import base64
import hashlib
import hmac
import json
import logging
import os
import re
import time

import requests
from dotenv import load_dotenv

# Logging
formatter = "[%(levelname)-8s] %(asctime)s %(funcName)s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger(__name__)

# Env
load_dotenv(".env")

ACCESS_TOKEN = os.environ["SWITCHBOT_ACCESS_TOKEN"]
SECRET = os.environ["SWITCHBOT_SECRET"]
DEVICE_ID = os.environ["SWITCHBOT_DEVICE_ID"]
CITY_CODE = os.environ["WEATHER_CITY_CODE"]

API_BASE_URL = "https://api.switch-bot.com"
WEATHER_URL = "https://weather.tsukumijima.net/api/forecast/city"


def get_pm_rainy_percent(city_code: str) -> int:
    """指定した地点の降水確率を取得する"""

    try:
        url = f"{WEATHER_URL}/{city_code}"
        r = requests.get(url)
        # status 2xx以外は例外とする
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return 0

    weather_json = r.json()
    # forecasts 0:今日 1:明日 2:明後日
    rain = weather_json["forecasts"][0]["chanceOfRain"]
    logger.info(f"Chance of rain: {rain}")

    # 降水確率の「%」部分を除去する
    rain_12 = int(re.sub("\\D", "", rain["T12_18"]) or 0)
    rain_18 = int(re.sub("\\D", "", rain["T18_24"]) or 0)

    return max(rain_12, rain_18)


def generate_sign(token: str, secret: str, nonce: str) -> tuple[str, str]:
    """SWITCH BOT APIの認証キーを生成する"""

    t = int(round(time.time() * 1000))
    string_to_sign = "{}{}{}".format(token, t, nonce)
    string_to_sign_b = bytes(string_to_sign, "utf-8")
    secret_b = bytes(secret, "utf-8")
    sign = base64.b64encode(
        hmac.new(secret_b, msg=string_to_sign_b, digestmod=hashlib.sha256).digest()
    )

    return (str(t), str(sign, "utf-8"))


def post_command(
    device_id: str,
    command: str,
    parameter: str = "default",
    command_type: str = "command",
) -> requests.Response:
    """指定したデバイスにコマンドを送信する"""

    nonce = "zzz"
    t, sign = generate_sign(ACCESS_TOKEN, SECRET, nonce)
    headers = {
        "Content-Type": "application/json; charset: utf8",
        "Authorization": ACCESS_TOKEN,
        "t": t,
        "sign": sign,
        "nonce": nonce,
    }
    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/commands"
    data = json.dumps(
        {"command": command, "parameter": parameter, "commandType": command_type}
    )
    try:
        logger.info(f"Post command: {data}")
        r = requests.post(url, data=data, headers=headers)
        logger.info(f"Responce: {r.text}")
    except requests.exceptions.RequestException as e:
        logger.error(e)

    return r


def turn_on_light(
    device_id: str,
    color: tuple[int, int, int] = (0, 0, 0),
    brightness: int = 100,
):
    """指定したパラメーターでカラーライトをオンにする"""

    (r, g, b) = color

    post_command(device_id, "setBrightness", str(brightness))
    post_command(device_id, "setColor", f"{r}:{g}:{b}")
    post_command(device_id, "turnOn")


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

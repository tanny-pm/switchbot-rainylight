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

formatter = "[%(levelname)-8s] %(asctime)s %(name)-12s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger(__name__)

load_dotenv(".env")

ACCESS_TOKEN = os.environ["SWITCHBOT_ACCESS_TOKEN"]
SECRET = os.environ["SWITCHBOT_SECRET"]
DEVICE_ID = os.environ["SWITCHBOT_DEVICE_ID"]
CITY_CODE = os.environ["WEATHER_CITY_CODE"]

API_BASE_URL = "https://api.switch-bot.com"
WEATHER_URL = "https://weather.tsukumijima.net/api/forecast/city"


def get_pm_rainy_percent(city_code: str = CITY_CODE):
    """指定した地点の降水確率を取得する"""

    try:
        url = f"{WEATHER_URL}/{CITY_CODE}"
        r = requests.get(url)
        r.raise_for_status()  # ステータスコード200番台以外は例外とする
        logger.info(r.status_code)
    except requests.exceptions.RequestException as e:
        # print("Error:{}".format(e))
        logger.error(e)

    else:
        weather_json = r.json()
        logger.info(weather_json["forecasts"][0]["chanceOfRain"])  # 0:今日 1:明日 2:明後日

        chance_12 = int(
            re.sub("\\D", "", weather_json["forecasts"][0]["chanceOfRain"]["T12_18"])
            or 0
        )
        chance_18 = int(
            re.sub("\\D", "", weather_json["forecasts"][0]["chanceOfRain"]["T18_24"])
            or 0
        )
        return max(chance_12, chance_18)


def generate_sign(token: str, secret: str, nonce: str = "") -> tuple[str, str, str]:
    """SWITCH BOT APIの認証キーを生成する"""

    t = int(round(time.time() * 1000))
    string_to_sign = "{}{}{}".format(token, t, nonce)
    string_to_sign = bytes(string_to_sign, "utf-8")
    secret = bytes(secret, "utf-8")
    sign = base64.b64encode(
        hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest()
    )

    return (str(t), str(sign, "utf-8"), nonce)


def post_command(
    device_id: str,
    command: str,
    parameter: str = "default",
    command_type: str = "command",
):
    """指定したデバイスにコマンドを送信する"""

    t, sign, nonce = generate_sign(ACCESS_TOKEN, SECRET)
    headers = {
        "Content-Type": "application/json; charset: utf8",
        "Authorization": ACCESS_TOKEN,
        "t": t,
        "sign": sign,
        "nonce": nonce,
    }
    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/commands"
    body = {"command": command, "parameter": parameter, "commandType": command_type}
    data = json.dumps(body)

    try:
        logger.info(data)
        r = requests.post(url, data=data, headers=headers)
        logger.info(r.text)

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


def main():
    """降水確率に基づいてカラーライトの色を変更する"""

    rain = get_pm_rainy_percent()

    if rain == 0:
        turn_on_light(DEVICE_ID, (255, 127, 0))
    elif rain <= 20:
        turn_on_light(DEVICE_ID, (255, 255, 0))
    elif rain <= 40:
        turn_on_light(DEVICE_ID, (127, 255, 0))
    elif rain <= 60:
        turn_on_light(DEVICE_ID, (0, 255, 255))
    elif rain <= 80:
        turn_on_light(DEVICE_ID, (0, 127, 255))
    else:
        turn_on_light(DEVICE_ID, (0, 0, 255))

    return True


if __name__ == "__main__":
    main()

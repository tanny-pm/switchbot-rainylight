import base64
import hashlib
import hmac
import json
import os
import time

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

load_dotenv(".env")

API_BASE_URL = "https://api.switch-bot.com"

ACCESS_TOKEN: str = os.environ["SWITCHBOT_ACCESS_TOKEN"]
SECRET: str = os.environ["SWITCHBOT_SECRET"]


class Switchbot:
    def __init__(self, access_token=None, secret=None):
        self.access_token = access_token or ACCESS_TOKEN
        self.secret = secret or SECRET

    def __generate_request_headers(self) -> dict:
        """SWITCH BOT APIのリクエストヘッダーを生成する"""

        nonce = ""
        t = str(round(time.time() * 1000))
        string_to_sign = "{}{}{}".format(self.access_token, t, nonce)
        string_to_sign_b = bytes(string_to_sign, "utf-8")
        secret_b = bytes(self.secret, "utf-8")
        sign = base64.b64encode(
            hmac.new(secret_b, msg=string_to_sign_b, digestmod=hashlib.sha256).digest()
        )

        headers = {
            "Authorization": self.access_token,
            "t": t,
            "sign": sign,
            "nonce": nonce,
        }

        return headers

    def get_device_list(self) -> dict:
        """SWITCH BOTのデバイスリストを取得する"""

        url = f"{API_BASE_URL}/v1.1/devices"
        try:
            r = requests.get(url, headers=self.__generate_request_headers())
            r.raise_for_status()
        except RequestException as e:
            raise RequestException(e)
        else:
            return r.json()["body"]["deviceList"]

    def get_device_status(self, device_id: str) -> dict:
        """Switchbotデバイスのステータスを取得する"""

        url = f"{API_BASE_URL}/v1.1/devices/{device_id}/status"

        try:
            r = requests.get(url, headers=self.__generate_request_headers())
            r.raise_for_status()
        except RequestException as e:
            raise RequestException(e)
        else:
            return r.json()["body"]

    def post_command(
        self,
        device_id: str,
        command: str,
        parameter: str = "default",
        command_type: str = "command",
    ) -> requests.Response:
        """指定したデバイスにコマンドを送信する"""

        url = f"{API_BASE_URL}/v1.1/devices/{device_id}/commands"
        data = json.dumps(
            {"command": command, "parameter": parameter, "commandType": command_type}
        )
        try:
            r = requests.post(url, data=data, headers=self.__generate_request_headers())
        except RequestException as e:
            raise RequestException(e)
        else:
            return r


if __name__ == "__main__":
    # デバイスリストをjsonファイルに出力する
    bot = Switchbot()
    device_list = bot.get_device_list()

    with open("./device_list.json", "w") as f:
        f.write(json.dumps(device_list, indent=2, ensure_ascii=False))

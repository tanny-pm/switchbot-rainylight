# switchbot-rainylight

【SwitchBot】雨が降りそうなときに廊下ライトの色を変えてお知らせする機能を作る

https://zenn.dev/tanny/articles/808487545eb30f

## ローカルでの実行手順

- `.env`ファイルに環境変数を登録する。

```env:.env.example
SWITCHBOT_ACCESS_TOKEN=
SWITCHBOT_SECRET=
SWITCHBOT_DEVICE_ID=
WEATHER_CITY_CODE=
```

- パッケージをインストールする。

```sh
pipenv
$ pipenv install

pip
$ pip install -r requirements.txt
```

- モジュールを実行する。

```sh
$ python -m rainylight
```

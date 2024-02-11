#!/bin/bash

# requirements.txtを出力する
pipenv requirements > requirements.txt

# GCPにアップロードするzipファイルを生成する
zip -r gcp_source.zip main.py requirements.txt rainylight
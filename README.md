Cinderella
===
[![lint and test](https://github.com/daniel0076/Cinderella/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/daniel0076/Cinderella/actions/workflows/main.yml)

自動化帳單分析，搭配 BeanCount 實現全自動記帳

## Introduction

[Beancount](https://github.com/beancount/beancount) 是一個純文字檔[複式記帳](https://zh.wikipedia.org/wiki/复式簿记)工具。網路上有關複式記帳的特性及好處文章眾多，在此不再贅述。和 Beancount 有關的簡介和使用方式可以參考他的 [文件](https://beancount.github.io/docs/) 和 [CheatSheet](https://beancount.github.io/docs/beancount_cheat_sheet.html)，選用 BeanCount 除了他是開源複式記帳工具，也因為他是純文字檔記錄，單純且容易以程式自動化，且能以 [Fava](https://github.com/beancount/fava) 來視覺化。

**Cinderella** 能夠自動分析銀行的帳戶、信用卡對帳單，和電子發票記錄，**並依照使用者定義的關鍵字分類開銷歸戶**。最後產生 BeanCount 格式檔案。可以先參考 [Fava Demo](https://fava.pythonanywhere.com)。

## 支援

### 支援的金融機構

目前支援自動分析下列機構對帳單，未來會繼續增加。歡迎直接 PR 或 Feature Request

每個機構帶有一個 **source name**，用於識別


| 金融機構         | 帳戶對帳單  | 信用卡      | **source name**   | 備註 |
| -----------      | ----------- | ----------- | -----------       | ----------- |
| 財政部電子發票   | ✅ (csv)    |➖           | `receipt`         | 每月寄的匯整通知  |
| 中華郵政         | ✅ (csv)    |❌           | `post`            | 網銀下載           |
| 台新 Richart     | 🛠 (xlsx)   |🛠 (xlsx)    | `richart`         | Richart App 匯出 |
| 永豐銀行         | 📋 (csv)    |✅ (csv)     | `sinopac`         | 網銀下載   |
| 玉山銀行         | 🛠 (excel)  |❌           | `esun`            | 網銀下載|
| 國泰世華         | ✅ (csv)    |✅ (csv)     | `cathay`          | 網銀下載           |
| 中國信託         | ✅ (csv)    |❌           | `ctbc`            | 網銀下載 |


> ✅下載後直接支援 | ❌目前不支援 | 🛠下載後需經 Cinderella Pipeline 處理 | 📋需手動複製網銀表格後貼上


### 支援帳單的種類

每種帳單帶有一個 **帳單識別字**，用於同間機構但是不同格式的對帳單

+ 銀行帳戶對帳單：`bank`
+ 信用卡對帳單：`card`


## 使用

### 系統需求

+ `Python`  >= 3.10
+ 目前只在 `macOS Ventra`, `Ubuntu 22.04` 上測試

### 安裝

+ 下載專案
```bash
git clone https://github.com/daniel0076/Cinderella
```

+ 安裝 Python packages (推薦使用 [pipenv](https://pipenv.pypa.io/en/latest/))
+ 在專案目錄下
```bash
pipenv install
pipenv shell
```
或 (使用 [virtualenv](https://virtualenv.pypa.io/en/latest/) 等)
```bash
pip install -r requirements.txt
```

### 準備對帳單

1. 建立 **對帳單資料夾** (例 `statements`，可用任意名稱)，並把對帳單檔案放入資料夾
1. 依對帳單的金融機構，將 **帳單識別字** 及 **source name** 加入對帳單的**資料夾名或檔名**，二個識別字需在資料夾或檔名(檔案路徑)中。例如
    + `statements/bank/receipt-202101.csv`
    + `statements/card/cathay-202101.csv`
1. 範例對帳單資料夾
```bash
statements
|-- card
|   |-- cathay-202101.csv
|-- bank
    |-- receipt-202101.csv
```
4. 在 `examples/` 有範例 config 和 bean 輸出資料夾
 + 修改 `examples/configs/cinderella_sample.json`
   + `statements_directory` 指向對帳單資料夾
   + `output_directory` 指向 `examples/beans`，為 BeanCount 記帳輸出資料夾

### 執行

```bash
python3 main.py -dv -c examples/configs/cinderella_sample.json
fava examples/beans/main.bean  # 啟動 GUI，在 localhost:5000
```

### 自訂消費項目分類(歸戶)

Cinderella 能夠依照使用者提供的關鍵字在對帳單項目中比對，將某筆收支歸戶到自定義的類別下

設定存放於設定中的 `mappings` 欄位: [範例](https://github.com/daniel0076/Cinderella/tree/main/Cinderella/examples/configs/cinderella_sample.json)

+ 通用歸類 (`general`)：收錄了常用的歸類，可照需求自行修改
+ 特用歸類：按照 **source name** 為 key ，提供了針對不同金融機構的歸類關鍵字，只用於該金融機構對帳單。

**Cinderella 將優先使用特用的歸類項目**，且檔案越上面的項目優先度越高。關鍵字支援 regex expression

## 後記

Cinderella?

小時候看灰姑娘一直記得 Cinderella 有挑豆子的橋段。不過問了身邊朋友，很少人對這段有印象。[但 Cinderella 真的有挑豆子的?](https://sites.pitt.edu/~dash/grimm021.html)不論如何，就讓 Cinderella 來幫我們做 bean counting 吧

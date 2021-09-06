Cinderella
===
[![lint and test](https://github.com/daniel0076/Cinderella/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/daniel0076/Cinderella/actions/workflows/main.yml)

自動化帳單分析，搭配 BeanCount 實現全自動記帳

## Introduction

[Beancount](https://github.com/beancount/beancount) 是一個純文字檔[複式記帳](https://zh.wikipedia.org/wiki/复式簿记)工具。網路上有關複式記帳的特性及好處文章眾多，在此不再贅述。和 Beancount 有關的簡介和使用方式可以參考他的 [文件](https://beancount.github.io/docs/) 和 [CheatSheet](https://beancount.github.io/docs/beancount_cheat_sheet.html)，選用 BeanCount 除了他是開源複式記帳工具，也因為他是純文字檔記錄，單純且容易以程式自動化，且能以 [Fava](https://github.com/beancount/fava) 來視覺化。

**Cinderella** 能夠自動分析銀行的帳戶、信用卡對帳單，和電子發票記錄，**並依照使用者定義的關鍵字分類開銷歸戶**。最後產生 BeanCount 格式檔案。可以先參考 [Fava Demo](https://fava.pythonanywhere.com)。

## 支援

### 支援的金融機構

目前支援自動分析下列機構對帳單，未來會繼續增加。歡迎直接 PR 或 Feature Request (如果我有空的話)

每個機構帶有一個 **Cinderella 識別字**，用於識別一個金融機構的分析 script


| 金融機構         | 帳戶對帳單  | 信用卡     | **Cinderella 識別字**  | 備註 |
| -----------     | ----------- | ----------- | ----------- | ----------- |
| 財政部電子發票    | ✅ (csv)  |➖         | `receipt`         | 每週/月寄的匯整通知  |
| 中華郵政         | ✅ (csv)  |❌         | `post`            | 網銀下載           |
| 台新銀行(Richart)| ✅ (excel)|✅ (excel) | `taishin`         | 網銀/APP下載 |
| 永豐銀行         | ✅ (csv)* |✅ (csv)   | `sinopac`         | 網銀下載   |
| 玉山銀行         | ✅ (excel)|🚀         | `esun`            |手動 xls->xlsx|
| 國泰世華         | ✅ (csv)  |✅ (csv)   | `cathay`          | 網銀下載           |
| 中國信託         | 🚀        |🚀         |                   |                   |

> 🚀: 已規劃支援

> *：需手動複製網銀表格後貼上


### 支援帳單的種類

每種帳單帶有一個 **帳單識別字**，用於同間機構但是不同格式的對帳單

+ 銀行帳戶對帳單：`bank`
+ 信用卡對帳單：`card`
+ 證券對帳單：🚀

> 🚀: 已規劃支援


## 使用

### 系統需求

+ `Python`  >= 3.9
+ 目前只在 `macOS Big Sur` 上測試

### 安裝

+ 下載專案
```
git clone https://github.com/daniel0076/Cinderella
```

+ 安裝 Python packages (推薦使用 [pipenv](https://pipenv.pypa.io/en/latest/))
+ 在專案目錄下
```
pipenv install
pipenv shell
```
或 (使用 [virtualenv](https://virtualenv.pypa.io/en/latest/) 等)
```
pip install -r requirements.txt
```

### 準備對帳單

1. 建立 **對帳單資料夾** (例 `statements`，可用任意名稱)，並把對帳單檔案放入資料夾
2. 依對帳單的金融機構，將 **帳單識別字** 及 **Cinderella 識別字** 加入對帳單的資料夾名或檔名，二個識別字需在資料夾或檔名(檔案路徑)中。例如
    + 台新銀行的帳戶對帳單 (以下都是合法的) ✅：
        + `statements/taishin/bank-202101.csv`
        + `statements/bank/taishin-202101.csv`
        + `statements/taishin-bank-2021.csv`
        + `statements/taishin/bank/2021.csv`
    + 永豐銀行的信用卡對帳單 (以下都是合法的) ✅：
        + `statements/sinopac/card-2021.csv`
        + `statements/card/sinopac-2021.csv`
        + `statements/sinopac-card-2021.csv`
        + `statements/card/sinopac/2021.csv`
    + 以下是不合法的 ❌ ：
        + `statements/card/2021.csv`：缺少 **Cinderella 識別字**
        + `statements/sinopac/2021.csv`：缺少 **帳單識別字**

3. 範例對帳單資料夾
```
statements
|-- card
|   |-- taishin-2021.excel
|
|-- bank
    |-- sinopac-202108.csv
```

4. 往後只要把新的對帳單放入相應資料夾，Cinderella 會批次處理
5. 建立 BeanCount 資料夾
 + 比如 `beans`
 + 修改 `main.bean` 去讀取不同資料夾中的 `bean` 檔案

### 執行

```
python3 main.py PATH_TO_STATEMENTS PATH_TO_BEANCOUNT
fava main.bean  # 啟動 GUI，在 localhost:5000
```
+ 範例


```
python3 main.py ./statements ./beans
fava main.bean  # 啟動 GUI，在 localhost:5000
```

### 自訂消費項目分類(歸戶)

Cinderella 能夠依照使用者提供的關鍵字在對帳單項目中比對，將某筆收支歸戶到自定義的類別下

Cinderella 的 [`configs/mappings`](https://github.com/daniel0076/Cinderella/tree/main/Cinderella/configs/mappings.sample) 資料夾下存放了自訂的關鍵字和對應的類別

+ 通用歸類：[`general.json`](https://github.com/daniel0076/Cinderella/tree/main/Cinderella/configs/mappings.sample/general.json)，收錄了常用的歸類，可照需求自行修改
+ 特用歸類：其它按照 **Cinderella 識別字** 命名的檔案，提供了針對不同金融機構的歸類關鍵字，只用該金融機構對帳單。

**Cinderella 將優先使用特用的歸類項目**，且檔案越上面的項目優先度越高

## 後記

Cinderella?

小時候看灰姑娘一直記得 Cinderella 有挑豆子的橋段。不過問了身邊好多朋友，都沒有人對這段有印象。[但 Cinderella 真的有挑豆子的?](https://sites.pitt.edu/~dash/grimm021.html)不論如何，就讓 Cinderella 來幫我們做 bean counting 吧

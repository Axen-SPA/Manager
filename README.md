# AxenSystem Manager
タスクマネージャーはもう古い。  
新時代のシステム管理を、軽量・高速・高情報密度で。

AxenSystem Manager は Windows の状態を高速かつ正確に可視化するための  
次世代システム管理ツールです。

---

## 特徴
- 120FPS のリアルタイムモニタリング
- CPU / メモリ / ディスク / ネットワークの高速グラフ描画
- プロセス一覧（CPU順 / メモリ / スレッド / ハンドル / 実行パス）
- ハードウェア情報（CPU / メモリ / GPU / ディスク / NIC）
- ソフトウェア情報（OS / Python / 起動時間）
- インストール済みアプリ一覧
- スプラッシュ画面（splash.png）
- About画面（about.png）
- 全アイコンを icon.ico に統一

---

## ビルド方法（PyInstaller）
pyinstaller ^
--noconfirm ^
--onefile ^
--windowed ^
--icon=icon.ico ^
--add-data "splash.png;." ^
--add-data "about.png;." ^
--add-data "icon.ico;." ^
axensystem_manager.py


---

## 必要ファイル
- axensystem_manager.py  
- splash.png  
- about.png  
- icon.ico  

---

## 公式サイト
https://axen.jp

---

## 開発者
haru


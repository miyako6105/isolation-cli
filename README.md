# Isolation エージェント作成
## ディレクトリ構成
```
isolation/
├── core/
│   ├── board.py # 盤面の状態とルール
|   ├── evaluation.py # 盤面評価の関数
│   └── game.py  # ゲーム進行の制御
├── agents/
│   ├── base.py # 全エージェントが従う抽象基底クラス
|   ├── simple.py # 単純な評価によるエージェント
│   └── human.py # 人間(player)
├── cli/
│   └── play.py # CLIアプリ本体
├── eval/
│   └── tournament.py  # エージェント同士の総当たり
└── tests/
```
## ライブラリのインストール
requirements.txt に必要ならイブラリを追加している。以下、もしくはそれに類するコマンドでインストールする。
```
pip install -r requirements.txt
```
## 遊び方
本ディレクトリで以下を実行
```
python -m cli.play
```
起動後、

①モードの選択 ②盤面サイズの指定 ③CPUの制御手法の選択

の順番で問われるので設定する。(コンソール上で)
### モードの選択
3つのモードから選択可能

1. Human vs Human (対人戦)
    - 人同士で対局するモード
2. Human vs CPU (対コンピュータ戦)
    - コンピュータと対戦するモード
    - CPUの制御手法は選択可能
3. CPU vs CPU (コンピュータ同士の対戦シミュレーション)
### 盤面
任意の正の整数の盤面を指定可能。但しサイズが大きすぎると動かないかもしれない。

### 選択可能なCPUの制御方法
- random（完全ランダム）
- greedy-mobility（1手で移動可能なマスの数差を評価値とする）
- greedy-reachable（現時点のマスから到達可能な全てのマスの数の差を評価値とする）
- greedy-voronoi（ボロノイ分割で近いマスの数の差を評価値とする）
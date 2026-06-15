# Isolation CLI
ボードゲーム「Isolation」をコマンドライン上で遊べるプログラムです。
最終的には強いAgentを作り、それらで天下一武道会がしたいです。
## ディレクトリ構成
```
isolation-cli/
├── core/
│   ├── board.py                # 盤面の状態とルール
|   ├── evaluation.py           # 盤面評価の関数
│   └── game.py                 # ゲーム進行の制御
├── agents/
│   ├── base.py                 # 全エージェントが従う抽象基底クラス
|   ├── *-agent.py              # 各評価によるエージェント
│   └── human.py                # 人間(player)
├── cli/
│   └── play.py                 # CLIアプリ本体
├── eval/
|   ├── run_demo.py             # 総当たり戦
|   ├── run_search.py           # 強い奴を探すスクリプト（の予定）
│   └── tournament.py           # エージェント同士の総当たり用スクリプト
└── tests/
```
## ライブラリのインストール
requirements.txt に必要ならイブラリが書かれています。以下、もしくはそれに類するコマンドでインストールしてください。
```
pip install -r requirements.txt
```
## 遊び方
本ディレクトリで以下を実行してください。
```
python -m cli.play
```
起動後、

①モードの選択 ②盤面サイズの指定 ③CPUの制御手法の選択

の順番で問われるので設定します。(コンソール上で)
### モードの選択
3つのモードから選択可能です。

1. Human vs Human (対人戦)
    - 人同士で対局するモード
2. Human vs CPU (対コンピュータ戦)
    - コンピュータと対戦するモード
    - CPUの制御手法は選択可能
3. CPU vs CPU (コンピュータ同士の対戦シミュレーション)
### 盤面サイズ
任意の正の整数の盤面サイズを指定可能。但しサイズが大きすぎると動かないかもしれません。
盤面の表示は、列数が1桁の時にきれいに並ぶように作ってあります。（行数は任意の数に対応）

### 選択可能なCPUの制御方法
- random（完全ランダム）

## 対戦シミュレーション
各エージェントを戦わせ、強いエージェントを決めることができます。スクリプトは "eval/run_demo.py" と "eval/run_search.py" で、run_demo.py では総当たり戦で勝率を競います。run_search.py は、最強のエージェントを決める、所謂「天下一武道会」みたいな感じです。
### 実行方法
- run_demo.py
```
python -m eval/run_demo.py
```
- run_search.py
```
python -m eval/run_search.py
```
## エージェントの追加方法
本リポジトリにおいて、エージェントは満たすべき基底クラス（"agents/base.py" の Agents クラス）に従っていれば、独自のエージェントを対戦用CPUに組み込むことができます。

CLIアプリ上のCPUで利用可能にするためには、作成したエージェントを "agents"ディレクトリに配置し、 "cli/play.py" 内で import、14行目の "CPU_CHOICES" と 22 行目からの "build_cpu" 関数にそれぞれ自作エージェント用の処理を追加してください。
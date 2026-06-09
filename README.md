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
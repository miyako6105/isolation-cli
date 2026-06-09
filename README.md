# Isolation エージェント作成
## ディレクトリ構成
```
isolation/
├── core/
│   ├── board.py # 盤面の状態とルール
│   └── game.py  # ゲーム進行の制御
├── agents/
│   ├── base.py # 全エージェントが従う抽象基底クラス
│   ├── random_agent.py
│   ├── greedy_agent.py
│   ├── minimax_agent.py
│   ├── mcts_agent.py
│   └── rl_agent.py
├── cli/
│   └── play.py # CLIアプリ本体
├── eval/
│   └── tournament.py  # エージェント同士の総当たり
└── tests/
```
## ゲームのコア部分

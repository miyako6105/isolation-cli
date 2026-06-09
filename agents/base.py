"""
全プレイヤー（人間・ランダム・貪欲・将来のMinimax/MCTS/RL）が従う
共通インターフェース
"""
from abc import ABC, abstractmethod

class Agent(ABC):
    """
    エージェントの抽象基底クラス
    すべてのエージェントはこのクラスを継承し、select_move メソッドを実装する必要がある。
    """

    def __init__(self, name=None):
        # 名前の設定、ログや対戦表での識別に使用する
        # 名前を省略したらクラス名を既定にする
        self.name = name or self.__class__.__name__

    @abstractmethod
    def select_move(self, state):
        """
        状態 state を受け取り、打つ手 (dest, remove_cell) を返す

        返す手は必ず state.legal_moves() に含まれるものであること。
        合法手が無い状態（終局）で呼ばれることはない前提
        （呼ぶ側のゲームループが終局を先に判定する）。
        """
        ...

    def __repr__(self):
        # デバッグやログで見やすいように、クラス名と名前を表示する
        return f"{self.__class__.__name__}(name={self.name!r})"
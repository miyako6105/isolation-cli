"""
弱いエージェント2種。全実験のベースライン（最低ライン）になる。
  RandomAgent : 合法手から一様ランダムに選ぶ。最弱の基準点。
  GreedyAgent : 1手先だけ見て、評価関数が最大になる手を選ぶ。
"""
import random
from agents.base import Agent
from core.evaluation import get_evaluation_function

# MARK: RandomAgent
class RandomAgent(Agent):
    """
    合法手から一様ランダムに1手選ぶ。
    """
    def __init__(self, name=None, seed=None):
        super().__init__(name)
        # エージェントごとに独立した乱数源を持つ。
        # グローバルな random を汚さないことで、再現性を確保する。
        self._rng = random.Random(seed)

    def select_move(self, state):
        return self._rng.choice(state.legal_moves())

# MARK: GreedyAgent
class GreedyAgent(Agent):
    """
    1手先読みの貪欲法。

    全合法手を試し、その手を打った直後の状態を評価関数で測り、
    自分にとって最も有利な手を選ぶ。
    """
    def __init__(self, name=None, evaluation="mobility", seed=None):
        super().__init__(name)
        self._eval = get_evaluation_function(evaluation)   # 評価関数を差し替え可能に
        self._eval_name = evaluation
        self._rng = random.Random(seed)           # 同点手のタイブレーク用

    def select_move(self, state):
        me = state.turn  # 今から打つのが自分。この視点を固定する。
        best_value = None
        best_moves = []
        for move in state.legal_moves():
            nxt = state.apply_move(move)
            value = self._eval(nxt, player=me)    # 自分視点で評価
            if best_value is None or value > best_value:
                best_value = value
                best_moves = [move]
            elif value == best_value:
                best_moves.append(move)           # 同点はためておく
        # 同点の手が複数あればランダムに1つ選ぶ（偏りを避ける）
        return self._rng.choice(best_moves)

    def __repr__(self):
        return (f"GreedyAgent(name={self.name!r}, "
                f"evaluation={self._eval_name!r})")
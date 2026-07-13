import math
import random
from agents.base import Agent
from agents.search_mcts import mcts_best_move, random_playout


class MCTSAgent(Agent):
    """
    モンテカルロ木探索で手を選ぶエージェント
    Args:
        time_limit: 1手あたりの思考時間(秒)。
        c         : UCB1 の探索定数(既定 sqrt(2))。
        playout   : プレイアウト方策(既定は一様ランダム)。差し替え可能。
    """

    def __init__(self, name=None, time_limit=10.0, c=math.sqrt(2),
                 playout=random_playout, seed=None):
        super().__init__(name or f"MCTS(t={time_limit}s)")
        self.time_limit = time_limit
        self.c = c
        self._playout = playout
        self._rng = random.Random(seed)
        self.last_info = None   # 直近探索の情報(iterations 等)

    def select_move(self, state):
        move, info = mcts_best_move(
            state, time_limit=self.time_limit, c=self.c,
            playout=self._playout, rng=self._rng)
        self.last_info = info
        return move

    def __repr__(self):
        return (f"MCTSAgent(name={self.name!r}, "
                f"time_limit={self.time_limit}, c={self.c:.3f})")
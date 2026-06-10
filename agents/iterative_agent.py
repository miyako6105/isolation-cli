import random
from agents.base import Agent
from agents.search_iterative import iterative_deepening_best_move
from core.evaluation import get_evaluation_function


class IterativeDeepeningAgent(Agent):
    """
    時間制限つき反復深化 alpha-beta エージェント。
    """
    def __init__(self, name=None, time_limit=1.0, evaluation="voronoi",
                 seed=None):
        super().__init__(name or f"IDDFS(t={time_limit}s,{evaluation})")
        self.time_limit = time_limit
        self._eval = get_evaluation_function(evaluation)
        self._eval_name = evaluation
        self._rng = random.Random(seed)
        self.last_info = None   # 直近の探索情報(depth/value/elapsed)

    def select_move(self, state):
        move, info = iterative_deepening_best_move(
            state, evaluate=self._eval,
            time_limit=self.time_limit, rng=self._rng)
        self.last_info = info
        return move

    def __repr__(self):
        return (f"IterativeDeepeningAgent(name={self.name!r}, "
                f"time_limit={self.time_limit}, "
                f"evaluation={self._eval_name!r})")
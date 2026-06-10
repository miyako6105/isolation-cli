import random
from agents.base import Agent
from agents.search_minimax import minimax_best_move
from core.evaluation import get_evaluation_function


class MinimaxAgent(Agent):
    """
    固定深さのミニマックスで手を選ぶエージェント。
    Args:
        depth: 読みの深さ(根の自分の手を1手目として、合計何層読むか)。
               depth=1 は実質「1手先の評価」= 貪欲とほぼ同じ。
               depth=2 で「自分の手→相手の応手」まで読む。
        evaluation: 葉で使う評価関数名 ("mobility"/"reachable"/"voronoi")。
    """

    def __init__(self, name=None, depth=2, evaluation="voronoi", seed=None):
        super().__init__(name or f"Minimax(d={depth},{evaluation})")
        self.depth = depth
        self._eval = get_evaluation_function(evaluation)
        self._eval_name = evaluation
        self._rng = random.Random(seed)

    def select_move(self, state):
        move, _value = minimax_best_move(
            state, depth=self.depth, evaluate=self._eval, rng=self._rng)
        
        return move

    def __repr__(self):
        return (f"MinimaxAgent(name={self.name!r}, depth={self.depth}, "
                f"evaluation={self._eval_name!r})")
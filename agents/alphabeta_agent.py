import random
from agents.base import Agent
from agents.search_alphabeta import alphabeta_best_move
from core.evaluation import get_evaluation_function
class AlphaBetaAgent(Agent):
    """
    固定深さのアルファ・ベータ探索で手を選ぶエージェント
    """
    def __init__(self, name=None, depth=2, evaluation="voronoi", seed=None):
        super().__init__(name or f"AlphaBeta(d={depth},{evaluation})")
        self.depth = depth
        self._eval = get_evaluation_function(evaluation)
        self._eval_name = evaluation
        self._rng = random.Random(seed)

    def select_move(self, state):
        move, _value = alphabeta_best_move(
            state, depth=self.depth, evaluate=self._eval, rng=self._rng)
        return move

    def __repr__(self):
        return (f"AlphaBetaAgent(name={self.name!r}, depth={self.depth}, "
                f"evaluation={self._eval_name!r})")

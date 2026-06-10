"""
評価基盤のデモ実行: 貪欲勢の総当たり
このスクリプトを実行すると、ランダムエージェントと3種類の貪欲エージェントが総当たりで対戦し、ランキングと勝率行列が表示される。
"""
from eval.tournament import register, run_tournament, format_ranking, format_win_matrix, AGENT_REGISTRY
from agents.simple import RandomAgent, GreedyAgent
from agents.minimax_agent import MinimaxAgent
from agents.alphabeta_agent import AlphaBetaAgent
from agents.iterative_agent import IterativeDeepeningAgent

AGENT_REGISTRY.clear()
register("random",       lambda s: RandomAgent(name="random", seed=s))
register("greedy-mob",   lambda s: GreedyAgent(name="greedy-mob", evaluation="mobility", seed=s))
register("greedy-reach", lambda s: GreedyAgent(name="greedy-reach", evaluation="reachable", seed=s))
register("greedy-vor",   lambda s: GreedyAgent(name="greedy-vor", evaluation="voronoi", seed=s))
register("minimax-mob",   lambda s: MinimaxAgent(name="minimax-mob", depth=2, evaluation="mobility", seed=s))
register("alphabeta-mob", lambda s: AlphaBetaAgent(name="alphabeta-mob", depth=2, evaluation="mobility", seed=s))
register("iterative-mob", lambda s: IterativeDeepeningAgent(name="iterative-mob", time_limit=1.0, evaluation="mobility", seed=s))
register("minimax-reach",   lambda s: MinimaxAgent(name="minimax-reach", depth=2, evaluation="reachable", seed=s))
register("alphabeta-reach", lambda s: AlphaBetaAgent(name="alphabeta-reach", depth=2, evaluation="reachable", seed=s))
register("iterative-reach", lambda s: IterativeDeepeningAgent(name="iterative-reach", time_limit=1.0, evaluation="reachable", seed=s))
register("minimax-vor",   lambda s: MinimaxAgent(name="minimax-vor", depth=2, evaluation="voronoi", seed=s))
register("alphabeta-vor", lambda s: AlphaBetaAgent(name="alphabeta-vor", depth=2, evaluation="voronoi", seed=s))
register("iterative-vor", lambda s: IterativeDeepeningAgent(name="iterative-vor", time_limit=1.0, evaluation="voronoi", seed=s))


res = run_tournament(n_games=20, width=5, height=5, base_seed=1221)
print(format_ranking(res))
print()
print(format_win_matrix(res))
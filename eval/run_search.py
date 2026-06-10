"""
探索エージェントの武道会: 軽い×深い 対 賢い×浅い を測る
"""
from eval.tournament import register, run_tournament, format_ranking, format_win_matrix, AGENT_REGISTRY
from agents.simple import GreedyAgent
from agents.iterative_agent import IterativeDeepeningAgent

AGENT_REGISTRY.clear()
# 同じ思考時間(0.3秒)を全探索エージェントに与え、評価関数だけ変える。
# 「軽くて深い mobility」対「賢くて浅い voronoi」を公平に比較する。
register("greedy-vor",  lambda s: GreedyAgent(name="greedy-vor", evaluation="voronoi", seed=s))
register("iddfs-mob",   lambda s: IterativeDeepeningAgent(name="iddfs-mob", time_limit=0.3, evaluation="mobility", seed=s))
register("iddfs-reach", lambda s: IterativeDeepeningAgent(name="iddfs-reach", time_limit=0.3, evaluation="reachable", seed=s))
register("iddfs-vor",   lambda s: IterativeDeepeningAgent(name="iddfs-vor", time_limit=0.3, evaluation="voronoi", seed=s))

# 探索は重いので局数は控えめ、盤は5x5
res = run_tournament(n_games=4, width=3, height=3, base_seed=0)
print(format_ranking(res))
print()
print(format_win_matrix(res))
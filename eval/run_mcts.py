from eval.tournament import register, run_tournament, format_ranking, format_win_matrix, AGENT_REGISTRY
from agents.simple import GreedyAgent
from agents.iterative_agent import IterativeDeepeningAgent
from agents.mcts_agent import MCTSAgent

AGENT_REGISTRY.clear()
# 全員に同じ思考時間 0.3秒 を与えて公平に比較する
register("greedy-vor", lambda s: GreedyAgent(name="greedy-vor", evaluation="voronoi", seed=s))
register("iddfs-mob",  lambda s: IterativeDeepeningAgent(name="iddfs-mob", time_limit=0.3, evaluation="mobility", seed=s))
register("iddfs-vor",  lambda s: IterativeDeepeningAgent(name="iddfs-vor", time_limit=0.3, evaluation="voronoi", seed=s))
register("mcts",       lambda s: MCTSAgent(name="mcts", time_limit=0.3, seed=s))

res = run_tournament(n_games=12, width=5, height=5, base_seed=0)
print(format_ranking(res))
print()
print(format_win_matrix(res))
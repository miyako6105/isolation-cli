"""
評価基盤のデモ実行: 貪欲勢の総当たり
このスクリプトを実行すると、ランダムエージェントと3種類の貪欲エージェントが総当たりで対戦し、ランキングと勝率行列が表示される。
"""
from eval.tournament import register, run_tournament, format_ranking, format_win_matrix, AGENT_REGISTRY
from agents.simple import RandomAgent, GreedyAgent

AGENT_REGISTRY.clear()
register("random",       lambda s: RandomAgent(name="random", seed=s))
register("greedy-mob",   lambda s: GreedyAgent(name="greedy-mob",   evaluation="mobility",  seed=s))
register("greedy-reach", lambda s: GreedyAgent(name="greedy-reach", evaluation="reachable", seed=s))
register("greedy-vor",   lambda s: GreedyAgent(name="greedy-vor",   evaluation="voronoi",   seed=s))

res = run_tournament(n_games=40, width=5, height=5, base_seed=0)
print(format_ranking(res))
print()
print(format_win_matrix(res))
"""プレイアウト方策の比較実験: 同じ思考時間でどれが強いか。"""
from eval.tournament import register, run_tournament, format_ranking, format_win_matrix, AGENT_REGISTRY
from agents.mcts_agent import MCTSAgent
from agents.search_mcts import random_playout, make_greedy_playout, make_epsilon_greedy_playout
 
AGENT_REGISTRY.clear()
tl = 1.0 # 1手あたりの思考時間(秒)を指定する。
# 全員 MCTS、思考時間0.3秒で固定。プレイアウト方策だけ変える。
register("mcts-random", lambda s: MCTSAgent(name="random", time_limit=tl,
                                            playout=random_playout, seed=s))
register("mcts-greedy", lambda s: MCTSAgent(name="greedy", time_limit=tl,
                                            playout=make_greedy_playout("voronoi"), seed=s))
register("mcts-eps0.3", lambda s: MCTSAgent(name="eps0.3", time_limit=tl,
                                            playout=make_epsilon_greedy_playout("voronoi", 0.3), seed=s))
register("mcts-eps0.1", lambda s: MCTSAgent(name="eps0.1", time_limit=tl,
                                            playout=make_epsilon_greedy_playout("voronoi", 0.1), seed=s))
register("mcts-eps0.5", lambda s: MCTSAgent(name="eps0.5", time_limit=tl,
                                            playout=make_epsilon_greedy_playout("voronoi", 0.5), seed=s))

register("mcts-eps0.7", lambda s: MCTSAgent(name="eps0.7", time_limit=tl,
                                            playout=make_epsilon_greedy_playout("voronoi", 0.7), seed=s))
 
res = run_tournament(n_games=16, width=7, height=7, base_seed=1221)
print(format_ranking(res))
print()
print(format_win_matrix(res))
 
# 各エージェントの平均試行回数も覗く(1手だけサンプリング)
print()
print("=== 参考: 0.3秒での試行回数(7x7初期, 1手) ===")
from core.board import initial_state
import random
s0 = initial_state(7, 7)
for name in ["mcts-random", "mcts-greedy", "mcts-eps0.3", "mcts-eps0.1", "mcts-eps0.5", "mcts-eps0.7"]:
    ag = AGENT_REGISTRY[name](0)
    ag.select_move(s0)
    print(f"  {name}: {ag.last_info['iterations']} 回")
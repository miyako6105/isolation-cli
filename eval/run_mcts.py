from eval.tournament import register, run_tournament, format_ranking, format_win_matrix, AGENT_REGISTRY
from agents.mcts_agent import MCTSAgent
from agents.search_mcts import random_playout, make_greedy_playout, make_epsilon_greedy_playout
from core.board import initial_state
import random

AGENT_REGISTRY.clear()
# 全員 MCTS、思考時間0.3秒で固定。プレイアウト方策だけ変える。
register("mcts-random", lambda s: MCTSAgent(name="mcts-random", time_limit=0.3,
                                            playout=random_playout, seed=s))
register("mcts-greedy", lambda s: MCTSAgent(name="mcts-greedy", time_limit=0.3,
                                            playout=make_greedy_playout("mobility"), seed=s))
register("mcts-eps0.3", lambda s: MCTSAgent(name="mcts-eps0.3", time_limit=0.3,
                                            playout=make_epsilon_greedy_playout("mobility", 0.3), seed=s))

res = run_tournament(n_games=12, width=5, height=5, base_seed=0)
print(format_ranking(res))
print()
print(format_win_matrix(res))

# 各エージェントの平均試行回数も覗く(1手だけサンプリング)
print()
print("=== 参考: 0.3秒での試行回数(5x5初期, 1手) ===")
s0 = initial_state(5, 5)
for name in ["mcts-random", "mcts-greedy", "mcts-eps0.3"]:
    ag = AGENT_REGISTRY[name](0)
    ag.select_move(s0)
    print(f"  {name}: {ag.last_info['iterations']} 回")

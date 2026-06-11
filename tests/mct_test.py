"""agents.search_mcts と MCTSAgent のテスト。

MCTS は確率的なので、(a) 構造的な性質は決定的に検証し、
(b) 「強さ」は十分な反復で確率的にほぼ確実になることを確認する。
"""
import math
import random
import numpy as np
import pytest

from core.board import GameState, initial_state
from agents.search_mcts import (
    _Node, random_playout, _backpropagate, _expand, _select, mcts_best_move,
)
from agents.mcts_agent import MCTSAgent


def make3(blocked, p1, p2, turn=1):
    b = np.zeros((3, 3), dtype=bool)
    for rc in blocked:
        b[rc] = True
    return GameState(width=3, height=3, blocked=b,
                     p1_pos=p1, p2_pos=p2, turn=turn)


# ----------------------------------------------------------------------
# プレイアウト
# ----------------------------------------------------------------------

def test_playout_returns_valid_winner():
    """ランダムプレイアウトは必ず終局し、勝者は1か2。"""
    rng = random.Random(0)
    s = initial_state(5, 5)
    for _ in range(20):
        w = random_playout(s, rng)
        assert w in (1, 2)


def test_playout_on_terminal_returns_winner():
    """既に終局した局面では、その勝者をそのまま返す。"""
    around = {(0, 1), (1, 0), (1, 1)}
    s = make3(around, p1=(0, 0), p2=(2, 2), turn=1)  # P1詰み → winner 2
    assert s.is_terminal()
    rng = random.Random(0)
    assert random_playout(s, rng) == 2


# ----------------------------------------------------------------------
# ノードと逆伝播
# ----------------------------------------------------------------------

def test_node_initial_state():
    """新ノードは未訪問・全手未展開。"""
    s = initial_state(5, 5)
    node = _Node(s)
    assert node.visits == 0
    assert node.wins == 0.0
    assert not node.is_fully_expanded()
    assert node.to_play == s.turn


def test_backpropagate_accumulates():
    """逆伝播で visits が増え、to_play が勝者と一致するノードの wins が増える。"""
    s = initial_state(5, 5)   # turn=1
    root = _Node(s)           # to_play=1
    rng = random.Random(0)
    child = _expand(root, rng)  # child.to_play=2
    # 勝者=1 を逆伝播
    _backpropagate(child, winner=1)
    assert root.visits == 1 and child.visits == 1
    assert root.wins == 1.0   # root.to_play=1 が勝者
    assert child.wins == 0.0  # child.to_play=2 は敗者
    # 勝者=2 を逆伝播
    _backpropagate(child, winner=2)
    assert root.visits == 2 and child.visits == 2
    assert root.wins == 1.0   # 変わらず
    assert child.wins == 1.0  # 今度はchildが勝者


# ----------------------------------------------------------------------
# UCB1 の視点反転
# ----------------------------------------------------------------------

def test_ucb1_unvisited_is_infinite():
    """未訪問の子は UCB1 = inf(最優先で試される)。"""
    s = initial_state(5, 5)
    root = _Node(s)
    rng = random.Random(0)
    child = _expand(root, rng)
    root.visits = 1   # 親に訪問数を与える(log の引数を正にする)
    assert child.ucb1(c=1.0) == float("inf")


def test_ucb1_perspective_flips():
    """子の勝率が高い(子の手番側が勝っている)ほど、親から見た
    UCB1 の活用項は低くなる(親にとっては不利な子だから)。"""
    s = initial_state(5, 5)
    root = _Node(s)
    rng = random.Random(0)
    child = _expand(root, rng)
    root.visits = 10
    # 子の手番側が全勝(子視点 winrate=1.0)→ 親視点では 0.0
    child.visits = 5
    child.wins = 5.0
    ucb_high_childwin = child.ucb1(c=0.0)  # 探索項を消して活用項だけ見る
    # 子の手番側が全敗(子視点 winrate=0.0)→ 親視点では 1.0
    child.wins = 0.0
    ucb_low_childwin = child.ucb1(c=0.0)
    assert ucb_low_childwin > ucb_high_childwin


# ----------------------------------------------------------------------
# 最重要: 1手詰みを(確率的に)見つける
# ----------------------------------------------------------------------

def test_mcts_finds_forced_win():
    """1手詰み局面で、十分な反復を与えれば勝ち手を選ぶ。"""
    s = make3({(0, 1), (1, 1)}, p1=(2, 0), p2=(0, 2), turn=1)
    rng = random.Random(0)
    # 時間ではなく反復回数で十分量を保証(再現性のため)
    move, info = mcts_best_move(s, time_limit=None, max_iters=2000, rng=rng)
    dest, remove_cell = move
    # 勝ち筋: (1,2)を削除して相手を詰ませる手
    after = s.apply_move(move)
    assert after.is_terminal() and after.winner() == 1


def test_mcts_returns_legal_move():
    """通常局面で合法手を返す。"""
    s = initial_state(5, 5)
    agent = MCTSAgent(time_limit=None, seed=0)
    # time_limit=None だと無限ループになるため、エージェント経由ではなく
    # 反復上限つきの関数を直接使う
    move, _ = mcts_best_move(s, time_limit=None, max_iters=200,
                             rng=random.Random(0))
    assert move in s.legal_moves()


def test_mcts_agent_runs_with_time():
    """時間制限つきエージェントが合法手を返す。"""
    s = initial_state(5, 5)
    agent = MCTSAgent(time_limit=0.2, seed=0)
    move = agent.select_move(s)
    assert move in s.legal_moves()
    assert agent.last_info["iterations"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ----------------------------------------------------------------------
# プレイアウト方策のバリエーション
# ----------------------------------------------------------------------
from agents.search_mcts import make_greedy_playout, make_epsilon_greedy_playout


def test_greedy_playout_returns_valid_winner():
    """貪欲プレイアウトも必ず終局し勝者を返す。"""
    rng = random.Random(0)
    s = initial_state(5, 5)
    playout = make_greedy_playout("mobility")
    for _ in range(10):
        assert playout(s, rng) in (1, 2)


def test_greedy_playout_on_terminal():
    """終局局面では勝者をそのまま返す。"""
    around = {(0, 1), (1, 0), (1, 1)}
    s = make3(around, p1=(0, 0), p2=(2, 2), turn=1)  # winner 2
    playout = make_greedy_playout("mobility")
    assert playout(s, random.Random(0)) == 2


def test_epsilon_greedy_returns_valid_winner():
    """ε-貪欲プレイアウトも必ず終局し勝者を返す。"""
    rng = random.Random(0)
    s = initial_state(5, 5)
    playout = make_epsilon_greedy_playout("mobility", epsilon=0.3)
    for _ in range(10):
        assert playout(s, rng) in (1, 2)


def test_mcts_with_greedy_playout_finds_win():
    """貪欲プレイアウトを使っても1手詰みを見つける。"""
    s = make3({(0, 1), (1, 1)}, p1=(2, 0), p2=(0, 2), turn=1)
    playout = make_greedy_playout("mobility")
    move, _ = mcts_best_move(s, time_limit=None, max_iters=1000,
                             playout=playout, rng=random.Random(0))
    after = s.apply_move(move)
    assert after.is_terminal() and after.winner() == 1
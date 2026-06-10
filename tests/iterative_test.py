"""agents.search_iterative のテスト。

検証の柱:
  ・order_moves は値を変えず、順序だけ変える(pv先頭・評価降順)
  ・固定深さに到達した反復深化の値は、素朴αβの値と一致する
  ・time_limit を概ね守る
  ・1手詰みを見つける
"""

import numpy as np
import random
import time
import pytest

from core.board import GameState, initial_state
from core.evaluation import get_evaluation_function, EVALUATIONS
from agents.search_alphabeta import alphabeta_value
from agents.search_iterative import (
    order_moves, iterative_deepening_best_move, _alphabeta, WIN,
)
from agents.iterative_agent import IterativeDeepeningAgent


def make3(blocked, p1, p2, turn=1):
    b = np.zeros((3, 3), dtype=bool)
    for rc in blocked:
        b[rc] = True
    return GameState(width=3, height=3, blocked=b,
                     p1_pos=p1, p2_pos=p2, turn=turn)


def random_state(width, height, n_blocked, seed):
    rng = random.Random(seed)
    cells = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(cells)
    p1, p2 = cells[0], cells[1]
    blocked = set(cells[2:2 + n_blocked])
    b = np.zeros((height, width), dtype=bool)
    for rc in blocked:
        b[rc] = True
    return GameState(width=width, height=height, blocked=b,
                     p1_pos=p1, p2_pos=p2, turn=1)


# ----------------------------------------------------------------------
# 手の順序付け
# ----------------------------------------------------------------------

def test_order_moves_is_permutation():
    """順序付けは手の集合を変えない(並べ替えるだけ)。"""
    s = initial_state(5, 5)
    ev = get_evaluation_function("mobility")
    moves = s.legal_moves()
    ordered = order_moves(s, moves, ev, root_player=s.turn)
    assert set(ordered) == set(moves)
    assert len(ordered) == len(moves)


def test_order_moves_descending_by_eval():
    """pv なしのとき、評価値の降順に並ぶ。"""
    s = initial_state(5, 5)
    ev = get_evaluation_function("voronoi")
    ordered = order_moves(s, s.legal_moves(), ev, root_player=s.turn)
    scores = [ev(s.apply_move(m), s.turn) for m in ordered]
    # 降順(非増加)になっているか
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))


def test_order_moves_pv_first():
    """pv_move を指定すると、それが先頭に来る。"""
    s = initial_state(5, 5)
    ev = get_evaluation_function("mobility")
    moves = s.legal_moves()
    pv = moves[-1]  # わざと末尾の手を pv に指定
    ordered = order_moves(s, moves, ev, root_player=s.turn, pv_move=pv)
    assert ordered[0] == pv
    assert set(ordered) == set(moves)  # 集合は不変


# ----------------------------------------------------------------------
# 反復深化の値は素朴αβと一致する(順序付けは答えを変えない)
# ----------------------------------------------------------------------

def test_iterative_value_matches_alphabeta():
    """十分な時間を与えれば、反復深化が到達した深さでの値は
    同じ深さの素朴αβの値と一致する。

    ここでは _alphabeta(順序付き)を固定深さで直接呼び、
    順序なしαβと値が一致することを確認する(順序付けの正しさ)。
    """
    for eval_name in EVALUATIONS:
        ev = get_evaluation_function(eval_name)
        for seed in range(6):
            s = random_state(4, 4, n_blocked=3, seed=seed)
            if s.is_terminal():
                continue
            for depth in (1, 2, 3):
                v_plain = alphabeta_value(
                    s, depth, root_player=s.turn, evaluate=ev,
                    alpha=-float("inf"), beta=float("inf"))
                v_ordered = _alphabeta(
                    s, depth, root_player=s.turn, evaluate=ev,
                    alpha=-float("inf"), beta=float("inf"), deadline=None)
                assert v_ordered == v_plain, (
                    f"ordering changed value: eval={eval_name} "
                    f"depth={depth} seed={seed}")


# ----------------------------------------------------------------------
# 時間制限を守る
# ----------------------------------------------------------------------

def test_time_limit_is_respected():
    """time_limit を大きく超えない(多少のオーバーは許容)。"""
    s = initial_state(6, 6)  # 大きめの盤で深く読みたくなる状況
    ev = get_evaluation_function("voronoi")
    limit = 1.0
    t0 = time.time()
    move, info = iterative_deepening_best_move(s, ev, time_limit=limit)
    elapsed = time.time() - t0
    # 途中チェックで中断するので、制限の2倍以内には収まるはず
    assert elapsed < limit * 2.0
    assert move in s.legal_moves()
    assert info["depth"] >= 1


def test_returns_move_even_with_tiny_time():
    """極端に短い制限でも、最低 depth=1 の手を必ず返す。"""
    s = initial_state(5, 5)
    ev = get_evaluation_function("mobility")
    move, info = iterative_deepening_best_move(s, ev, time_limit=0.0001)
    assert move in s.legal_moves()
    assert info["depth"] >= 1


def test_deeper_with_more_time():
    """時間を増やすと到達深さが増える(または同等)傾向。"""
    s = initial_state(5, 5)
    ev = get_evaluation_function("voronoi")
    _, info_short = iterative_deepening_best_move(s, ev, time_limit=0.1)
    _, info_long = iterative_deepening_best_move(s, ev, time_limit=2.0)
    assert info_long["depth"] >= info_short["depth"]


# ----------------------------------------------------------------------
# 1手詰み
# ----------------------------------------------------------------------

def test_iterative_finds_forced_win():
    """1手詰み局面で勝ち手を返し、勝ち値(>=WIN)を報告する。"""
    s = make3({(0, 1), (1, 1)}, p1=(2, 0), p2=(0, 2), turn=1)
    agent = IterativeDeepeningAgent(time_limit=1.0,
                                    evaluation="mobility", seed=0)
    move = agent.select_move(s)
    dest, remove_cell = move
    assert remove_cell == (1, 2)
    after = s.apply_move(move)
    assert after.is_terminal() and after.winner() == 1
    assert agent.last_info["value"] >= WIN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""agents.search_alphabeta のテスト。

最重要: αβ は素朴 minimax と『同じ値』を返す(枝刈りは結果を変えない)。
小さい盤・浅い深さで総当たり的に値の一致を検証する。
"""

import numpy as np
import random
import pytest

from core.board import GameState, initial_state
from core.evaluation import get_evaluation_function, EVALUATION_FUNCTIONS
from agents.search_minimax import minimax_value, minimax_best_move
from agents.search_alphabeta import alphabeta_value, alphabeta_best_move, WIN
from agents.alphabeta_agent import AlphaBetaAgent


def make3(blocked, p1, p2, turn=1):
    b = np.zeros((3, 3), dtype=bool)
    for rc in blocked:
        b[rc] = True
    return GameState(width=3, height=3, blocked=b,
                     p1_pos=p1, p2_pos=p2, turn=turn)


def random_state(width, height, n_blocked, seed):
    """ランダムに削除済みマスを撒いた局面を作る(両プレイヤーは未削除マスに置く)。"""
    rng = random.Random(seed)
    cells = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(cells)
    p1 = cells[0]
    p2 = cells[1]
    blocked = set(cells[2:2 + n_blocked])
    b = np.zeros((height, width), dtype=bool)
    for rc in blocked:
        b[rc] = True
    return GameState(width=width, height=height, blocked=b,
                     p1_pos=p1, p2_pos=p2, turn=1)


# ----------------------------------------------------------------------
# 最重要: αβ の値 == minimax の値
# ----------------------------------------------------------------------

@pytest.mark.parametrize("eval_name", list(EVALUATION_FUNCTIONS))
@pytest.mark.parametrize("depth", [1, 2, 3])
def test_alphabeta_value_equals_minimax(eval_name, depth):
    """4x4 のランダム局面群で、αβ値 と minimax値 が完全一致する。"""
    ev = get_evaluation_function(eval_name)
    for seed in range(8):
        s = random_state(4, 4, n_blocked=3, seed=seed)
        if s.is_terminal():
            continue
        v_mm = minimax_value(s, depth, root_player=s.turn, evaluate=ev)
        v_ab = alphabeta_value(s, depth, root_player=s.turn, evaluate=ev,
                               alpha=-float("inf"), beta=float("inf"))
        assert v_ab == v_mm, (
            f"mismatch eval={eval_name} depth={depth} seed={seed}: "
            f"mm={v_mm} ab={v_ab}")


@pytest.mark.parametrize("depth", [1, 2, 3])
def test_alphabeta_best_value_equals_minimax(depth):
    """最善手の『値』が一致する(手そのものは同点タイブレークで割れうる)。"""
    ev = get_evaluation_function("mobility")
    for seed in range(8):
        s = random_state(4, 4, n_blocked=3, seed=seed)
        if s.is_terminal():
            continue
        _m_mm, v_mm = minimax_best_move(s, depth, evaluate=ev)
        _m_ab, v_ab = alphabeta_best_move(s, depth, evaluate=ev)
        assert v_ab == v_mm


# ----------------------------------------------------------------------
# αβ も 1手詰みを見つける
# ----------------------------------------------------------------------

def test_alphabeta_finds_forced_win():
    """minimax と同じ1手詰み局面で、αβ も勝ち手を返す。"""
    s = make3({(0, 1), (1, 1)}, p1=(2, 0), p2=(0, 2), turn=1)
    agent = AlphaBetaAgent(depth=2, evaluation="mobility", seed=0)
    move = agent.select_move(s)
    dest, remove_cell = move
    assert remove_cell == (1, 2)
    after = s.apply_move(move)
    assert after.is_terminal() and after.winner() == 1


# ----------------------------------------------------------------------
# 選んだ手の値が、全合法手の中で最善であること
# ----------------------------------------------------------------------

def test_alphabeta_move_is_optimal():
    """αβ が返す手の値は、全合法手を minimax で測った最大値に等しい。"""
    ev = get_evaluation_function("voronoi")
    s = random_state(4, 4, n_blocked=2, seed=3)
    depth = 2
    move_ab, val_ab = alphabeta_best_move(s, depth, evaluate=ev)
    # 全合法手を minimax で測った真の最大値
    root = s.turn
    true_max = max(
        minimax_value(s.apply_move(m), depth - 1, root_player=root, evaluate=ev)
        for m in s.legal_moves()
    )
    assert val_ab == true_max
    # αβ が返した手も、その最大値を達成していること
    assert minimax_value(s.apply_move(move_ab), depth - 1,
                         root_player=root, evaluate=ev) == true_max


def test_alphabeta_returns_legal_moves():
    """各深さ・各評価で合法手を返す(スモークテスト)。"""
    s = initial_state(5, 5)
    for d in (1, 2, 3):
        for ev in EVALUATION_FUNCTIONS:
            agent = AlphaBetaAgent(depth=d, evaluation=ev, seed=0)
            assert agent.select_move(s) in s.legal_moves()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
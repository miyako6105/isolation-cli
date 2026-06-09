"""core.evaluation のテスト。

評価関数が満たすべき性質を仕様として固定する。
特に「視点は player に固定（turn 非依存）」「player 入れ替えで符号反転」
「分断後は到達可能マス差が勝敗を示す」を確認する。
"""

import numpy as np
import pytest

from core.board import GameState
from core.evaluation import (
    mobility_diff, reachable_diff, voronoi_diff,
    get_evaluation_function, EVALUATION_FUNCTIONS,
)


def make_state(width, height, p1, p2, turn=1, blocked_cells=()):
    blocked = np.zeros((height, width), dtype=bool)
    for (r, c) in blocked_cells:
        blocked[r, c] = True
    return GameState(width=width, height=height, blocked=blocked,
                     p1_pos=p1, p2_pos=p2, turn=turn)


ALL_EVALS = [mobility_diff, reachable_diff, voronoi_diff]


# ----------------------------------------------------------------------
# 対称性: player を入れ替えると符号が反転する
# ----------------------------------------------------------------------

@pytest.mark.parametrize("eval_fn", ALL_EVALS)
def test_sign_flips_when_player_swapped(eval_fn):
    """同じ状態で player=1 と player=2 を評価すると符号が反転する。
    これは差分型評価 (自分 − 相手) の本質的性質。"""
    s = make_state(5, 5, p1=(1, 1), p2=(3, 3), turn=1,
                   blocked_cells={(2, 2), (0, 4)})
    v1 = eval_fn(s, player=1)
    v2 = eval_fn(s, player=2)
    assert v1 == -v2


# ----------------------------------------------------------------------
# 視点は player 固定で turn に依存しない
# ----------------------------------------------------------------------

@pytest.mark.parametrize("eval_fn", ALL_EVALS)
def test_evaluation_independent_of_turn(eval_fn):
    """turn だけが違う2状態を player=1 視点で評価すると同じ値になる。
    評価は『誰の得か(player)』で決まり『今の手番(turn)』では決まらない。"""
    s_turn1 = make_state(5, 5, (1, 1), (3, 3), turn=1,
                         blocked_cells={(2, 2)})
    s_turn2 = make_state(5, 5, (1, 1), (3, 3), turn=2,
                         blocked_cells={(2, 2)})
    assert eval_fn(s_turn1, 1) == eval_fn(s_turn2, 1)


# ----------------------------------------------------------------------
# 対称な盤面では評価0
# ----------------------------------------------------------------------

@pytest.mark.parametrize("eval_fn", ALL_EVALS)
def test_symmetric_board_is_zero(eval_fn):
    """中心対称な配置では、どちらも有利でないので評価は0になる。"""
    # 5x5 の点対称: P1=(0,0), P2=(4,4)、削除も点対称に配置
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1,
                   blocked_cells={(1, 2), (3, 2)})  # (1,2)と(3,2)は点対称
    assert eval_fn(s, 1) == 0


# ----------------------------------------------------------------------
# mobility: 動ける数の差をそのまま返す
# ----------------------------------------------------------------------

def test_mobility_counts_moves():
    """隅(0,0)のP1は3手、中央(2,2)のP2は8手 → mobility(P1)= 3-8 = -5。"""
    s = make_state(5, 5, p1=(0, 0), p2=(2, 2), turn=1)
    assert mobility_diff(s, 1) == 3 - 8


# ----------------------------------------------------------------------
# 分断後: reachable と voronoi が勝敗方向を正しく示す
# ----------------------------------------------------------------------

def test_partitioned_board_reachable_favors_larger_region():
    """盤を縦に分断し、自分側を広く・相手側を狭くする。
    reachable_diff は自分側が正（有利）を返すはず。"""
    # 5x5。列2をすべて削除して左右に分断する。
    # 左領域(列0-1)にP1、右領域(列3-4)にP2。左の方が広い配置にする。
    wall = {(r, 2) for r in range(5)}  # 中央の縦の壁
    # さらに右領域を削って狭くする: 列4を上3つ削除
    narrow = {(0, 4), (1, 4), (2, 4)}
    s = make_state(5, 5, p1=(2, 0), p2=(4, 4), turn=1,
                   blocked_cells=wall | narrow)

    # 分断されているので、自分(左,広い)が相手(右,狭い)より到達数が多い
    assert reachable_diff(s, 1) > 0
    # voronoi も同じ方向（左の方が支配マスが多い）
    assert voronoi_diff(s, 1) > 0


def test_partition_reachable_exact_difference():
    """完全分断時、reachable_diff は (自領域マス数 − 相手領域マス数) に一致する。
    この厳密性が『分断後は評価が真実に近い』の根拠。"""
    # 3x3 を中央列で分断。左列(0,1,2行 × 列0)にP1、右列(列2)にP2、列1は壁。
    wall = {(0, 1), (1, 1), (2, 1)}
    s = make_state(width=3, height=3, p1=(0, 0), p2=(0, 2), turn=1,
                   blocked_cells=wall)
    # 自領域: 列0の (1,0),(2,0) の2マス（自分の足元(0,0)は除く）
    # 相手領域: 列2の (1,2),(2,2) の2マス
    # よって差は 2 - 2 = 0
    assert reachable_diff(s, 1) == 0

    # 相手側だけ1マス潰すと、自分が有利(+1)になる
    s2 = make_state(3, 3, p1=(0, 0), p2=(0, 2), turn=1,
                    blocked_cells=wall | {(2, 2)})
    # 自領域 2マス、相手領域 1マス → 差 +1
    assert reachable_diff(s2, 1) == 1


# ----------------------------------------------------------------------
# voronoi: 分断前でも「近さ」で領域を分ける
# ----------------------------------------------------------------------

def test_voronoi_distinguishes_before_partition():
    """壁のない開けた盤でも、ボロノイは中心に近い側を有利と評価する。
    mobility が同点でも voronoi は差を出せることを示す。"""
    # 7x7。P1を中央寄り(3,3)、P2を隅(6,6)。壁なし＝分断前。
    s = make_state(7, 7, p1=(3, 3), p2=(6, 6), turn=1)
    # 中央寄りのP1は盤の大部分に先に到達できる → 有利
    assert voronoi_diff(s, 1) > 0


# ----------------------------------------------------------------------
# レジストリ
# ----------------------------------------------------------------------

def test_registry_returns_correct_function():
    assert get_evaluation_function("mobility") is mobility_diff
    assert get_evaluation_function("reachable") is reachable_diff
    assert get_evaluation_function("voronoi") is voronoi_diff


def test_registry_rejects_unknown():
    with pytest.raises(KeyError):
        get_evaluation_function("nonexistent")


def test_all_registered_evals_share_signature():
    """登録済み評価はすべて (state, player) で呼べる。"""
    s = make_state(5, 5, (0, 0), (4, 4), turn=1)
    for name, fn in EVALUATION_FUNCTIONS.items():
        result = fn(s, 1)
        assert isinstance(result, (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
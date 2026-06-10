"""agents.search_minimax と MinimaxAgent のテスト。

最重要: 『読めば正しい手を選ぶ』こと。1手詰みの局面で勝ち手を
見つけられるか、を中心に検証する。
"""

import numpy as np
import pytest

from core.board import GameState, initial_state
from core.evaluation import get_evaluation_function, mobility_diff
from agents.search_minimax import (
    minimax_value, minimax_best_move, WIN, _terminal_value,
)
from agents.minimax_agent import MinimaxAgent
from agents.simple import GreedyAgent


def make3(blocked, p1, p2, turn=1):
    """3x3 盤を手早く作る。"""
    b = np.zeros((3, 3), dtype=bool)
    for rc in blocked:
        b[rc] = True
    return GameState(width=3, height=3, blocked=b,
                     p1_pos=p1, p2_pos=p2, turn=turn)


def make_state(width, height, p1, p2, turn=1, blocked_cells=()):
    b = np.zeros((height, width), dtype=bool)
    for rc in blocked_cells:
        b[rc] = True
    return GameState(width=width, height=height, blocked=b,
                     p1_pos=p1, p2_pos=p2, turn=turn)


# ----------------------------------------------------------------------
# 終局値の符号と手数の向き
# ----------------------------------------------------------------------

def test_terminal_value_win_is_large_positive():
    """自分(root_player)の勝ち終局は +WIN 以上。"""
    # P1 手番だが P1 が動けない状態 = P1 の負け = winner 2
    around = {(0, 1), (1, 0), (1, 1)}
    s = make3(around, p1=(0, 0), p2=(2, 2), turn=1)
    assert s.is_terminal() and s.winner() == 2
    # root_player=2 から見れば勝ち
    assert _terminal_value(s, root_player=2, depth=5) >= WIN
    # root_player=1 から見れば負け
    assert _terminal_value(s, root_player=1, depth=5) <= -WIN


def test_earlier_win_scores_higher():
    """同じ勝ちなら、早い勝ち(depthが大きい)ほど高評価。"""
    around = {(0, 1), (1, 0), (1, 1)}
    s = make3(around, p1=(0, 0), p2=(2, 2), turn=1)  # winner=2
    v_early = _terminal_value(s, root_player=2, depth=8)
    v_late = _terminal_value(s, root_player=2, depth=2)
    assert v_early > v_late


# ----------------------------------------------------------------------
# 最重要: 1手詰みを見つける
# ----------------------------------------------------------------------

def test_minimax_finds_forced_win_in_one():
    """P2の逃げ先が(1,2)だけの局面で、P1は(1,2)を削除して詰ませる。

    盤:
      . # 2
      . # .
      1 . .
    P2の唯一の移動先(1,2)を P1 が削除すれば、次のP2手番で詰む。
    P1自身は(1,2)へ移動してはいけない(移動先は削除できないため)。
    """
    s = make3({(0, 1), (1, 1)}, p1=(2, 0), p2=(0, 2), turn=1)
    agent = MinimaxAgent(depth=2, evaluation="mobility", seed=0)
    move = agent.select_move(s)
    dest, remove_cell = move
    # 勝ち筋: (1,2)を削除する手であること
    assert remove_cell == (1, 2)
    # かつ自分は(1,2)へは移動していないこと
    assert dest != (1, 2)
    # 実際にこの手で相手が詰むことを確認
    after = s.apply_move(move)
    assert after.is_terminal()
    assert after.winner() == 1


def test_minimax_value_detects_win():
    """勝ち筋のある局面の minimax 値は WIN 級になる。"""
    s = make3({(0, 1), (1, 1)}, p1=(2, 0), p2=(0, 2), turn=1)
    _move, value = minimax_best_move(
        s, depth=2, evaluate=get_evaluation_function("mobility"))
    assert value >= WIN


# ----------------------------------------------------------------------
# depth=1 の minimax は貪欲と一致する
# ----------------------------------------------------------------------

def test_depth1_minimax_matches_greedy_value():
    """depth=1 の minimax_best_move は『1手先の評価最大』を選ぶ。
    これは GreedyAgent と同じ規準。同じ評価関数なら同じ値を最大化する。
    """
    s = initial_state(5, 5)
    ev = get_evaluation_function("mobility")
    # depth=1: 各手を打った子(depth0)を評価関数で測るだけ
    move_mm, _ = minimax_best_move(s, depth=1, evaluate=ev)
    # 貪欲が選ぶ手の評価値と、minimaxが選ぶ手の評価値が一致するか確認
    # (同点が複数ありうるので、値の一致で検証する)
    val_of = lambda m: ev(s.apply_move(m), s.turn)
    greedy = GreedyAgent(evaluation="mobility", seed=0)
    move_gd = greedy.select_move(s)
    assert val_of(move_mm) == val_of(move_gd)


# ----------------------------------------------------------------------
# 深さを増やすと相手の即詰み返しを避ける
# ----------------------------------------------------------------------

def test_deeper_search_returns_legal_moves():
    """深さ3まででも合法手を返し、落ちない(スモークテスト)。"""
    s = initial_state(5, 5)
    for d in (1, 2, 3):
        agent = MinimaxAgent(depth=d, evaluation="voronoi", seed=0)
        assert agent.select_move(s) in s.legal_moves()


# ----------------------------------------------------------------------
# 視点の一貫性: 同じ局面を両プレイヤー視点で読むと符号が反転する方向
# ----------------------------------------------------------------------

def test_minimax_value_perspective():
    """root_playerを入れ替えると、同一局面の評価は符号反転する。
    (終局でない中間局面で、深さ1=評価関数1回ぶんで確認)
    """
    s = make_state(5, 5, p1=(1, 1), p2=(3, 3), turn=1,
                   blocked_cells={(2, 2)})
    ev = get_evaluation_function("mobility")
    # depth=0 なら純粋に評価関数。root_player視点が効く。
    v1 = minimax_value(s, depth=0, root_player=1, evaluate=ev)
    v2 = minimax_value(s, depth=0, root_player=2, evaluate=ev)
    assert v1 == -v2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
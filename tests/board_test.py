"""isolation.core.board のテスト。

このテスト群は「ルールの仕様書」を兼ねる。各テストの名前と中身が、
ゲームがどう振る舞うべきかを文章として固定している。
"""

import numpy as np
import pytest

from core.board import GameState, initial_state, DIRECTIONS


# ----------------------------------------------------------------------
# 補助: 任意の盤面を簡単に組み立てるためのファクトリ
# ----------------------------------------------------------------------

def make_state(width, height, p1, p2, turn=1, blocked_cells=()):
    """テスト用に状態を手早く作る。blocked_cells は削除済みにする (r,c) の集合。"""
    blocked = np.zeros((height, width), dtype=bool)
    for (r, c) in blocked_cells:
        blocked[r, c] = True
    return GameState(width=width, height=height, blocked=blocked,
                     p1_pos=p1, p2_pos=p2, turn=turn)


# ----------------------------------------------------------------------
# 初期状態
# ----------------------------------------------------------------------

def test_initial_positions_are_diagonal():
    """初期配置は対角。P1=左上, P2=右下, 手番はP1。"""
    s = initial_state(width=5, height=4)
    assert s.p1_pos == (0, 0)
    assert s.p2_pos == (3, 4)  # (height-1, width-1)
    assert s.turn == 1


def test_initial_board_is_empty():
    """初期盤面に削除済みマスは無い。"""
    s = initial_state(5, 5)
    assert not s.blocked.any()


# ----------------------------------------------------------------------
# 移動範囲（キングの動き）
# ----------------------------------------------------------------------

def test_king_has_eight_destinations_in_open_center():
    """周囲が完全に開いた中央のプレイヤーは八方向すべてに動ける。"""
    # 7x7 の中央 (3,3) にP1、相手は遠く隅に置いて干渉させない。
    s = make_state(7, 7, p1=(3, 3), p2=(6, 6), turn=1)
    dests = set(s.legal_destinations())
    expected = {(3 + dr, 3 + dc) for dr, dc in DIRECTIONS}
    assert dests == expected
    assert len(dests) == 8


def test_corner_player_has_three_destinations():
    """隅 (0,0) のプレイヤーは盤内の3方向にしか動けない。"""
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1)
    dests = set(s.legal_destinations())
    assert dests == {(0, 1), (1, 0), (1, 1)}


# ----------------------------------------------------------------------
# 移動の制約: 盤外 / 削除済み / 相手マス
# ----------------------------------------------------------------------

def test_cannot_move_onto_blocked_cell():
    """削除済みマスへは移動できない。"""
    # (3,3) のP1。右 (3,4) を削除済みにすると、その方向だけ消える。
    s = make_state(7, 7, p1=(3, 3), p2=(6, 6), turn=1,
                   blocked_cells={(3, 4)})
    assert (3, 4) not in s.legal_destinations()


def test_cannot_move_onto_opponent():
    """相手のいるマスへは移動できない。"""
    # P1=(3,3), P2 を隣 (3,4) に置く。その方向へは行けない。
    s = make_state(7, 7, p1=(3, 3), p2=(3, 4), turn=1)
    assert (3, 4) not in s.legal_destinations()


def test_cannot_move_out_of_bounds():
    """盤外へは出られない（隅で確認済みだが明示しておく）。"""
    s = make_state(3, 3, p1=(0, 0), p2=(2, 2), turn=1)
    for (r, c) in s.legal_destinations():
        assert s.in_bounds(r, c)


# ----------------------------------------------------------------------
# 削除のルール
# ----------------------------------------------------------------------

def test_move_blocks_chosen_cell():
    """移動後、指定した空きマスが削除済みになる。"""
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1)
    move = ((1, 1), (2, 2))  # (1,1) へ移動し、(2,2) を削除
    ns = s.apply_move(move)
    assert ns.blocked[2, 2]          # 削除された
    assert ns.p1_pos == (1, 1)       # 移動した
    assert ns.turn == 2              # 手番が相手に渡る


def test_cannot_delete_own_landing_cell():
    """移動後の自分の足元は削除できない（合法手に含まれない）。"""
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1)
    for dest, remove_cell in s.legal_moves():
        assert remove_cell != dest


def test_cannot_delete_opponent_cell():
    """相手のいるマスは削除できない。"""
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1)
    for dest, remove_cell in s.legal_moves():
        assert remove_cell != s.opponent_pos()


def test_cannot_delete_already_blocked_cell():
    """既に削除済みのマスは削除対象に挙がらない。"""
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1,
                   blocked_cells={(2, 2)})
    for _, remove_cell in s.legal_moves():
        assert remove_cell != (2, 2)


# ----------------------------------------------------------------------
# イミュータブル性: apply_move は元の状態を壊さない
# ----------------------------------------------------------------------

def test_apply_move_does_not_mutate_original():
    """apply_move 後も元の状態は一切変わらない。"""
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1)
    original_blocked = s.blocked.copy()
    original_p1 = s.p1_pos
    original_turn = s.turn

    _ = s.apply_move(((1, 1), (2, 2)))

    assert np.array_equal(s.blocked, original_blocked)  # 盤面不変
    assert s.p1_pos == original_p1                      # 位置不変
    assert s.turn == original_turn                      # 手番不変


# ----------------------------------------------------------------------
# 合法手の数（分岐因子の確認）
# ----------------------------------------------------------------------

def test_legal_move_count_matches_dest_times_free_cells():
    """合法手数 = 移動先数 × (削除可能な空きマス数) になっているか。

    削除可能な空きマス = 全空きマス
        − 移動後の自分の足元(dest)  ※destごとに1つ差し引く
        − 相手のマス
    相手のマスは常に空き扱いされていないので、空きマス集合から
    あらかじめ除いておく。
    """
    s = make_state(5, 5, p1=(0, 0), p2=(4, 4), turn=1)

    # 盤上の空きマス（未削除）の (r,c) 集合
    free = {(r, c) for r in range(5) for c in range(5)
            if not s.blocked[r, c]}
    # 相手マスは削除対象から常に外れる
    free_minus_opp = free - {s.opponent_pos()}

    dests = s.legal_destinations()
    # 各 dest について、削除候補は free_minus_opp から dest を除いた数。
    # （dest が空きマスである限り 1 つ減る）
    expected = 0
    for dest in dests:
        candidates = free_minus_opp - {dest}
        expected += len(candidates)

    assert len(s.legal_moves()) == expected


# ----------------------------------------------------------------------
# 終局と勝者判定（このゲームの核心）
# ----------------------------------------------------------------------

def test_not_terminal_when_moves_exist():
    """動ける手がある限り終局ではなく、勝者は未定。"""
    s = initial_state(5, 5)
    assert not s.is_terminal()
    assert s.winner() is None


def test_terminal_when_completely_surrounded():
    """手番プレイヤーの八方向がすべて塞がれていれば終局し、相手の勝ち。"""
    # P1=(1,1) を中央に置き、周囲8マスを削除済みにする。
    # ただし相手 P2 は周囲8マスの外（(4,4)）に置く。
    around = {(1 + dr, 1 + dc) for dr, dc in DIRECTIONS}
    s = make_state(5, 5, p1=(1, 1), p2=(4, 4), turn=1,
                   blocked_cells=around)
    assert s.is_terminal()
    assert s.winner() == 2  # 動けない P1 の負け → P2 の勝ち


def test_terminal_uses_opponent_as_blocker():
    """周囲が盤外＋相手で塞がれても終局になる（削除なしでも詰む）。"""
    # 2x1 盤。P1=(0,0), P2=(1,0)。P1 の動ける先は下の (1,0) だけだが
    # そこには相手がいるので動けない → 即終局。
    s = make_state(width=1, height=2, p1=(0, 0), p2=(1, 0), turn=1)
    assert s.is_terminal()
    assert s.winner() == 2


# ----------------------------------------------------------------------
# 等価判定とハッシュ（探索での状態管理に必要）
# ----------------------------------------------------------------------

def test_equal_states_are_equal_and_hash_same():
    """同じ内容の状態は == で等しく、ハッシュも一致する（dictのキーに使える）。"""
    s1 = make_state(5, 5, (0, 0), (4, 4), turn=1, blocked_cells={(2, 2)})
    s2 = make_state(5, 5, (0, 0), (4, 4), turn=1, blocked_cells={(2, 2)})
    assert s1 == s2
    assert hash(s1) == hash(s2)
    # set に入れて重複が潰れることも確認
    assert len({s1, s2}) == 1


def test_different_blocked_states_differ():
    """削除済みマスが違えば別状態として区別される。"""
    s1 = make_state(5, 5, (0, 0), (4, 4), turn=1, blocked_cells={(2, 2)})
    s2 = make_state(5, 5, (0, 0), (4, 4), turn=1, blocked_cells={(3, 3)})
    assert s1 != s2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
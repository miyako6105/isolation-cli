# 盤面を定義するファイル
from dataclasses import dataclass, replace
import numpy as np

# MARK: Direction
# 8方向の移動ベクトル（行方向, 列方向）
# キングの動きそのもの。ここを差し替えれば別ルールにも転用できる
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]

# MARK: GameState
@dataclass(frozen=True) # 変更不可
class GameState:
    width: int # 盤面の幅
    height: int # 盤面の高さ
    blocked: np.ndarray # blocked[i][j]がTrueなら(i, j)は削除（移動不可）
    p1_pos: tuple[int, int] # プレイヤー1の位置
    p2_pos: tuple[int, int] # プレイヤー2の位置
    turn: int # 1 or 2, プレイヤーのターンを表す

    def current_pos(self):
        """
        現在のプレイヤーの位置を返す
        """
        return self.p1_pos if self.turn == 1 else self.p2_pos
    
    def opponent_pos(self):
        """
        相手プレイヤーの位置を返す
        """
        return self.p2_pos if self.turn == 1 else self.p1_pos
    
    def is_bounds(self, r, c):
        """
        (r, c)が盤面の範囲内かどうかをチェックする
        """
        return (0 <= r < self.height) and (0 <= c < self.width)
    
    def is_free(self, r, c):
        """
        (r, c)が移動可能かどうかをチェックする
        条件は以下の3点を全て満たす場合：
        1. 盤面の範囲内であること
        2. 削除されていないこと
        3. 相手プレイヤーがいないこと
        """
        if not self.is_bounds(r, c):
            return False # 範囲外(条件1)
        if self.blocked[r][c]:
            return False # 削除されている(条件2)
        if (r, c) == self.opponent_pos():
            return False # 相手プレイヤーがいる(条件3)
        return True # 全ての条件を満たす場合は移動可能
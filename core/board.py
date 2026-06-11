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
    
    def in_bounds(self, r, c):
        """
        (r, c)が盤面の範囲内かどうかをチェックする
        Args:
            r (int): 行番号
            c (int): 列番号
        """
        return (0 <= r < self.height) and (0 <= c < self.width)
    
    def is_free(self, r, c):
        """
        (r, c)が移動可能かどうかをチェックする
        条件は以下の3点を全て満たす場合：
        1. 盤面の範囲内であること
        2. 削除されていないこと
        3. 相手プレイヤーがいないこと
        Args:
            r (int): 行番号
            c (int): 列番号
        """
        if not self.in_bounds(r, c):
            return False # 範囲外(条件1)
        if self.blocked[r][c]:
            return False # 削除されている(条件2)
        if (r, c) == self.opponent_pos():
            return False # 相手プレイヤーがいる(条件3)
        return True # 全ての条件を満たす場合は移動可能
    
    def legal_destinations(self):
        """
        今の手番プレイヤーが移動できるマスの一覧を返す。
        削除のことは考えず、純粋に「八方向で行けるマス」だけを返す。
        評価関数（動ける数）でも使うので独立した関数にしてある。
        """
        r0, c0 = self.current_pos()
        dests = []
        for dr, dc in DIRECTIONS:
            nr, nc = r0 + dr, c0 + dc
            if self.is_free(nr, nc):
                dests.append((nr, nc))
        return dests
    
    def legal_moves(self):
        """
        今のプレイヤーの合法手を全列挙する
        """
        r0, c0 = self.current_pos() # 現在のプレイヤーの位置
        moves = [] # 合法手のリスト

        # 移動先の候補を収集
        destinations = []
        for dr, dc in DIRECTIONS:
            r, c = r0 + dr, c0 + dc
            if self.is_free(r, c):
                destinations.append((r, c))
        
        # 各移動先に対して、削除するマスを全列挙
        for dest in destinations:
            for r in range(self.height):
                for c in range(self.width):
                    # 削除可能なのは移動先以外の空きマス
                    if self.blocked[r][c]:
                        continue # 既に削除されているマスはスキップ
                    if (r, c) == dest:
                        continue # 移動先は削除できないのでスキップ
                    if (r, c) == self.opponent_pos():
                        continue # 相手プレイヤーがいるマスは削除できないのでスキップ
                    moves.append((dest, (r, c))) # (移動先, 削除するマス)のペアを追加
        return moves
    
    def apply_move(self, move):
        """
        新しい手を適用した状態を返す（元の状態は変更しない）
        Args:
            move (tuple): (移動先, 削除するマス)のペア
        """
        dest, remove_cell = move
        new_blocked = self.blocked.copy() # 新しいblocked配列を作成
        new_blocked[remove_cell] = True # 削除するマスを更新

        if self.turn == 1:
            return replace(self, blocked=new_blocked, p1_pos=dest, turn=2) # プレイヤー1のターンからプレイヤー2のターンへ
        else:
            return replace(self, blocked=new_blocked, p2_pos=dest, turn=1) # プレイヤー2のターンからプレイヤー1のターンへ
    
    def is_terminal(self):
        """
        ゲームが終了しているかどうかをチェックする
        """
        return len(self.legal_moves()) == 0
    
    def winner(self):
        """
        終局時の勝者を返す
        """
        if not self.is_terminal():
            return None # ゲームが終了していない場合は勝者なし
        return 2 if self.turn == 1 else 1 # 現在のプレイヤーが合法手を持たない場合、相手プレイヤーが勝者
    def _key(self):
        """
        状態の等価判定とハッシュに使うキーを生成する
        """
        return (
            self.width, self.height,
            self.blocked.tobytes(), # blocked配列をバイト列に変換してキーにする
            self.p1_pos, self.p2_pos,
            self.turn
        )
    
    def __eq__(self, other):
        """
        状態の等価判定。盤面の状態が同じなら等しいとみなす。
        """
        if not isinstance(other, GameState):
            return False
        return self._key() == other._key()
    
    def __hash__(self):
        """
        状態のハッシュ値を返す。盤面の状態が同じなら同じハッシュ値になる。
        """
        return hash(self._key())

# MARK: initial_state
def initial_state(width: int, height: int, p1: tuple[int, int]=None, p2: tuple[int, int]=None, turn: int = 1):
    """
    初期状態を生成する関数
    Args:
        width (int): 盤面の幅
        height (int): 盤面の高さ
        p1 (tuple[int, int]): プレイヤー1の初期位置（optional, デフォルトは左上隅(0, 0)）
        p2 (tuple[int, int]): プレイヤー2の初期位置（optional, デフォルトは右下隅(width-1, height-1)）
        turn (int): 最初の手番（1または2）
    """
    if p1 is None:
        # p1の初期座標
        p1 = (0, width//2 - 1) # デフォルトは左上隅
    if p2 is None:
        # p2の初期座標
        p2 = (height - 1, width//2 + 1) # デフォルトは右下隅
    # 初期配置が適切かチェック
    if not (0 <= p1[0] < height and 0 <= p1[1] < width):
        raise ValueError("プレイヤー1の初期位置が盤面の範囲外です")
    if not (0 <= p2[0] < height and 0 <= p2[1] < width):
        raise ValueError("プレイヤー2の初期位置が盤面の範囲外です")
    if p1 == p2:
        raise ValueError("プレイヤー1とプレイヤー2の初期位置が同じです")
    blocked = np.zeros((height, width), dtype=bool) # 全てのマスが空き（False）で初期化
    return GameState(width, height, blocked, p1, p2, turn)

# MARK: render
def render(state: GameState):
    """
    状態をテキストで表示する関数
        - P1の位置は '1'
        - P2の位置は '2'
        - 削除されたマスは '#'
        - 空きマスは '*
    """
    rows = []
    # 列番号を先頭に追加して、マスの内容を描画
    row_numbers = [f"{c} " for c in range(state.width)] # 列番号を上部に追加
    rows.append("".join(["   "] + row_numbers))
    for r in range(state.height):
        cells = [f"{r:2d}"] # 行番号を先頭に追加
        for c in range(state.width):
            if (r, c) == state.p1_pos:
                cells.append("1")
            elif (r, c) == state.p2_pos:
                cells.append("2")
            elif state.blocked[r][c]:
                cells.append("#")
            else:
                cells.append("*")
        rows.append(" ".join(cells))
    return "\n".join(rows)

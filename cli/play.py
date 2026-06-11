# CLIプログラム
import argparse
from core.game import play_game
from core.board import GameState
from agents.human import HumanAgent
from agents.simple import RandomAgent, GreedyAgent
from agents.minimax_agent import MinimaxAgent
from agents.alphabeta_agent import AlphaBetaAgent
from agents.iterative_agent import IterativeDeepeningAgent
from agents.mcts_agent import MCTSAgent

# MARK: CPU_CHOICES
# CPUエージェントの選択肢。コマンドライン引数や対話的な選択で使用する。
# 随時追加していくことができるように、文字列で指定する形式にしている。
CPU_CHOICES = [
    "random", "greedy-mobility", "greedy-reachable", "greedy-voronoi", # 貪欲エージェントの選択肢
    "minimax-mobility", "minimax-reachable", "minimax-voronoi", # ミニマックスエージェントの選択肢
    "alphabeta-mobility", "alphabeta-reachable", "alphabeta-voronoi",# アルファベータエージェントの選択肢
    "iterative-mobility", "iterative-reachable", "iterative-voronoi", # 反復深化エージェントの選択肢
    "mcts" # MCTSエージェント
] 

# MARK: build CPU
def build_cpu(kind: str, seed=None):
    """
    CPUエージェントを生成する関数
    Args:
        kind (str): エージェントの種類 ("random" または "greedy-*")
        seed (int, optional): 乱数シード (RandomAgentの場合)
    """
    if kind == "random": # ランダムエージェント
        return RandomAgent(name="CPU-Random", seed=seed)
    elif kind.startswith("greedy-"): # 貪欲エージェント
        eval_fn = kind.split("-", 1)[1]
        return GreedyAgent(name=f"CPU-Greedy-{eval_fn}", evaluation=eval_fn, seed=seed)
    elif kind.startswith("minimax-"): # ミニマックスエージェント
        eval_fn = kind.split("-", 1)[1]
        return MinimaxAgent(name=f"CPU-Minimax-{eval_fn}", depth=2, evaluation=eval_fn, seed=seed)
    elif kind.startswith("alphabeta-"): # アルファベータエージェント
        eval_fn = kind.split("-", 1)[1]
        return AlphaBetaAgent(name=f"CPU-AlphaBeta-{eval_fn}", depth=2, evaluation=eval_fn, seed=seed)
    elif kind.startswith("iterative-"): # 反復深化エージェント
        eval_fn = kind.split("-", 1)[1]
        return IterativeDeepeningAgent(name=f"CPU-Iterative-{eval_fn}", time_limit=1.0, evaluation=eval_fn, seed=seed)
    elif kind == "mcts": # MCTSエージェント
        return MCTSAgent(name="CPU-MCTS", time_limit=1.0, seed=seed)
    else:
        raise ValueError(f"不明なエージェントの種類: {kind}")

# MARK: prompt_choice
def prompt_choice(prompt, choices):
    """
    番号付きで選択肢を提示し、選ばれた要素を返す
    """
    for i, c in enumerate(choices, 1):
        print(f"  {i}. {c}")
    while True:
        raw = input(f"{prompt} (1-{len(choices)}): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print("-> 無効な選択です。")

# MARK: interactive_setup
def interactive_setup():
    """
    対話的にモード・盤サイズ・エージェントを決める
    """
    print("=== Isolation ===")
    print("モードを選んでください:")
    mode = prompt_choice("モード",
                         ["human-vs-human",
                          "human-vs-cpu",
                          "cpu-vs-cpu"])

    width = int(input("盤の幅 (例 5): ").strip() or "5")
    height = int(input("盤の高さ (例 5): ").strip() or "5")

    if mode == "human-vs-human":
        a1 = HumanAgent(name="Player-1")
        a2 = HumanAgent(name="Player-2")
    elif mode == "human-vs-cpu":
        a1 = HumanAgent(name="Player-1")
        print("相手CPUの種類:")
        a2 = build_cpu(prompt_choice("CPU", CPU_CHOICES), seed=0)
    else:  # cpu-vs-cpu
        print("CPU1の種類:")
        a1 = build_cpu(prompt_choice("CPU1", CPU_CHOICES), seed=0)
        print("CPU2の種類:")
        a2 = build_cpu(prompt_choice("CPU2", CPU_CHOICES), seed=1)

    return a1, a2, width, height

# MARK: main
def main():
    # コマンドライン引数の処理
    parser = argparse.ArgumentParser(description="Isolation CLI")
    parser.add_argument("--mode",
                        choices=["hvh", "hvc", "cvc"],
                        help="hvh=人vs人, hvc=人vsCPU, cvc=CPUvsCPU")
    parser.add_argument("--width", type=int, default=5)
    parser.add_argument("--height", type=int, default=5)
    parser.add_argument("--cpu1", choices=CPU_CHOICES, default="greedy-voronoi")
    parser.add_argument("--cpu2", choices=CPU_CHOICES, default="greedy-mobility")
    args = parser.parse_args()

    # コマンドライン引数がない場合は対話的に設定。ある場合は引数から設定。
    if args.mode is None:
        a1, a2, width, height = interactive_setup()
    else:
        width, height = args.width, args.height
        if args.mode == "hvh":
            a1, a2 = HumanAgent(name="Player-1"), HumanAgent(name="Player-2")
        elif args.mode == "hvc":
            a1 = HumanAgent(name="Player-1")
            a2 = build_cpu(args.cpu2, seed=0)
        else:
            a1 = build_cpu(args.cpu1, seed=0)
            a2 = build_cpu(args.cpu2, seed=1)

    # 人間が関与するかどうかで verbose を切り替える
    human_involved = isinstance(a1, HumanAgent) or isinstance(a2, HumanAgent)

    print(f"\nP1 = {a1.name} / P2 = {a2.name}  盤 {width}x{height}\n")
    result = play_game(a1, a2, width=width, height=height,
                       verbose=not human_involved)

    print("\n=== 終局 ===")
    winner_name = a1.name if result.winner == 1 else a2.name
    print(f"勝者: P{result.winner} ({winner_name})  "
          f"総手数: {result.moves}  理由: {result.reason}")

if __name__ == "__main__":
    main()
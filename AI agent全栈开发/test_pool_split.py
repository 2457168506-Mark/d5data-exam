from pool_split import split_pool, split_pool_0
import random


# 基础测试用例：(奖池, 权重列表)
cases = [
    # 题目自带的例子：原函数会少发
    (10000, [1, 1, 1]),
    # 原函数会多发的例子
    (3, [1, 1]),
    # 大奖池
    (999999, [7, 13, 19, 23]),
]

# 边界用例：权重 / 奖池的极端取值
edge_cases = [
    (100, [0, 1, 1]),      # 有人权重为 0，应分到 0
    (100, [5]),            # 只有一个人，独吞全部
    (10, [999999, 1]),     # 权重差距极大，小权重者可能分到 0
    (1, [1, 1, 1, 1]),     # 池子比分的人数还少
    (0, [1, 2, 3]),        # 奖池为 0
    (2, [3, 3, 3]),        # 池子小于总权重
]

# 异常输入：总权重为 0 应报错；负数输入不报错但结果无业务意义
error_cases = [
    (100, [0, 0, 0]),      # 总权重为 0，应抛 ZeroDivisionError
    (-100, [1, 1, 1]),     # 奖池为负数
    (100, [1, -1, 1]),     # 权重里出现负数
]


def run_test(name, pool, weights):
    result_old = split_pool_0(pool, weights)
    result_new = split_pool(pool, weights)
    ok_old = sum(result_old) == pool
    ok_new = sum(result_new) == pool

    print(f"--- Case: {name} ---")
    print(f"  pool={pool}, weights={weights}")
    print(f"  旧函数: {result_old}  sum={sum(result_old)}  {'✓' if ok_old else '✗'}")
    print(f"  新函数: {result_new}  sum={sum(result_new)}  {'✓' if ok_new else '✗'}")
    print()

    # 新函数必须通过；旧函数用来展示原实现会出问题的场景
    assert ok_new, f"新函数在 pool={pool}, weights={weights} 上失败"


def run_edge_test(pool, weights):
    result = split_pool(pool, weights)
    total = sum(weights)
    ok = sum(result) == pool
    # 每个人与向下取整的基础份额最多相差 1 分
    ok = ok and all(
        result[i] in (pool * w // total, pool * w // total + 1)
        for i, w in enumerate(weights)
    )

    print(f"--- Edge: pool={pool}, weights={weights} ---")
    print(f"  新函数: {result}  sum={sum(result)}  {'✓' if ok else '✗'}")
    print()
    assert ok, f"边界用例失败: pool={pool}, weights={weights}"


def run_error_test(pool, weights):
    print(f"--- Error: pool={pool}, weights={weights} ---")
    try:
        result = split_pool(pool, weights)
    except ZeroDivisionError:
        print("  新函数: 抛出 ZeroDivisionError ✓（总权重为 0，应报错）")
        print()
        return

    # 负数输入不会报错，但结果无业务意义，只校验和不变式仍成立
    ok = sum(result) == pool
    print(f"  新函数: {result}  sum={sum(result)}  {'✓ 和不变式成立（负数输入属异常，函数不报错）' if ok else '✗'}")
    print()
    assert ok, f"异常输入下和不变式被破坏: pool={pool}, weights={weights}"


def random_test(rounds=500, seed=42):
    """随机数字测试：任意非负奖池 + 非负权重。

    校验三条不变式：
    1. 所有人的钱加起来正好等于奖池；
    2. 每个人与向下取整的基础份额最多相差 1 分，且不为负；
    3. 相同输入跑两次，结果固定一致。
    """
    rng = random.Random(seed)
    checked = 0
    for r in range(rounds):
        n = rng.randint(1, 10)
        pool = rng.randint(0, 10**6)
        weights = [rng.randint(0, 100) for _ in range(n)]
        total = sum(weights)
        if total == 0:
            continue  # 全零权重属异常输入，在 error_cases 里单独测
        result = split_pool(pool, weights)

        assert sum(result) == pool, f"第 {r} 轮: 总和 {sum(result)} != 奖池 {pool}"
        for i, w in enumerate(weights):
            base = pool * w // total
            assert result[i] in (base, base + 1), \
                f"第 {r} 轮: 第 {i} 人 {result[i]} 超出 [{base}, {base + 1}]"
            assert result[i] >= 0
        assert split_pool(pool, weights) == result, f"第 {r} 轮: 结果不固定"
        checked += 1

    print(f"--- Random ---")
    print(f"  随机测试通过：{checked} 轮（总和不变式 + 每人误差 <= 1 分 + 结果固定）✓")
    print()


for pool, weights in cases:
    run_test(f"pool={pool}, weights={weights}", pool, weights)

for pool, weights in edge_cases:
    run_edge_test(pool, weights)

for pool, weights in error_cases:
    run_error_test(pool, weights)

random_test()

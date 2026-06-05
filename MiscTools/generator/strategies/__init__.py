"""谜题生成策略（可插拔）。

每种策略实现 GenerationStrategy 接口，只负责产出候选 region_grid，
不保证唯一解；唯一性由 pipeline 的 uniqueness 模块统一校验。
"""

from .base import GenerationStrategy
from .random_carve import RandomCarveStrategy
from .progressive import ProgressiveStrategy
from .shape import ShapeStrategy, TEMPLATES

# 策略注册表：CLI 通过 --strategy <name> 选择。新增策略在此登记即可。
# 注：曾试过 staircase（楼梯/带状），但带状区域几乎不产唯一解（6x6 起命中率→0），已移除。
STRATEGIES = {
    'random': RandomCarveStrategy,
    'progressive': ProgressiveStrategy,
}
# 每个图案模板注册为一个 shape-<名字> 策略
for _shape in TEMPLATES:
    STRATEGIES[f'shape-{_shape}'] = (lambda s: (lambda: ShapeStrategy(s)))(_shape)


def get_strategy(name):
    """按名称返回策略实例，未知名称抛 KeyError。"""
    return STRATEGIES[name]()

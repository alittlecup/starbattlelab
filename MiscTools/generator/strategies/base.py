"""生成策略抽象接口。

设计要点：pipeline（唯一解校验、去重、按尺寸保存、渲染）与具体生成算法完全解耦。
新增策略（思路 B、形状约束等）只需实现本接口并在 STRATEGIES 注册。
"""

from abc import ABC, abstractmethod


class GenerationStrategy(ABC):
    """谜题区域划分策略。"""

    #: 供 CLI / 日志展示的策略名。
    name = "base"

    @abstractmethod
    def generate(self, size, stars, rng):
        """产出一个候选区域划分。

        :param int size: 网格边长（4~14）。
        :param int stars: 每区星数（影响区域数量约束的语义，本接口仅透传）。
        :param random.Random rng: 随机源（由调用方注入，便于并行/复现）。
        :returns: size×size 的 region_grid，区域 id 从 1 起、连续、共 size 个连通区域。
                  无法产出合法划分时返回 None（调用方会重试）。
        :rtype: list[list[int]] | None
        """
        raise NotImplementedError

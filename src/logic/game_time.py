from dataclasses import dataclass
from typing import ClassVar

from src.config import GameTimeConfig as config

@dataclass(order=True, frozen=True)
class GameTime:
    """
    Represents game time in Arknights, including cost and ticks.

    Attributes:
        cost (int): The in-game cost.
        tick (int): The current tick count.

    Class Attributes:
        TICK_MAX (int): The maximum value of ticks. Can be set globally.

    Methods:
        set_tick_max: Set the global maximum value of ticks.
        __add__: Add two GameTime instances.
        __sub__: Subtract one GameTime instance from another.
    """
    cost: int
    tick: int

    TICK_MAX: ClassVar[int] = config.TICK_MAX_DEFAULT

    def __post_init__(self):
        # Ensure the ticks are within the valid range
        object.__setattr__(self, 'cost', self.cost + self.tick // self.TICK_MAX)
        object.__setattr__(self, 'tick', self.tick % self.TICK_MAX)

    @classmethod
    def set_tick_max(cls, max_value: int):
        """Set the global maximum tick value."""
        if max_value <= 0:
            raise ValueError("TICK_MAX must be a positive integer.")
        cls.TICK_MAX = max_value
    
    @classmethod
    def get_tick_max(cls) -> int:
        """Get the global maximum tick value."""
        return cls.TICK_MAX

    def __add__(self, other: 'GameTime') -> 'GameTime':
        total_cost = self.cost + other.cost + (self.tick + other.tick) // self.TICK_MAX
        total_tick = (self.tick + other.tick) % self.TICK_MAX
        return GameTime(total_cost, total_tick)

    def __sub__(self, other: 'GameTime') -> 'GameTime':
        total_cost = self.cost - other.cost + (self.tick - other.tick) // self.TICK_MAX
        total_tick = (self.tick - other.tick) % self.TICK_MAX
        return GameTime(total_cost, total_tick)

if __name__ == "__main__":
    GameTime.set_tick_max(30)

    time1 = GameTime(cost=50, tick=10)
    time2 = GameTime(20, 25)

    # Test and Print
    print(time1)
    print(time2)
    print(f"time1 + time2 = {time1 + time2}")
    print(f"time1 - time2 = {time1 - time2}")
    print(f"time1 < time2 = {time1 < time2}")
    print(f"time1 == time2 = {time1 == time2}")
    print(f"time1 > time2 = {time1 > time2}")

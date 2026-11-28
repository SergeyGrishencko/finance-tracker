from enum import Enum


class StatsGroupBy(Enum):
    """Шаг группировки статистики: по дням или по месяцам."""

    DAY = "day"
    MONTH = "month"


class TransactionType(Enum):
    """Тип финансовой операции: доход или расход."""

    INCOME = "income"
    EXPENSE = "expense"

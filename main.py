class CoffeeOrder:
    def __init__(
        self,
        base: str,
        size: str,
        milk: str = "none",
        syrups: tuple[str, ...] = (),
        sugar: int = 0,
        iced: bool = False,
        pricing: dict | None = None,
    ):
        self.base = base
        self.size = size
        self.milk = milk
        self.syrups = syrups
        self.sugar = sugar
        self.iced = iced
        self.price = self._calculate_price(pricing)
        self.description = self._generate_description()

    def _calculate_price(self, pricing: dict) -> float:
        base_price = pricing["base_prices"][self.base]
        size_multiplier = pricing["size_multipliers"][self.size]
        milk_price = pricing["milk_prices"][self.milk]
        syrup_price = pricing["syrup_price"] * len(self.syrups)
        ice_price = pricing["ice_price"] if self.iced else 0
        total = (base_price + milk_price + syrup_price) * size_multiplier
        total += ice_price
        return float(total)

    def _generate_description(self) -> str:
        extra_parts = []
        if self.milk != "none":
            extra_parts.append(f"with {self.milk} milk")
        if self.syrups:
            extra_parts.append(f"+{', '.join(self.syrups)}")
        if self.iced:
            extra_parts.append("(iced)")
        if self.sugar > 0:
            extra_parts.append(f"{self.sugar} tsp sugar")

        if not extra_parts:
            return "" 
        else:
            return f"{self.size} {self.base} " + " ".join(extra_parts).strip()

    def __str__(self) -> str:
        if not self.description.strip():
            return f"{self.price:.2f} RUB"
        return self.description


class CoffeeOrderBuilder:
    """
    Fluent builder для создания неизменяемых заказов кофе.
    Правила:
    - Обязательные поля: base и size.
    - Сиропы: до 4, дубликаты игнорируются, добавление сверх лимита — ValueError.
    - Сахар: 0–5 ч.л., выход за пределы — ValueError.
    - Молоко: whole/skim (+30), oat (+60), soy (+50), none (0).
    - Сироп: +40 за каждый.
    - Лёд: +20 (фиксировано).
    - Размер: small (x1.0), medium (x1.2), large (x1.4).
    """
    BASE_PRICES = {
        "espresso": 200,
        "americano": 250,
        "latte": 300,
        "cappuccino": 320,
    }
    SIZE_MULTIPLIERS = {
        "small": 1.0,
        "medium": 1.2,
        "large": 1.4,
    }
    MILK_PRICES = {
        "whole": 30,
        "skim": 30,
        "oat": 60,
        "soy": 50,
        "none": 0,
    }
    SYRUP_PRICE = 40
    ICE_PRICE = 20
    MAX_SYRUPS = 4
    MAX_SUGAR = 5

    def __init__(self):
        self.base = None
        self.size = None
        self.milk = "none"
        self.syrups = set()
        self.sugar = 0
        self.iced = False

    def set_base(self, base: str):
        if base not in self.BASE_PRICES:
            raise ValueError(f"Base must be one of: {', '.join(self.BASE_PRICES)}")
        self.base = base
        return self

    def set_size(self, size: str):
        if size not in self.SIZE_MULTIPLIERS:
            raise ValueError(f"Size must be one of: {', '.join(self.SIZE_MULTIPLIERS)}")
        self.size = size
        return self

    def set_milk(self, milk: str):
        if milk not in self.MILK_PRICES:
            raise ValueError(f"Milk must be one of: {', '.join(self.MILK_PRICES)}")
        self.milk = milk
        return self

    def add_syrup(self, name: str):
        if len(self.syrups) >= self.MAX_SYRUPS:
            raise ValueError(f"Maximum {self.MAX_SYRUPS} syrups allowed")
        self.syrups.add(name)
        return self

    def set_sugar(self, teaspoons: int):
        if not (0 <= teaspoons <= self.MAX_SUGAR):
            raise ValueError(f"Sugar must be between 0 and {self.MAX_SUGAR}")
        self.sugar = teaspoons
        return self

    def set_iced(self, iced: bool = True):
        self.iced = iced
        return self

    def clear_extras(self):
        self.milk = "none"
        self.syrups.clear()
        self.sugar = 0
        self.iced = False
        return self

    def build(self) -> CoffeeOrder:
        if self.base is None:
            raise ValueError("Base is required")
        if self.size is None:
            raise ValueError("Size is required")
        pricing = {
            "base_prices": self.BASE_PRICES,
            "size_multipliers": self.SIZE_MULTIPLIERS,
            "milk_prices": self.MILK_PRICES,
            "syrup_price": self.SYRUP_PRICE,
            "ice_price": self.ICE_PRICE,
        }
        return CoffeeOrder(
            self.base,
            self.size,
            self.milk,
            tuple(self.syrups),
            self.sugar,
            self.iced,
            pricing,
        )


# Минимальные тесты
if __name__ == "__main__":
    print("=== Minimal tests ===")
    builder = CoffeeOrderBuilder()
    order = (
        builder
        .set_base("latte")
        .set_size("medium")
        .set_milk("oat")
        .add_syrup("vanilla")
        .set_sugar(2)
        .set_iced(True)
        .build()
    )
    assert isinstance(order, CoffeeOrder)
    assert isinstance(order.price, float)
    assert order.price > 0
    assert order.base == "latte"
    assert order.size == "medium"
    assert order.milk == "oat"
    assert "vanilla" in order.syrups
    assert order.sugar == 2
    assert order.iced is True
    print("Basic order test passed")

    order1 = order
    order2 = (
        builder
        .set_milk("soy")
        .set_iced(False)
        .add_syrup("caramel")
        .build()
    )
    assert order1 is not order2
    assert order1.price != order2.price
    assert order1.milk != order2.milk
    assert order2.milk == "soy"
    assert order2.price > 0
    print("Reuse builder test passed")

    try:
        CoffeeOrderBuilder().set_size("small").build()
        assert False, "ValueError expected for missing base"
    except ValueError:
        print("Missing base validation passed")

    try:
        CoffeeOrderBuilder().set_base("espresso").build()
        assert False, "ValueError expected for missing size"
    except ValueError:
        print("Missing size validation passed")

    try:
        CoffeeOrderBuilder().set_base("latte").set_size("small").set_sugar(6)
        assert False, "ValueError expected for sugar > 5"
    except ValueError:
        print("Sugar limit validation passed")

    try:
        b = CoffeeOrderBuilder().set_base("latte").set_size("small")
        b.add_syrup("a").add_syrup("b").add_syrup("c").add_syrup("d").add_syrup("e")
        assert False, "ValueError expected for syrup overflow"
    except ValueError:
        print("Syrup limit validation passed")

    b = CoffeeOrderBuilder().set_base("latte").set_size("small")
    b.add_syrup("vanilla").add_syrup("vanilla")
    order = b.build()
    assert len(order.syrups) == 1
    print("Duplicate syrup logic passed")

    b = CoffeeOrderBuilder().set_base("espresso").set_size("small")
    price_no_ice = b.build().price
    price_ice = b.set_iced(True).build().price
    assert price_ice > price_no_ice
    print("Iced surcharge logic passed")

    order_empty = CoffeeOrderBuilder().set_base("espresso").set_size("small").build()
    assert str(order_empty) == "200.00 RUB"
    print("Empty description → price only: passed")

    order_full = (
        CoffeeOrderBuilder()
        .set_base("latte")
        .set_size("large")
        .set_milk("oat")
        .add_syrup("vanilla")
        .set_iced(True)
        .build()
    )
    full_str = str(order_full)
    assert "large latte" in full_str
    assert "oat" in full_str
    assert "vanilla" in full_str
    assert "(iced)" in full_str
    print("Full description test passed")

    print("=== All tests passed ===")
import random
import mesa_geo as mg


class HouseAgent(mg.GeoAgent):
    """A house agent that can be a grower, buyer, or non-participant in trading."""

    GROWER = "grower"
    BUYER = "buyer"
    NON_PARTICIPANT = "non_participant"

    def __init__(self, model, geometry, crs, house_type=None):
        super().__init__(model, geometry, crs)

        self.house_type = house_type or random.choice(
            [self.GROWER, self.BUYER, self.NON_PARTICIPANT]
        )

        # Trading attributes
        self.inventory = 0.0
        self.money = 100.0

        if self.house_type == self.GROWER:
            self.production_rate = random.uniform(1.0, 5.0)
            self.sell_price = random.uniform(5.0, 15.0)
        elif self.house_type == self.BUYER:
            self.demand_rate = random.uniform(1.0, 3.0)
            self.max_buy_price = random.uniform(8.0, 20.0)
        # Non-participants have no trading attributes

    def step(self):
        if self.house_type == self.GROWER:
            self._grower_step()
        elif self.house_type == self.BUYER:
            self._buyer_step()
        # Non-participants do nothing

    def _grower_step(self):
        """Produce goods each step."""
        self.inventory += self.production_rate

    def _buyer_step(self):
        """Try to buy from a nearby grower."""
        growers = [
            a for a in self.model.house_agents
            if a.house_type == self.GROWER and a.inventory > 0
        ]
        if not growers:
            return

        # Pick a random grower to buy from
        seller = random.choice(growers)
        amount = min(self.demand_rate, seller.inventory)
        cost = amount * seller.sell_price

        if cost <= self.money:
            seller.inventory -= amount
            seller.money += cost
            self.money -= cost

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

        # Food attributes
        self.inventory = 0.0  # kg of fresh produce stored

        if self.house_type == self.GROWER:
            
            # Arbitrary production
            self.production_min = random.uniform(0.3, 0.8)
            self.production_max = random.uniform(1.2, 2.5)
            
            # Arbitrary consumption
            self.consumption_min = random.uniform(0.3, 0.6)
            self.consumption_max = random.uniform(0.8, 1.5)
            
            # Starting food
            self.inventory = random.uniform(2.0, 5.0)
        elif self.house_type == self.BUYER:
            # Arbitrary demand
            self.demand_min = random.uniform(0.5, 1.0)
            self.demand_max = random.uniform(1.5, 3.0)
            
            # Arbitrary consumption
            self.consumption_min = random.uniform(0.3, 0.6)
            self.consumption_max = random.uniform(0.8, 1.5)
            # Starting food
            self.inventory = random.uniform(0.0, 2.0)

    def step(self):
        if self.house_type == self.GROWER:
            self._grower_step()
        elif self.house_type == self.BUYER:
            self._buyer_step()
        # Non-participants do nothing

    def _apply_consumption(self):
        """Apply daily household consumption — amount varies each day."""
        daily_consumption = random.uniform(self.consumption_min, self.consumption_max)
        self.inventory -= daily_consumption
        # Cannot go below zero
        self.inventory = max(0.0, self.inventory)

    def _grower_step(self):
        """Produce fresh food from backyard garden, then consume."""
        # Harvest varies day-to-day (weather, season, etc.)
        daily_production = random.uniform(self.production_min, self.production_max)
        self.inventory += daily_production
        # Apply household consumption
        self._apply_consumption()

    def _buyer_step(self):
        """Try to receive food from a grower, then consume."""
        growers = [
            a for a in self.model.house_agents
            if a.house_type == self.GROWER and a.inventory > 0
        ]
        if growers:
            seller = random.choice(growers)
            # Demand varies day-to-day
            daily_demand = random.uniform(self.demand_min, self.demand_max)
            amount = min(daily_demand, seller.inventory)
            seller.inventory -= amount
            self.inventory += amount

        # Apply household consumption
        self._apply_consumption()

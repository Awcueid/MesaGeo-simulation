import random
import mesa_geo as mg


class HouseAgent(mg.GeoAgent):
    """A house agent that can be a grower, buyer, or non-participant in trading."""

    GROWER = "grower"
    BUYER = "buyer"
    NON_PARTICIPANT = "non_participant"
    
    # Crop types and production/consumption rates (kg per day)
    CROPS = {
        'tomatoes': {
            'production_min': 6.0,
            'production_max': 12.0,
            'consumption_min': 0.100,
            'consumption_max': 0.125,
        },
        'lettuce': {
            'production_min': 3.0,
            'production_max': 5.0,
            'consumption_min': 0.055,
            'consumption_max': 0.075,
        },
        'herbs': {
            'production_min': 1.0,
            'production_max': 2.0,
            'consumption_min': 0.010,
            'consumption_max': 0.020,
        },
    }

    def __init__(self, model, geometry, crs, house_type=None, consumption_rate=1.0):
        super().__init__(model, geometry, crs)

        self.house_type = house_type or random.choice(
            [self.GROWER, self.BUYER, self.NON_PARTICIPANT]
        )

        # Food attributes - inventory for each crop type
        self.inventory = {
            'tomatoes': 0.0,
            'lettuce': 0.0,
            'herbs': 0.0
        }

        if self.house_type == self.GROWER:
            # Starting inventory for growers
            self.inventory = {
                'tomatoes': random.uniform(5.0, 10.0),
                'lettuce': random.uniform(3.0, 6.0),
                'herbs': random.uniform(1.0, 3.0)
            }
        elif self.house_type == self.BUYER:
            # Consumption Rate
            self.demand_min = consumption_rate * 0.8
            self.demand_max = consumption_rate * 2.0
            
            # Starting inventory for buyers
            self.inventory = {
                'tomatoes': random.uniform(5.0, 10.0),
                'lettuce': random.uniform(3.0, 6.0),
                'herbs': random.uniform(1.0, 3.0)
            }

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
        """Try to receive food from one of the nearest 5 growers, then consume."""
        growers = [
            a for a in self.model.house_agents
            if a.house_type == self.GROWER and a.inventory > 0
        ]
        if growers:
            # Sort growers by distance to this buyer (nearest first)
            growers_by_distance = sorted(growers,key=lambda g: self.geometry.distance(g.geometry))
            
            # Pick randomly from the nearest 5
            seller = random.choice(growers_by_distance[:5])
            # Demand varies day-to-day
            daily_demand = random.uniform(self.demand_min, self.demand_max)
            amount = min(daily_demand, seller.inventory)
            seller.inventory -= amount
            self.inventory += amount

        # Apply household consumption
        self._apply_consumption()

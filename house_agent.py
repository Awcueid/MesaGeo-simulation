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

    def __init__(self, model, geometry, crs, house_type=None, consumption_rate=1.0, specialized_crop=None):
        super().__init__(model, geometry, crs)

        self.house_type = house_type or random.choice([self.GROWER, self.BUYER, self.NON_PARTICIPANT])
        self.specialized_crop = specialized_crop or random.choice(list(self.CROPS.keys()))

        crop_def = self.CROPS[self.specialized_crop]
        self.production_min = crop_def['production_min']
        self.production_max = crop_def['production_max']
        self.consumption_min = crop_def['consumption_min']
        self.consumption_max = crop_def['consumption_max']

        # Food attributes - inventory for each crop type
        self.inventory = {
            crop_name: crop_info['consumption_max']
            for crop_name, crop_info in self.CROPS.items()
        }

        if self.house_type == self.GROWER:
            
            self.inventory[self.specialized_crop] = random.uniform(self.production_min, self.production_max)
            
        elif self.house_type == self.BUYER:

            self.inventory[self.specialized_crop] = random.uniform(self.consumption_min, self.consumption_max)

    def step(self):
        if self.house_type == self.GROWER:
            self._grower_step()
        elif self.house_type == self.BUYER:
            self._buyer_step()
        # Non-participants do nothing

    def _apply_consumption(self):
        """Apply daily household consumption for all crops"""
        for crop_name, crop_info in self.CROPS.items():
            daily_consumption = random.uniform(crop_info['consumption_min'],crop_info['consumption_max'],)
            self.inventory[crop_name] = max(
                0.0,
                self.inventory[crop_name] - daily_consumption,
            )

    def _grower_step(self):
        """Produce fresh food from backyard garden, then consume."""
        
        #calculate production
        daily_production = random.uniform(self.production_min, self.production_max)
        
        self.inventory[self.specialized_crop] += daily_production
        self._apply_consumption()

    def _buyer_step(self):
        """Buy food from nearby growers when a crop reserve gets too low, then consume."""
        for crop_name, crop_info in self.CROPS.items():
            reserve_target = crop_info['consumption_max'] * 2.0
            if self.inventory[crop_name] >= reserve_target:
                continue

            growers = [
                a for a in self.model.house_agents
                if a.house_type == self.GROWER and a.inventory.get(crop_name, 0.0) > 0
            ]
            if not growers:
                continue

            growers_by_distance = sorted(
                growers,
                key=lambda g: self.geometry.distance(g.geometry),
            )

            shortage = reserve_target - self.inventory[crop_name]
            for seller in growers_by_distance[:3]:
                if shortage <= 0:
                    break

                available = seller.inventory.get(crop_name, 0.0)
                if available <= 0:
                    continue

                amount = min(shortage, available)
                seller.inventory[crop_name] -= amount
                self.inventory[crop_name] += amount
                shortage -= amount

        self._apply_consumption()

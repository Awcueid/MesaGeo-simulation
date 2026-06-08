import geopandas as gpd
import mesa
from mesa.datacollection import DataCollector
import random
import mesa_geo as mg
from shapely.geometry import Point
from datetime import datetime, timedelta
from house_agent import HouseAgent


class Trading_model(mesa.Model):
    """Trading simulation model with house agents (growers, buyers, non-participants)."""

    def __init__(self, non_participant_pct=30, grower_share_pct=50, grower_production_rate=1.5, consumption_rate=1.0):
        super().__init__()

        # Convert UI percentages to internal proportions.
        non_participant_pct = max(0.0, min(100.0, non_participant_pct)) / 100.0
        grower_share_pct = max(0.0, min(100.0, grower_share_pct)) / 100.0


        participant_pct = 1.0 - non_participant_pct
        grower_pct = participant_pct * grower_share_pct
        buyer_pct = participant_pct * (1.0 - grower_share_pct)

        # Store configurable rates
        self.grower_production_rate = grower_production_rate
        self.consumption_rate = consumption_rate

        self.start_date = datetime(2026, 1, 1)
        self.current_date = self.start_date
        self.space = mg.GeoSpace(warn_crs_conversion=False) 
        self.running = True

        # Read in the geojson files
        road_path = "Maps/Roads.geojson"
        buildings_path = "Maps/Buildings.geojson"

        # Set up roads (visual only)
        roads_comp = gpd.read_file(road_path).to_crs(epsg=3857)
        road_agents = [mg.GeoAgent(self, geometry=geom, crs=roads_comp.crs) for geom in roads_comp.geometry]
        self.space.add_agents(road_agents)

        # Set up buildings as house agents
        buildings_comp = gpd.read_file(buildings_path).to_crs(epsg=3857)
        self.house_agents = []
        for _, row in buildings_comp.iterrows():
            roll = random.random()
            if roll < grower_pct:
                house_type = HouseAgent.GROWER
            elif roll < grower_pct + buyer_pct:
                house_type = HouseAgent.BUYER
            else:
                house_type = HouseAgent.NON_PARTICIPANT

            agent = HouseAgent(
                model=self,
                geometry=row.geometry,
                crs=buildings_comp.crs,
                house_type=house_type,
                grower_production_rate=self.grower_production_rate,
                consumption_rate=self.consumption_rate,
            )
            agent.OBJECTID = row["OBJECTID"]
            self.house_agents.append(agent)

        self.space.add_agents(self.house_agents)

        self.datacollector = DataCollector(
            model_reporters={
                "avg_food_inventory": lambda m: (
                    sum(a.inventory for a in m.house_agents if hasattr(a, "inventory"))
                    / max(1, sum(1 for a in m.house_agents if hasattr(a, "inventory")))
                ),
            }
        )
        self.datacollector.collect(self)

    def step(self):
        """Run one step of the model — each step is one day."""
        self.current_date += timedelta(days=1)

        for agent in self.house_agents:
            agent.step()

        self.datacollector.collect(self)
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

    def __init__(self, grower_pct=0.3, buyer_pct=0.4):
        super().__init__()

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
            )
            agent.OBJECTID = row["OBJECTID"]
            self.house_agents.append(agent)

        self.space.add_agents(self.house_agents)

    def step(self):
        """Run one step of the model — each step is one day."""
        self.current_date += timedelta(days=1)

        for agent in self.house_agents:
            agent.step()

        if hasattr(self, "datacollector"):
            self.datacollector.collect(self)
import geopandas as gpd
import mesa
import random
import mesa_geo as mg
from mesa_geo import AgentCreator


class Car_agent(mg.GeoAgent):
    """Car agent."""

    def __init__(self, model, geometry, crs,):
        """Create a new car agent."""

        super().__init__(model, geometry, crs)


    def step(self):
        """Advance agent one step."""




class Road_agent(mg.GeoAgent):
    """Schelling segregation agent."""

    def __init__(self, model, geometry, crs):
        """Create a new Schelling agent.

        Args:
            agent_type: Indicator for the agent's type (minority=1, majority=0)
        """
        super().__init__(model, geometry, crs)


    def step(self):
        """Advance agent one step."""

    def __repr__(self):
        return "Agent " + str(self.unique_id)




class Main_model(mesa.Model):
    """Model class for the Schelling segregation model."""

    def __init__(self, num_of_cars=100, speed_limit=40):
        super().__init__()

        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.running = True

        # read in the geojson files
        ac = mg.AgentCreator(Road_agent, model=self)
        road_path = "Roads.geojson"
        buildings_path = "Buildings.geojson"

        # Set up roads
        roads_comp = gpd.read_file(road_path)
        road_agents = ac.from_GeoDataFrame(roads_comp)
        self.space.add_agents(road_agents)

        # Set up buildings
        buildings_comp = gpd.read_file(buildings_path)
        buildings_agents = ac.from_GeoDataFrame(buildings_comp)
        self.space.add_agents(buildings_agents)
        
        # Set up cars
        car_ac = mg.AgentCreator(Car_agent, model=self,crs=roads_comp.crs)
        car_agents = []
        for i in range(num_of_cars):
            # Create car agents with random positions 
            random_road = roads_comp.sample(1).geometry.values[0]  # Randomly select a road
            random_point = random_road.interpolate(random.uniform(0, random_road.length)) # Randomly place the car on the road
            car_agent = car_ac.create_agent(
                geometry=random_point,
            )
            
            car_agents.append(car_agent)
        self.space.add_agents(car_agents)


    def step(self):
        """Run one step of the model."""
        for agent in self.space.agents:
                agent.step()

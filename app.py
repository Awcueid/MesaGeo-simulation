import solara
from mesa.visualization import Slider, SolaraViz
from mesa_geo.visualization import make_geospace_component
from traffic_simulation import Main_model
from trading_simulation import Trading_model
from car_agent import test_car
from bicycle_agent import Bicycle_agent, test_bicycle
from pedestrian_agent import Pedestrian_agent, test_pedestrian
from house_agent import HouseAgent

model_params = {
    # sliders for model parameters
    "num_of_cars": Slider("Number of Cars", 30, 0, 1000, 1),
}

def Time(model):
    total_seconds = int(model.sim_time.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    time_str = f"{minutes:02d}:{seconds:02d}"
    return solara.Text(f"Simulation time: {time_str}")


def VehicleLegend():
    return solara.Markdown(
        """### Vehicle legend
- **Purple**: Cars
- **Green**: Bicycles
- **Blue**: Pedestrians
- **Red**: Test agents (car/bicycle/pedestrian)
"""
    )


def Main_draw(agent):

    geom_type = agent.geometry.geom_type

    # Static geometries — buildings and roads
    if geom_type in ("Polygon"):
        if hasattr(agent, "_static_portrayal"):
            return agent._static_portrayal

        # Polygon (buildings) — only draw target buildings in red
        TARGET_BUILDING_IDS = {'HOSPITAL_1', 'HOSPITAL_2', 'NEW_APARTMENT'}
        if not hasattr(agent, "_is_target_building"):
            agent._is_target_building = getattr(agent, "OBJECTID", None) in TARGET_BUILDING_IDS

        if not agent._is_target_building:
            invisible = {
                "opacity": 0,
                "fillOpacity": 0,
                "weight": 0,
                "stroke": False,
                "fill": False,
            }
            agent._static_portrayal = invisible
            return invisible

        portrayal = {"color": "red", "fillColor": "red", "fillOpacity": 0.5, "weight": 2}
        agent._static_portrayal = portrayal
        return portrayal

    # Dynamic agents (points)
    if isinstance(agent, test_car):
        portrayal = {
            "type": "point",
            "color": "red",  # special agent
            "radius": 5,
        }
    elif isinstance(agent, test_bicycle):
        portrayal = {
            "type": "point",
            "color": "red",  # test bicycle
            "radius": 5,
        }
    elif isinstance(agent, test_pedestrian):
        portrayal = {
            "type": "point",
            "color": "red",  # test pedestrian
            "radius": 5,
        }
    elif isinstance(agent, Bicycle_agent):
        portrayal = {
            "type": "point",
            "color": "green",  # bicycles
            "radius": 4,
        }
    elif isinstance(agent, Pedestrian_agent):
        portrayal = {
            "type": "point",
            "color": "blue",  # pedestrians
            "radius": 3,
        }
    elif geom_type == "Point":
        portrayal = {
            "type": "point",
            "color": "purple",  # regular cars
            "radius": 5,
        }
    else:
        # Fallback
        portrayal = {"type": "point", "color": "gray", "radius": 3}
    return portrayal


_raw_main_draw = Main_draw
def Main_draw(agent):  # noqa: F811
    result = _raw_main_draw(agent)
    return result if isinstance(result, dict) else {}




def test_agent_progress_plot(model):
    """Return a Solara line chart comparing test agents' progress over time."""

    if not hasattr(model, "datacollector"):
        return solara.Text("No data collector available")

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty:
        return solara.Text("No data yet")

    return solara.LineChart(
        df,
        x="step",
        y=[
            "test_car_progress",
            "test_bicycle_progress",
            "test_pedestrian_progress",
        ],
        colors=["red", "orange", "yellow"],
    )

trading_model_params = {
    "grower_pct": Slider("Grower %", 0.3, 0.0, 1.0, 0.05),
    "buyer_pct": Slider("Buyer %", 0.4, 0.0, 1.0, 0.05),
}


def Trading_draw(agent):
    """Draw function for the trading simulation (bicycles, pedestrians, buildings)."""
    geom_type = agent.geometry.geom_type

    # House agents — color by type
    if isinstance(agent, HouseAgent):
        color_map = {
            HouseAgent.GROWER: "#2ecc71",          # green
            HouseAgent.BUYER: "#e67e22",            # orange
            HouseAgent.NON_PARTICIPANT: "#95a5a6",  # gray
        }
        fill_map = {
            HouseAgent.GROWER: "#27ae60",
            HouseAgent.BUYER: "#d35400",
            HouseAgent.NON_PARTICIPANT: "#7f8c8d",
        }
        c = color_map.get(agent.house_type, "gray")
        f = fill_map.get(agent.house_type, "gray")
        return {"color": c, "fillColor": f, "fillOpacity": 0.7, "weight": 1}

    return {"type": "point", "color": "gray", "radius": 3}


def TradingLegend(model=None):
    return solara.Markdown(
        """### Trading Simulation Legend
- **Green**: Grower houses (produce goods)
- **Orange**: Buyer houses (purchase goods)
- **Gray**: Non-participant houses
"""
    )


def TradingDate(model):
    date_str = model.current_date.strftime("%d/%m/%Y")
    return solara.Text(f"Date: {date_str}")


sim_choice = solara.reactive(None)

@solara.component
def Page():
    if sim_choice.value is None:
        solara.Text("Choose a simulation to run:")
        solara.Button("Traffic Simulation", on_click=lambda: sim_choice.set("A"))
        solara.Button("Trading Simulation", on_click=lambda: sim_choice.set("B"))
    elif sim_choice.value == "A":
        print("Running Traffic Simulation")
        solara.Style(".v-tabs { display: none !important; }")
        SolaraViz(
            Main_model(),
            components=[
                make_geospace_component(Main_draw, zoom=14, height="100vh", width="100vw"),
            ],
            model_params=model_params,
            name="Traffic Simulation",
        )
        VehicleLegend()
    elif sim_choice.value == "B":
        print("Running Trading Simulation")
        solara.Style(".v-tabs { display: none !important; }")
        SolaraViz(
            Trading_model(),
            components=[
                make_geospace_component(Trading_draw, zoom=14, height="100vh", width="100vw"),
                TradingLegend,
                TradingDate,
            ],
            model_params=trading_model_params,
            name="Trading Simulation",
        )
import solara
from mesa.visualization import Slider, SolaraViz # add make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import Main_model, test_agent

model_params = {
    # sliders for model parameters
    "num_of_cars": Slider("Number of Cars", 30, 1, 1000, 1),
}

def Time(model):
    """Display formatted simulation time"""
    try:
        hours = int(model.sim_time.total_seconds() // 3600)
        minutes = int((model.sim_time.total_seconds() % 3600) // 60)
        seconds = int(model.sim_time.total_seconds() % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return solara.Text(f"Simulation time: {time_str}")
    except AttributeError:
        return solara.Text("Time not available")

def Main_draw(agent): 
    """Portrayal Method for canvas"""
    

    geom_type = agent.geometry.geom_type

    # Cache portrayals for static geometries so we don't recompute every frame
    if geom_type in ("Polygon", "LineString"):
        cached = getattr(agent, "_static_portrayal", None)
        if cached is not None:
            return cached

        if geom_type == "Polygon":
            # Compute the expensive area check once and cache the result
            if not hasattr(agent, "_is_large_building"):
                try:
                    agent._is_large_building = agent.geometry.area > 43677.19  # TODO: switch to id-based rule
                except Exception:
                    agent._is_large_building = False

            portrayal = {
                "type": "polygon",
                "color": "red" if agent._is_large_building else "green",
            }
        else:  # LineString (roads)
            portrayal = {
                "type": "linestring",
                "color": "blue",
            }

        # Cache and return for future draws
        agent._static_portrayal = portrayal
        return portrayal

    # Dynamic agents (points)
    if isinstance(agent, test_agent):
        portrayal = {
            "type": "point",
            "color": "red",  # special agent
            "radius": 5,
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

# run the model
model = Main_model()

# create the solara page
page = solara.Column(
    [
        SolaraViz(
            model,
            [
                make_geospace_component(Main_draw, zoom=14, height="100vh", width="100vw"),
            ],
            model_params=model_params,
            name="Neighborhood Project",
        ),Time(model)
    ]
)
page  # noqa
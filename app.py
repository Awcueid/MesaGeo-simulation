import solara
from mesa.visualization import Slider, SolaraViz # add make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import Main_model
from car_agent import test_car

model_params = {
    # sliders for model parameters
    "num_of_cars": Slider("Number of Cars", 30, 0, 1000, 1),
}

def Time(model):
    total_seconds = int(model.sim_time.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    time_str = f"{minutes:02d}:{seconds:02d}"
    return solara.Text(f"Simulation time: {time_str}")


def Main_draw(agent):

    geom_type = agent.geometry.geom_type

    # Cache portrayals for static geometries 
    if geom_type in ("Polygon", "LineString"):
        cached = getattr(agent, "_static_portrayal", None)
        if cached is not None:
            return cached

        if geom_type == "Polygon":
            # Compute the expensive area check once and cache the result
            if not hasattr(agent, "_is_large_building"):
                try:
                    agent.target = agent.geometry.area > 43677.19  # to do : switch to id-based rule
                except Exception:
                    agent.target = False

            portrayal = {
                "type": "polygon",
                "color": "red" if agent.target else "green",
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
    if isinstance(agent, test_car):
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
            components=[
                (make_geospace_component(Main_draw, zoom=14, height="100vh", width="100vw"), 0),
            ],
            model_params=model_params,
            name="Neighborhood Project",
        ),
        # display time after
    ]
)
page  # noqa
#run.py
# Interactive Visualization
# show environment map and agents for 

from C2D2E import *
from model import *
from agent import *


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "Layer": 0,
                 "Color": agent.color.name,
                 "r": 0.5}
    return portrayal

grid = CanvasGrid(agent_portrayal, MAP_WIDTH, MAP_HEIGHT)
chart = ChartModule([{"Label": "Blue Total Attrition",
                      "Color": "Blue"},
                    {"Label": "Red Total Attrition",
                      "Color": "Red"}],
                    data_collector_name='datacollector')
server = ModularServer(C2D2EModel,
                       [grid, chart],
                       "Unit Model",
                       {"N": 7})

server.port = 8521 # The default
server.launch()
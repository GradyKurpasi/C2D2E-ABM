#C2D2E.py
import random
import numpy as np
import pandas as pd
from enum import Enum, auto
import matplotlib.pyplot as plt


from mesa import Model, Agent
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
#Pathfinding functions used from https://github.com/brean/python-pathfinding. 
#Agent & Environment Maps must have positive values for agents to move.  
#In this API, map (i.e. array) values <= 0 equate to obstacles

#GLOBAL 'CONSTANTS' - not wrapped in Enums so that they can be manipulated by Batch Runs
MAX_STEPS = 500

MAP_HEIGHT = 50
MAP_WIDTH = 50

SENSOR_RANGE = 15                         #range at which Red & Blue units can detect each other

RED_TARGETING_EFFECTIVENESS = .5          #Red Side's effectiveness of detecting and targeting Blue Side coms
RED_RANGE = 8                             #Red-For ranged combat range (radius)
RED_RANGE_THREAT = 10                     #Red-For ranged combat threat magnitude
RED_CLOSE_RANGE = 2                       #Red-For close combat range (radius)
RED_CLOSE_THREAT = 30                     #Red-For close combat threat magnitude
RED_CFF_THREAT = 30

MSG_MODIFIER_POSREP = -.2                 #modifiers to RED_TARGETING_EFFECTIVENESS
MSG_MODIFIER_SITREP = .1                  #based IRL on message duration, required RF Freq / Output, etc.
MSG_MODIFIER_CSS = 0                      
MSG_MODIFIER_CFF = 0
MSG_MODIFIER_INTEL_UPDATE = .2

BLUE_COM_RISK_THRESHOLD = .5              #Blue Side's risk acceptance for establishing coms 
BLUE_COM_WINDOW = 10                      #mandated frequency of Blue Side communication with higher (in Steps)
BLUE_COM_EFFECTIVENESS_THRESHOLD = 70     #effectiveness threshold below which Blue Side will establish com regardless of risk
BLUE_RANGE = 8                             #Red-For ranged combat range (radius)
BLUE_RANGE_THREAT = 10                     #Red-For ranged combat threat magnitude
BLUE_CLOSE_RANGE = 2                       #Red-For close combat range (radius)
BLUE_CLOSE_THREAT = 30                     #Red-For close combat threat magnitude
BLUE_CFF_THREAT = 30
BLUE_CSS = 30                             #amount Blue Side effectiveness raised when requesting support

#GLOBAL Enums 
class AgentColor(Enum):
    BLUE = auto()
    RED = auto()
    UNKNOWN = auto()

class AgentType(Enum):
    GROUND = auto()
    AIR = auto()
    HEADQUARTERS = auto()
    
class EffectType(Enum):
    CSS = auto()
    CFF = auto()
    GROUND = auto()
    AIR = auto()
    IDF = auto()
    
class MessageType(Enum):
    POSREP = auto()
    SITREP = auto()
    CSS = auto()
    CFF = auto()
    INTEL_UPDATE = auto()
    
    
class PhysicalObstacle(Enum):
    #not currently in use
    #future use in map definition
    UNPASSABLE = 0
    RIVER = - 1
    MOUNTAIN = -2
    
def RedTargetingEffects(MsgType):
    #calculates chance of Red-For targeting of Blue-For communications
    #returns True if detected, else False

    AdjustedEffectiveness = RED_TARGETING_EFFECTIVENESS
    
    if MsgType == MessageType.POSREP : AdjustedEffectiveness += MSG_MODIFIER_POSREP
    elif MsgType == MessageType.SITREP : AdjustedEffectiveness += MSG_MODIFIER_SITREP
    elif MsgType == MessageType.CSS : AdjustedEffectiveness += MSG_MODIFIER_CSS
    elif MsgType == MessageType.CFF : AdjustedEffectiveness += MSG_MODIFIER_CFF
    elif MsgType == MessageType.INTEL_UPDATE : AdjustedEffectiveness += MSG_MODIFIER_INTEL_UPDATE
    
    return True if random.uniform(0, 1) < AdjustedEffectiveness else False
    
    
def sector_mask(shape,centre,radius,angle_range):
    #re-used from StackExchange
    #https://stackoverflow.com/questions/18352973/mask-a-circular-sector-in-a-numpy-array?noredirect=1
    
    #used to mask areas of a 2D array to reflect threat rings (circles) 
        
    """
    Return a boolean mask for a circular sector. The start/stop angles in  
    `angle_range` should be given in clockwise order.
    """

    x,y = np.ogrid[:shape[0],:shape[1]]
    cx,cy = centre
    tmin,tmax = np.deg2rad(angle_range)

    # ensure stop angle > start angle
    if tmax < tmin:
            tmax += 2*np.pi

    # convert cartesian --> polar coordinates
    r2 = (x-cx)*(x-cx) + (y-cy)*(y-cy)
    theta = np.arctan2(x-cx,y-cy) - tmin

    # wrap angles between 0 and 2*pi
    theta %= (2*np.pi)

    # circular mask
    circmask = r2 <= radius*radius

    # angular mask
    anglemask = theta <= (tmax-tmin)

    return circmask*anglemask

def generate_sector_mask(coord, radius, angle_range=(0,360)):
    #returns a mask of the environment_map array (i.e. [0][0]=True, [0][1]=False, etc.)
    #by default returns a circle of radius RADIUS, centered on COORD
    #can return a sector
    x, y = coord
    mask = sector_mask((MAP_WIDTH, MAP_HEIGHT), (x, y), radius, angle_range) 
    return mask

def generate_threat_ring(coord, radius, threat) :
    #returns a map with a threat ring as weights, intended to be added to existing environment map
    #threat ring weigts = THREAT, circle size = RADIUS, centered on COORD
    map_update = np.zeros((MAP_WIDTH, MAP_HEIGHT))
    mask = generate_sector_mask(coord, radius)
    map_update[mask] = threat
    return map_update

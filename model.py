#model.py
from C2D2E import *
from agent import *
from eventlist import *


    
class C2D2EModel(Model):
    """A model with some number of agents."""
    def __init__(self, N=1):
        
        #init vars / maps
        self.num_agents = N
        self.grid = MultiGrid(MAP_WIDTH, MAP_HEIGHT, False) #MESA grid object
        self.schedule = RandomActivation(self) #MESA scheduling object
        self.environment_map = np.zeros((MAP_WIDTH, MAP_HEIGHT)) #secondary internal map for storing map weights
        self.step_count = 0
        self.model_events = EventList()
        self.waiting_agents = []
    
        #init stats
        self.stat_red_total_attrition = 0
        self.stat_red_units_destroyed = 0
        self.stat_blue_total_attrition = 0
        self.stat_blue_total_css = 0
        self.stat_blue_units_destroyed = 0
        self.stat_blue_final_effectiveness = 0
        self.stat_mission_accomplished = False
        self.stat_total_steps = 0

        #add starting agents
        self.__initialize_agents()
        
        #add data collector
        self.datacollector = DataCollector(
            model_reporters={"Red Total Attrition" : "stat_red_total_attrition",
                             "Red Units Destroyed" : "stat_red_units_destroyed",
                             "Blue Total Attrition" :"stat_blue_total_attrition",
                             "Blue Total CSS" : "stat_blue_total_css",
                             "Blue Units Destroyed" : "stat_blue_units_destroyed",
                             "Blue Final Effectiveness" : "stat_blue_final_effectiveness",
                             "Mission Accomplished" : "stat_mission_accomplished",
                             "Total Steps" : "stat_total_steps"},
            agent_reporters={"POS" : "pos",
                             "Effectiveness": "effectiveness", 
                             "CFF Damage" : "stat_cff",
                             "Attrition Self" : "stat_attrition_self",
                             "Attrition OpFor" : "stat_attrition_opfor",
                             "CSS" : "stat_css",
                             "COM Made" : "stat_com_made",
                             "COM Targeted" : "stat_com_targeted",
                             "Update Sent" : "stat_map_update_sent",
                             "Update Received" : "stat_map_update_received",
                             "Path Length" : "stat_path_length",
                             "Current Effects" : "curr_effects",
                             "CFF Targets" : "stat_cff_targets",
                             "Range Targets" : "stat_range_targets",
                             "Close Targets" : "stat_close_targets"})
         
        #for MESA visualization
        self.running = True
      
        #schedule future events
        #Future AIR agent and events scheduled in self.Initialize_Agents

    def place_red_unit(self, unique_id, coord):
        # agent init function 
        #def __init__(self, unique_id, model,  agent_type, color=AgentColor.BLUE, should_move=False, objective=None, higher=None):
        
        should_move = False
        a = UnitAgent(unique_id, self, AgentType.GROUND, AgentColor.RED, should_move)
        self.schedule.add(a)
        self.grid.place_agent(a, coord)
        return a
    
    def place_blue_unit(self, unique_id, coord, objective, higher = None):
        # agent init function 
        #def __init__(self, unique_id, model,  agent_type, color=AgentColor.BLUE, should_move=False, objective=None, higher=None):
        
        should_move = True
        a = UnitAgent(unique_id, self, AgentType.GROUND, AgentColor.BLUE, should_move, objective, higher)        
        self.schedule.add(a)
        self.grid.place_agent(a, coord)
        if a.higher: a.higher.add_subordinate(a) #if higher != to None establish command relationship
        return a
        
    def __initialize_agents(self):
            
        # agent init function 
        #def __init__(self, unique_id, model,  agent_type, color="blue", should_move=False, objective=None, higher=None):
        
        #debug stuff
        #self.place_blue_unit("v12", (0,0), (19,19))
        #self.place_red_unit("red", (10, 19))
    
        HQ = HeadquartersAgent("2d Marines", self, AgentColor.BLUE, False, (25,45))
        self.schedule.add(HQ)
        self.grid.place_agent(HQ, (0,0))
        
        self.place_blue_unit("V12", (10, 1), (25,45), HQ)
        self.place_blue_unit("V22", (25, 1), (25,45), HQ)
        self.place_blue_unit("V32", (40, 1), (25,45), HQ)
        
        self.place_red_unit("red1", (5, 20))
        self.place_red_unit("red2", (20, 20))
        self.place_red_unit("red3", (25, 20))
        self.place_red_unit("red4", (35, 20))
        self.place_red_unit("red5", (45, 20))
        self.place_red_unit("red6", (15, 30))
        self.place_red_unit("red7", (25, 30))
        self.place_red_unit("red8", (40, 30))
        self.place_red_unit("Goal", (25, 45))
    
        #schedule future agent / events
        #currently only used to demonstrate capability
        
        # agent init function 
        #def __init__(self, unique_id, model,  agent_type, color="blue", should_move=False, objective=None, higher=None):
        #interarrrival = max(int(np.random.exponential(10)), 1) 
        interarrrival = 0
        agt = UnitAgent("Black Knight 1-1", self, AgentType.AIR, AgentColor.BLUE, False, None, HQ)
        self.model_events.add_event(interarrrival, self.schedule.add, (agt, ))
        self.model_events.add_event(interarrrival, self.grid.place_agent, (agt, (10,10)))
        self.model_events.add_event(interarrrival + 1, self.schedule.remove, (agt, ))
        self.model_events.add_event(interarrrival + 1, self.grid.remove_agent, (agt,))

    def __update_map_weights(self):
        
        #generates current map weights
        #map weights = (potential) damage taken by blue units when moving through map
        
        #all map weights are zeroed and re-calculated each step according to current location of units
        self.environment_map = np.ones((MAP_WIDTH, MAP_HEIGHT)) #secondary internal map for storing map weights

        #generate (potential) threat to blue units based on location of red unitws
        for agent in self.schedule.agents:

            #for all red agents, create threat rings centered on red units
            #reflect threat rings as map weights
            if agent.color == AgentColor.RED:
                x, y = agent.pos

                #close combat threat ring
                self.environment_map += generate_threat_ring((x, y), RED_CLOSE_RANGE, RED_CLOSE_THREAT)

                #ranged threat ring
                self.environment_map += generate_threat_ring((x, y), RED_RANGE, RED_RANGE_THREAT)
           
    def stop_sim(self, success=False):
        self.running = False
        self.stat_mission_accomplished = success
        self.stat_total_steps = self.step_count
        for agent in self.schedule.agents:
            if agent.color == AgentColor.BLUE : self.stat_blue_final_effectiveness += agent.effectiveness        
                
    def step(self):
        self.__update_map_weights()  
        self.model_events.exec_events(self.step_count)
        self.schedule.step()
        self.datacollector.collect(self)
        self.step_count += 1
        if self.step_count > MAX_STEPS : self.stop_sim(False)

    def run_model(self, n):
        for i in range(n):
            self.step()    

                
    
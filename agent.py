#agent.py
from C2D2E import *
from eventlist import *

def damage_mod():
    return np.random.beta(5, 1.5)

class UnitAgent(Agent):
    """ A Military unit agent """
    def __init__(self, unique_id, model,  agent_type=AgentType.GROUND, color=AgentColor.BLUE, should_move=False, objective=None, higher=None):
        super().__init__(unique_id, model)
        
        self.agent_type = agent_type
        self.color = color
        self.should_move = should_move
        self.objective = [objective] #LIFO list of objectives, next = objective[-1], final = objective[0]
        self.higher = higher            
        self.pos = (-1,-1)
        self.last_com=0              #last turn had com w higher
        self.effectiveness = 100.0   #hybrid of statistic of unit health/supply/combat effectiveness
        self.agent_map = np.ones((MAP_WIDTH, MAP_HEIGHT))  #what each agent knows about the world
                                                #Blue-For agents do not explictly know positions of Red-For agents
                                                #Red-For agents do not currently move and can be identified by map weights
        
        #stats for data collector, zeroed at beginning of every step
        self.stat_cff = 0                 #Blue-For call for fire effects
        self.stat_attrition_self = 0      #Blue-For 'damage' taken
        self.stat_attrition_opfor= 0      #Blue-For 'damage' dealt
        self.stat_css = 0                 #Blue-For 'health' restored
        self.stat_com_made = False        #Blue-For established communications with higher
        self.stat_com_targeted = False    #Blue-For communications detected and targeted by Red-For
        self.stat_map_update_sent = False #Blue-For sent intel update
        self.stat_map_update_received = False #Blue-For received intel update
        self.stat_path_length = 0         #Number of steps required to reach objective
        self.curr_effects = []            #FIFO list of effects each turn, gathered throghout turn and applied by self.effects()
        self.stat_cff_targets = []        
        self.stat_range_targets = []
        self.stat_close_targets = []
        
        
        #NOTE: agent.pos not defined until model.grid.add_agent is called. agent.pos cant be accessed in agent.__init
    
    def zero_stats(self):
        #stats for data collector, zeroed at beginning of every step
        self.stat_cff = 0                 #Blue-For call for fire effects
        self.stat_attrition_self = 0      #Blue-For 'damage' taken
        self.stat_attrition_opfor= 0      #Blue-For 'damage' dealt
        self.stat_css = 0                 #Blue-For 'health' restored
        self.stat_com_made = False        #Blue-For established communications with higher
        self.stat_com_targeted = False    #Blue-For communications detected and targeted by Red-For
        self.stat_map_update_sent = False #Blue-For sent intel update
        self.stat_map_update_received = False #Blue-For received intel update
        self.stat_path_length = 0         #Number of steps required to reach objective
        self.curr_effects = []            #FIFO list of effects each turn, gathered throghout turn and applied by self.effects()
        self.stat_cff_targets = []        
        self.stat_range_targets = []
        self.stat_close_targets = []
        
    def print_stats(self):
        #stats for data collector, zeroed at beginning of every step
        print("")
        print("")
        print(self.model.step_count, self.unique_id, self.pos, self.agent_map[self.pos])
        print("CURR EFFECTS ", self.curr_effects)            #FIFO list of effects each turn, gathered throghout turn and applied by self.effects()
        print("CFF TARGETS ", self.stat_cff_targets)
        print("RANGE TARGETS ", self.stat_range_targets)
        print("CLOSE TARGETS ", self.stat_close_targets)
        print("CFF ", self.stat_cff)                 #Blue-For call for fire effects
        print("ATTR SELF ", self.stat_attrition_self)      #Blue-For 'damage' taken
        print("ATTR OTHER ", self.stat_attrition_opfor)      #Blue-For 'damage' dealt
        print("CSS ", self.stat_css)                 #Blue-For 'health' restored
        print("COM MADE ", self.stat_com_made)        #Blue-For established communications with higher
        print("COM TARGETED ", self.stat_com_targeted)    #Blue-For communications detected and targeted by Red-For
        print("UPDATE SENT ", self.stat_map_update_sent) #Blue-For sent intel update
        print("UPDATE RECEIVED ", self.stat_map_update_received) #Blue-For received intel update
        print("PATH LENGTH ", self.stat_path_length)         #Number of steps required to reach objective
        print("CURR EFFECTIVENESS", self.effectiveness)
        
    def sense(self):
        #replaces a section (radius) of agent map with an update from environement map
        #occurs every step/turn with radius = SENSOR_RANGE 
        mask = generate_sector_mask(self.pos, SENSOR_RANGE)
        self.agent_map[mask] = self.model.environment_map[mask]
        return
    
    def communicate(self):
        #determines whether not to send one or more communication messages
        #each message can be detected and targeted by Red-For 
        #if com detected, Blue-For unit takes effects = current map weight
        
        rnd = random.uniform(0, 1)       #chance to decide to send comms this step
        
        if self.agent_type == AgentType.HEADQUARTERS : return
        
        if self.color == AgentColor.BLUE :
            
            if self.agent_type == AgentType.AIR :
                #single air unit is used primarily to demonstrate functionality of agent/event scheduling
                #only exists for one step/turn, makes sensor sweep, reports map to higher
                mask = self.agent_map > 1     # portion of map that agent has sensed
                self.higher.agent_map[mask] = self.agent_map[mask]
                return

            #POSREP
            if rnd < BLUE_COM_RISK_THRESHOLD or self.model.step_count - self.last_com > BLUE_COM_WINDOW :
                #send Position Report to higher if risk allows or BLUE_COM_WINDOW has passed
                self.higher.subordinates_lastpos[self.unique_id] = self.pos
                if RedTargetingEffects(MessageType.POSREP) : self.stat_com_targeted = True
                self.last_com = self.model.step_count
                self.stat_com_made = True
            
            #SITREP
            if rnd < BLUE_COM_RISK_THRESHOLD:
                #send Situation Report (i.e. push map updates to higher)
                mask = self.agent_map > 1     # portion of map that agent has sensed
                self.higher.agent_map[mask] = self.agent_map[mask]
                if RedTargetingEffects(MessageType.SITREP) : self.stat_com_targeted = True
                self.last_com = self.model.step_count
                self.stat_map_update_sent = True
                self.stat_com_made = True
            
            #CSS
            if rnd < BLUE_COM_RISK_THRESHOLD or self.effectiveness < BLUE_COM_EFFECTIVENESS_THRESHOLD:
                #send Combat Service Support request to higher if risk allows or effectiveness below threshold
                #CSS message is a catch all for MEDEVAC, Resupply, Combat Replacements, etc.
                #will increase effectiveness
                self.curr_effects.append((EffectType.CSS, BLUE_CSS))
                if RedTargetingEffects(MessageType.CSS) : self.stat_com_targeted = True
                self.last_com = self.model.step_count
                self.stat_com_made = True

            #CFF
            if (rnd < BLUE_COM_RISK_THRESHOLD and self.agent_map[self.pos] > 1) or (self.agent_map[self.pos] > RED_RANGE_THREAT) :
                #request Call For Fire if near Red-For and risk allows OR if in close combat with Red-For unit
                #proximity to Red-For unit currenlty implied from map_weights
                #will need to be updated if Red-For updated to maneuver
                self.curr_effects.append((EffectType.CFF, BLUE_CFF_THREAT))
                if RedTargetingEffects(MessageType.CFF) : self.stat_com_targeted = True
                self.last_com = self.model.step_count
                self.stat_com_made = True
            
            #INTEL UPDATE
            if rnd < BLUE_COM_RISK_THRESHOLD :
                #request Intelligence Update (i.e. pull map updates to higher)
                mask = self.higher.agent_map > 1     # portion of map that has been sensed
                self.agent_map[mask] = self.higher.agent_map[mask] 
                if RedTargetingEffects(MessageType.INTEL_UPDATE) : self.stat_com_targeted = True
                self.last_com = self.model.step_count
                self.stat_map_update_received = True
                self.stat_com_made = True
                
                
        if self.color == AgentColor.RED:
            #future modification should allow for Blue-For targeting of RedFor coms
            pass
                
        if self.stat_com_targeted : 
            #add effect if Red-For successfully targets Blue-For communication
            self.curr_effects.append((EffectType.IDF, RED_CFF_THREAT))
                    
    def move(self):
        #this method relies on external pathfinding API 
        #https://github.com/brean/python-pathfinding
        #not optimized for models with large maps or many agents
        
        #uses pathfinder to plot optimal course based on curent state of map 
        #then moves 1 position toward objective
        #will recalculate move next turn
        #In future - optimize to not calculate full path
        
        if not self.objective or not self.should_move: return  #if objective list is empty or unit shouldn't move: return
            #(should raise handled error in future)
        
        if self.pos != self.objective[-1]: #if current location not equal to next objective (i.e. last element of list)
            
            #create pathfinding grid from MESA grid
            #MESA grid and pathfinding grid are oriented differently, requires transposition of array => map.T
            grid = Grid(matrix=self.agent_map.T) 
            x, y = self.pos 
            start = grid.node(x, y)
            x, y = self.objective[-1]
            end = grid.node(x, y)

            finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
            path, runs = finder.find_path(start, end, grid)
            self.stat_path_length = len(path)
            
            if len(path) > 1: #if there is a solution path, then take first move
                x, y = path[1]
                self.model.grid.move_agent(self, (x, y)) #move
                if self.pos == self.objective[-1] : self.objective.pop() # if have arrived at objective, set next objective
  

    def effects(self):
        if self.color == AgentColor.BLUE:
            
            if self.agent_type == AgentType.AIR : return
            
            cff_effect = 0
            
            #com effects
            for effect in self.curr_effects: #curr_effect list is a type, (EffectType, scalar magnitude)
                
                if effect[0] == EffectType.CFF: #Blue-For Call for Fire
                    cff_effect += effect[1]
                elif effect[0] ==  EffectType.CSS: #Blue-For request for Combat Service Support
                    self.effectiveness += effect[1]
                    self.effectiveness = 100 if self.effectiveness > 100 else self.effectiveness #max effectiveness = 100
                    self.stat_css += effect[1]
                else: #everything else is damage
                    damage = damage_mod() * effect[1] #'damage' is stochastic, % of THREAT/EFFECT, skewed toward .8
                    self.effectiveness -= damage
                    self.stat_attrition_self += damage
                    #NOTE: Red-For CFF effects included in effects list as EffectType.IDF
            
            
            #ground combat effects -< CFF, Ranged, Close >- Effects all Stack
            #for simplicity BLUE/RED effect ranges are currently equal
            
            #CFF Effects
            for RedAgent in self.model.grid.get_neighbors(self.pos, True, True, BLUE_RANGE + 1):
                #+1 range accounts for Blue-For CFF request made in agent.Communicate() which occurs before agent.Move()
                if RedAgent.color != AgentColor.RED : continue
                self.stat_cff_targets.append((RedAgent.unique_id, RedAgent.pos))
                    
                #Blue-For only, Red-For CFF effects applied above in Com Effects
                damage = damage_mod() * cff_effect #'damage' is stochastic, % of THREAT/EFFECT, skewed toward .8
                RedAgent.effectiveness -= damage
                self.stat_cff += damage
                self.stat_attrition_opfor += damage
            
            #Ranged Effects
            for RedAgent in self.model.grid.get_neighbors(self.pos, True, True, BLUE_RANGE):
                if RedAgent.color != AgentColor.RED : continue
                self.stat_range_targets.append((RedAgent.unique_id, RedAgent.pos))
                    
                #Red-For effects
                damage = damage_mod() * RED_RANGE_THREAT #'damage' is stochastic, % of THREAT/EFFECT, skewed toward .8
                self.effectiveness -= damage
                self.stat_attrition_self += damage
                
                #Blue-For effects
                damage = damage_mod() * BLUE_RANGE_THREAT #'damage' is stochastic, % of THREAT/EFFECT, skewed toward .8
                RedAgent.effectiveness -= damage
                self.stat_attrition_opfor += damage
            
            #Close Effects
            for RedAgent in self.model.grid.get_neighbors(self.pos, True, True, BLUE_CLOSE_RANGE):
                if RedAgent.color != AgentColor.RED : continue
                self.stat_close_targets.append((RedAgent.unique_id, RedAgent.pos))

                #Red-For effects
                damage = damage_mod() * RED_CLOSE_THREAT #'damage' is stochastic, % of THREAT/EFFECT, skewed toward .8
                self.effectiveness -= damage
                self.stat_attrition_self += damage
                
                #Blue-For effects
                damage = damage_mod() * BLUE_CLOSE_THREAT #'damage' is stochastic, % of THREAT/EFFECT, skewed toward .8
                RedAgent.effectiveness -= damage
                self.stat_attrition_opfor += damage                

                
        if self.effectiveness < 0:        #agent dies at end of turn if effectiveness falls below 0
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            if self.color == AgentColor.BLUE : self.model.stat_blue_units_destroyed += 1
            if self.color == AgentColor.RED : self.model.stat_red_units_destroyed += 1
            if self.unique_id == "Goal" : self.model.stop_sim(True)
                
        #update remaining stats
        self.model.stat_red_total_attrition += self.stat_attrition_opfor
        self.model.stat_blue_total_attrition += self.stat_attrition_self
        self.model.stat_blue_total_css += self.stat_css


    def step(self):
        self.zero_stats()
        self.sense()
        self.communicate()
        self.move()
        self.effects()
        #debug
        #if self.color == AgentColor.BLUE : self.print_stats()
    
    
class HeadquartersAgent(UnitAgent):
    #headquarters units must be instantiated prior to subordiantes
    #so command relationship can be created
    
    def __init__(self, unique_id, model, color=AgentColor.BLUE, should_move=False, objective=None, higher=None):
        super().__init__(unique_id, model,  AgentType.HEADQUARTERS, color, should_move, objective, higher)
        
        self.subordinates = []                    #in future, this will be generic to UnitAgent
        self.subordinates_lastpos = {}
    
    def add_subordinate(self, agent):
        #establishes 'command' relationships between agents and a HQ agent
        #this must be called after 'agent' object has been added to grid
        #otherwise reference to agent.pos will fail
        
        #add agent to subordinates
        self.subordinates.append(agent)
        #ensure reciprocal command relationship
        agent.higher = self
        #add last known position
        self.subordinates_lastpos[agent.unique_id] = agent.pos
    
    def command(self):
        #future: coordinate movement and effects of agents
        pass
    
    
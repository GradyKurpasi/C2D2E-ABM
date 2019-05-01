from C2D2E import * 
from model import *
from agent import *

#vary risk acceptance of friendly com
Experiment1 = None
n = 0
#degree of RED_TARGETING_EFFECTIVENESS = independent variable
for i in range(1, 11, 1):
    #Sim will look at 10 values of Red-For targeting [.1, .2, .3, ... 1]
    RED_TARGETING_EFFECTIVENESS = i * .1

    for j in range(500):
        #at each value of RED_TARGETING, 500 samples / runs will be measured for Blue Com
        BLUE_COM_RISK_THRESHOLD = np.random.uniform()

        c2model = C2D2EModel()
        while c2model.running :
            c2model.step()
        filename = "Ex1RedTgt" + str(RED_TARGETING_EFFECTIVENESS) + "BlueCom" + str(BLUE_COM_RISK_THRESHOLD)

        agent_stats = c2model.datacollector.get_agent_vars_dataframe()
        agent_stats.to_excel(filename + "agents.xlsx")

        model_stats = c2model.datacollector.get_model_vars_dataframe()
        lastrow = model_stats.tail(1)
        lastrow["RedTgt"] = RED_TARGETING_EFFECTIVENESS
        lastrow["BlueCom"] = BLUE_COM_RISK_THRESHOLD
        if n == 0 :
            Experiment1 = pd.DataFrame(lastrow)
        else:
            Experiment1 = Experiment1.append(lastrow)
        print(n, i, j)
        n += 1
        Experiment1.to_excel("Experiment1.xlsx")
print("ALL DONE")
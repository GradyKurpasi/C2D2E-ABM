#EventList.py
def printme(st = "ASDFASDFASDFASDFASD"):
    print(st)
    return st

def addme(x=0, y=0):
    print(x+y)
    return(x+y)

class EventList:
    
    def __init__(self):
        self.events = []
    
    def add_event(self, step, action, params=()):
        self.events.append((step, action, params))
        
        #when adding events with 1 parameter
        #parameter must be added as a tuple with trailing ','
        #    e.g. ('asdf', )
        #otherwise exec_events won't unpack param correctly
        
        #when adding class methods/functions pass parent object to action
        #    e.g. add_event(1, some_object.some_action, (params,))
        
    def show_events(self):
        print(self.events)
    
    def exec_events(self, step):
        for events in self.events:
            if events[0] == step:
                x = events[1]
                y  = events[2]
                x(*y)
                
        
#myevents = EventList()
#myevents.add_event(1, printme, ("ASDF",))
#myevents.add_event(1, addme, (1, 5))
#myevents.add_event(2, myevents.show_events)
#myevents.show_events()
#myevents.exec_events(2)

import random
from mesa import Model, Agent
from mesa.time import RandomActivation

traits = {'normal':10000,
          'disobedients':0,
          'symptom_spreaders':0,
          'social_spreaders':0,
          'base_interactions':10, # agent interactions per day
          'base_contagion':.02, # base infection probability
          'base_cfr':.02,
          'hospital_need':0.1,
          'beds':50,
          'test_sensitivity':.99,
          'test_specificity':0.1}
          
class PopModel(Model):
    def __init__(self, traits):
        self.num_normal = traits['normal']
        self.num_disobedients = traits['disobedients']
        self.num_symptom_spreaders = traits['symptom_spreaders']
        self.num_social_spreaders = traits['social_spreaders']
        self.base_interactions = traits['base_interactions']
        self.base_contagion = traits['base_contagion']
        self.base_cfr = traits['base_cfr']
        self.sensitivity = traits['test_sensitivity']
        self.specificity = traits['test_specificity']
        self.schedule = RandomActivation(self)
        self.time = 0

        for i in range(self.num_normal):
            self.schedule.add(Normal(i, self))
        for i in range(self.num_disobedients):
            self.schedule.add(Disobedient(i, self))
        for i in range(self.num_symptom_spreaders):
            self.schedule.add(SymptomSpreader(i, self))
        for i in range(self.num_social_spreaders):
            self.schedule.add(SocialSpreader(i, self))

        self.schedule.agents[0].infected = True # one sick person
        self.schedule.agents[0].infected_time = 0

    def step(self):
        self.schedule.step()
        self.pop =len(self.schedule.agents)
        self.infected = len([a for a in self.schedule.agents if a.infected])
        self.immune = len([a for a in self.schedule.agents if a.immune])
        self.dead = len([a for a in self.schedule.agents if a.alive == False])
        self.time += 1

class Person(Agent):
    """Base class for a person"""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.infected = False
        self.immune = False
        self.alive = True
        self.hospitalized = False
        self.needs_hospital = False

    def step(self):
        if (self.infected == True and self.alive == True):
            if self.model.time == (self.infected_time + 14):
                if random.random() <= self.model.base_cfr:
                    self.alive = False
                else:
                    self.immune = True
            else:
                interactions = random.choices(
                    population=[x for x in self.model.schedule.agents if x.alive],
                    k=10)
                for i in interactions:
                    if random.random() <= self.model.base_contagion:
                        if i.immune == False:
                            i.infected = True
                            i.infected_time = self.model.time
                            i.infected_by = self

class Normal(Person):
    pass

class Disobedient(Person):
    pass

class SymptomSpreader(Person):
    pass

class SocialSpreader(Person):
    pass

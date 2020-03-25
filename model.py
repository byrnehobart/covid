import random
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

traits = {'normal':4900,
          'disobedients':4900,
          'symptom_spreaders':10,
          'social_spreaders':10,
          'base_interactions':10, # agent interactions per day
          'base_contagion':.02, # base infection probability
          'base_cfr':.02,
          'hospital_need':0.1,
          'beds':50,
          'test_sensitivity':.99,
          'test_specificity':0.1,
          'distancing_threshold':10}

          
class PopModel(Model):
    """This model simulaties the behavior of a population during an epidemic

    A single agent starts out as infected, and the contagion spreads according to
    simple rules. different agent types have different behaviors, viz.

    - Disobedient agents ignore social distancing rules.
    - Symptom spreaders are unusually contagious per interaction.
    - Social spreaders are agents with a higher frequency of interactions.

    Other model features:
    - Agents are contagious from the moment they're infected.
    - At an infection threshold, distancing measures reduce interactions.
    - Some agents need hospitalization starting one week into infection.
    - Agents are more likely to die when they can't get hospitalized
    - After two weeks, agents either die or become immune.

    This shows the typical cadence of infections: compounding at ~R0 for a
    while, until either behavioral changes or immunity slow the spread.
    Eventually, the infection dies out as R declines to < 1."""

    def __init__(self, traits):
        self.num_normal = traits['normal']
        self.num_disobedients = traits['disobedients']
        self.num_symptom_spreaders = traits['symptom_spreaders']
        self.num_social_spreaders = traits['social_spreaders']
        self.base_interactions = traits['base_interactions']
        self.base_contagion = traits['base_contagion']
        self.base_cfr = traits['base_cfr']
        self.hospital_need = traits['hospital_need']
        self.beds = traits['beds']
        self.sensitivity = traits['test_sensitivity']
        self.specificity = traits['test_specificity']
        self.distancing_threshold = traits['distancing_threshold']
        self.hospitalized = 0
        self.infected = 0
        self.distancing = False
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

        self.datacollector = DataCollector (
            model_reporters= {"Susceptible": "susceptible",
                              "Infected": "infected",
                              "Immune": "immune",
                              "Dead": "dead"})

    def step(self):
        self.alive = [a for a in self.schedule.agents if a.alive]
        self.schedule.step()
        self.pop =len(self.schedule.agents)
        self.living = sum([1 for a in self.schedule.agents if a.alive])
        self.susceptible = sum([1 for a in self.schedule.agents if a.alive and not a.infected and not a.immune])
        self.infected = sum([1 for a in self.schedule.agents if a.infected])
        self.immune = sum([1 for a in self.schedule.agents if a.immune])
        self.dead = sum([1 for a in self.schedule.agents if a.alive == False])
        self.hospitalized = sum([1 for a in self.schedule.agents if a.hospitalized])
        self.needs_hospital = sum([1 for a in self.schedule.agents if a.needs_hospital])
        if self.infected >= self.distancing_threshold and self.distancing == False:
            self.distancing = True
        if self.infected < self.distancing_threshold and self.distancing == True:
            self.distancing = False
        self.datacollector.collect(self)
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

    def medical(self):
        """For infected agents, update status"""
        if self.model.time == (self.infected_time +7):
            if random.random() <= self.model.hospital_need:
                self.needs_hospital = True
        if self.needs_hospital:
            if self.model.beds > self.model.hospitalized:
                self.hospitalized = True
                self.model.hospitalized += 1
                # we update the count each time so we can check each agent's status
                # then we reset the count each day.
                # This saves on computation while keeping the number reconciled
        if self.model.time >= (self.infected_time + 14):
            self.survive()
            
    def die(self):
        """Bookkeeping function for handling deaths."""
        self.infected = False
        self.alive = False
        self.hospitalized = False
        self.needs_hospital= False

    def cure(self):
        """Bookkeeping function for handling recovery."""
        self.infected = False
        self.immune = True
        self.hospitalized = False
        self.needs_hospital = False

    def survive(self):
        """Calculates agent's survival given traits.

        We assume patients who need hospitalization have 5x death rate."""
        outcome = random.random()
        if self.needs_hospital and not self.hospitalized:
            if outcome < 5 * self.model.base_cfr:
                self.die()
        elif outcome < self.model.base_cfr:
            self.die()
        else:
            self.cure()

    def infect(self, other):
        """Infect someone else."""
        if other.immune == False and other.infected == False:
            other.infected = True
            other.infected_time = self.model.time
            other.infected_by = self
                
    def socialize(self):
        """For infected agents, infect others"""
        if self.model.distancing:
            interactions = random.choices(
                population = self.model.alive,
                k = self.model.base_interactions // 3)
        else:
            interactions = random.choices(
                population=self.model.alive,
                k = self.model.base_interactions)
        for i in interactions:
            if random.random() <= self.model.base_interactions:
                self.infect(i)

    def step(self):
        if (self.infected == True and self.alive == True):
            self.medical()
            self.socialize()

class Normal(Person):
    """This class is empty for now, but refers to a generic agent whose
    behavior may differ from the base class."""
    pass

class Disobedient(Person):
    """A person who ignores distancing measures"""
    def socialize(self):
        """For infected agents, infect others"""
        interactions = random.choices(
            population=self.model.alive,
            k = self.model.base_interactions)
        for i in interactions:
            if random.random() <= self.model.base_contagion:
                self.infect(i)

class SymptomSpreader(Person):
    """These are people who are much more contagious than average."""
    def socialize(self):
        """For infected agents, infect others"""
        if self.model.distancing:
            interactions = random.choices(
                population = self.model.alive,
                k = self.model.base_interactions // 3)
        else:
            interactions = random.choices(
                population=self.model.alive,
                k = self.model.base_interactions)
        for i in interactions:
            if random.random() <= self.model.base_contagion * 5:
                self.infect(i)


class SocialSpreader(Person):
    """These are people who are much more likely to socialize than average."""
    def socialize(self):
        """For infected agents, infect others"""
        if self.model.distancing:
            interactions = random.choices(
                population = self.model.alive,
                k = self.model.base_interactions)
        else:
            interactions = random.choices(
                population=self.model.alive,
                k = self.model.base_interactions * 3)
        for i in interactions:
            if random.random() <= self.model.base_contagion:
                self.infect(i)

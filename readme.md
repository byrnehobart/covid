# Covid: A Simple Agent-Based Model

This model runs a fairly typical epidemiology simulation, where we start with a single infected individual, who has encounters with other individuals with some probability of infecting them.

Usage:

1. Install [Mesa](https://mesa.readthedocs.io/en/master/).
2. Instantiate a model with e.g. `m = PopModel(traits)`.
3. Run the model, with e.g. `for _ in range(100): m.step()`.
4. The mode records the number of susceptible, infected, immune, and dead people. Export it to a `pandas` DataFrame with `data = m.datacollector.get_model_vars_dataframe()`.

This model starts with the basics: infected people have a certain probability of spreading their infection with each interaction. 7 days after you get sick, you have a chance of needing hospitalization; 14 days after illness, you either die or recover and become immune. For Covid-appropriateness, I modeled a limited number of hospital beds and elevated mortality once they run out.

Where it gets interesting is modeling different kinds of people:

- Disobedient agents ignore social distancing rules.
- Symptom spreaders are unusually contagious per interaction.
- Social spreaders are agents with a higher frequency of interactions.


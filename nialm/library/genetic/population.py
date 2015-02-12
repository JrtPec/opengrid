from individual import Individual
import random
from itertools import izip_longest

class Population(object):
	"""

	"""
	def __init__(self,size,problem):
		self.individuals = []
		for i in range(0,size):
			ind = Individual(problem)
			self.individuals.append(ind)

	def evolve(self,elitism,breeding_percentage):
		'''
		Generates the next generation from an existing population by selectively breeding the most successful
		individuals. Fully retains the elite(s).

		Parameters
		----------
		elitism : int
			the amount of best performing individuals to copy unmutated and unevolved to the next generation
		breeding_percentage = float
			percentage of the population from which parents can be chosen
			ie. 0.1 means the parents come from the top 10% of the population
		'''
		num_parents = int(len(self.individuals)*breeding_percentage)
		self.sort()
		top = self.individuals[:num_parents]

		for individual in self.individuals[elitism:]:
			parentA,parentB = random.sample(top,2)
			individual = breed(parentA,parentB)
			individual.init_data()
			individual.check_genes()
			individual.calculate_score()

	def sort(self):
		"""
			Sort the list of individuals by score
		"""
		#Sort by highest score
		self.individuals = sorted(self.individuals, key=lambda Individual: Individual.score)[::-1]

	def get_score(self,top):
		self.sort()
		res = 0.0
		for ind in self.individuals[:top]:
			res += ind.score
		return res/top

	def get_best(self):
		self.sort()
		return self.individuals[0]

def breed(parentA,parentB):
	"""
		Combines genes of two parents into a new individual

		Parameters
		----------
		parentA : Individual
		parentB : Individual

		Returns
		-------
		Individual
	"""
	for geneA,geneB in izip_longest(parentA.genes,parentB.genes,fillvalue=None):
			geneA = random.choice([geneA,geneB])

	return parentA

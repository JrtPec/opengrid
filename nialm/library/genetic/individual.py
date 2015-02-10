import random
from gene import Gene

class Individual(object):
	"""
		An Individual is one possible solution to the optimilization problem.
		It contains genes, which represent the individual methods that are used to solve the problem.
	"""
	def __init__(self,problem,genes=[]):
		self.tol = problem.tol
		self.mutation_rate = problem.mutation_rate
		self.data = problem.df_diff.copy()
		self.problem = problem

		self.parts = []
		self.genes = []

		for gene in genes:
			if random.random() < self.mutation_rate:
				gene = Gene(methodlist=problem.methodlist)
			else:
				gene.mutate(self.mutation_rate)

			if not self.is_good_gene(gene):
				break

		if len(self.genes) == len(genes):
			while True:
				gene = Gene(methodlist=problem.methodlist)
				if not self.is_good_gene(gene):
					break

		self.score = self.calculate_score() / self.problem.score_ceiling

	def __repr__(self):
		print "Number of genes: ",len(self.genes)
		print "Score: ",self.calculate_score()
		print "Ceiling: ",self.problem.score_ceiling
		print "Solution percentage: ",self.score*100,"%"
		return ""

	def is_good_gene(self,gene):
		"""
			Checks if this gene will help solve the problem
			If it does, save the result and add the gene to the list

			Parameters
			----------
			gene : Gene
			data : Pandas Series
			tol : float
				Tolerance of the matching algorithms

			Returns
			-------
			bool
				True => Good gene, has been added, saved result
				False => Bad gene, no result
		"""
		response = gene.exec_method(data=self.data,tol=self.tol)
		if response is not None:
			self.parts.append(response)
			self.genes.append(gene)
			return True
		else:
			return False

	def calculate_score(self):
		"""
			How good is this individual at solving the problem?
			The higher the better.

			Returns
			_______
			float
		"""
		score = 0.0
		for part in self.parts:
			score += part.get_score()
		return score
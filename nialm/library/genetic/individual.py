import random
from gene import Gene

class Individual(object):
	"""
		An Individual is one possible solution to the optimilization problem.
		It contains genes, which represent the individual methods that are used to solve the problem.
	"""
	def __init__(self,problem,genes=[]):
		self.data = problem.df_diff.copy()
		self.problem = problem

		self.parts = []
		self.genes = genes
		self.score = 0

		self.check_genes()
		self.calculate_score()
		

	def __repr__(self):
		print "Number of genes: ",len(self.genes)
		print "Ceiling: ",self.problem.score_ceiling
		print "Solution percentage: ",self.score*100,"%"
		return ""

	def check_genes(self):
		for gene in self.genes:
			if random.random() < self.problem.mutation_rate:
				gene = Gene(methodlist=self.problem.methodlist)
			else:
				gene.mutate(self.problem.mutation_rate)

			if not self.is_good_gene(gene):
				return True

		#If all genes are checked and good, try adding new genes
		while True:
			gene = Gene(methodlist=self.problem.methodlist)
			if self.is_good_gene(gene):
				self.genes.append(gene)
			else:
				return True

		return True

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
		if gene is None:
			return False
		else:
			response = gene.exec_method(data=self.data,tol=self.problem.tol)
			if response is not None and response.is_valid(orig_signal=self.problem.df_orig):
				self.parts.append(response)
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
		self.score = score / self.problem.score_ceiling
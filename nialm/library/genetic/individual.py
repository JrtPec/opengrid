import random
from gene import Gene

class Individual(object):
	"""
		An Individual is one possible solution to the optimilization problem.
		It contains genes, which represent the individual methods that are used to solve the problem.
	"""
	def __init__(self,problem,genes=[]):
		self.problem = problem

		self.parts = []
		self.genes = genes

		self.init_data()
		self.check_genes()
		self.calculate_score()
		

	def __repr__(self):
		print "Number of genes: ",len(self.genes)
		print "Solution percentage: ",self.score*100,"%"
		return ""

	def init_data(self):
		self.norm_data = self.problem.df_norm.copy()
		self.der_data = self.problem.df_diff.copy()
		self.parts = []

	def check_genes(self):
		for i,gene in enumerate(self.genes):
			if random.random() < self.problem.mutation_rate:
				gene = Gene(methodlist=self.problem.methodlist)
			else:
				gene.mutate(self.problem.mutation_rate)

			if not self.is_good_gene(gene):
				self.genes = self.genes[:i]
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
			response = gene.exec_method(der_data=self.der_data,norm_data=self.norm_data,tol=self.problem.tol)
			if response is not None:
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
			score += part.score
		self.score = score / self.problem.score_ceiling
from population import Population
import matplotlib.pyplot as plt

from IPython import display

def extract_events(problem,generations=100,pop_size=100,elitism=1,breeding_percentage=0.1,plot_evolution=False,plot_end=False):
	"""
		Performs an analysis of switch on-off events using a genetic algorithm, saves the analysis results in seperate files

		Parameters
		----------
		generations : int (default=100)
			number of generations over wich to run the genetic algorithm
		pop_size : int (default=100)
			number of different individuals in the population
		elitism : int (default=1)
			the amount of best performing individuals to copy unmutated and unevolved to the next generation
		breeding_percentage = float (default=0.1)
			percentage of the population from which parents can be chosen
			ie. 0.1 means the parents come from the top 10% of the population

		Returns
		_______
		?
	"""
	#build the starting population
	pop = Population(size=pop_size,problem=problem)

	if plot_evolution == True or plot_end == True:
		best_score = [pop.get_score(1)]
		top_score = [pop.get_score(int(pop_size*breeding_percentage))]
		mean_score = [pop.get_score(pop_size)]



	#loop for the amount of generations
	for i in range(0,generations):
		if pop.get_best().score >= problem.score_ceiling:
			break
		else:
			pop.evolve(elitism=elitism,breeding_percentage=breeding_percentage)

		if plot_evolution == True or plot_end == True:
			best_score.append(pop.get_score(1))
			top_score.append(pop.get_score(int(pop_size*breeding_percentage)))
			mean_score.append(pop.get_score(pop_size))
		if plot_evolution==True:
			display.clear_output(wait=True)
			plot_genetic(best_score,top_score,mean_score)
	
	if plot_end==True:
		plot_genetic(best_score,top_score,mean_score)	

	#find the best individual
	return pop.get_best()

def plot_genetic(best_score,top_score,mean_score):
	plt.plot(best_score, label="best")
	plt.plot(top_score, label="top")
	plt.plot(mean_score, label="mean")
	plt.ylabel('score')
	plt.xlabel('generations')
	plt.legend()
	plt.show()
	return True

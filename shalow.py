import random
import time
from multiprocessing import Process, Queue

# range/xrange compatibility fix
import sys
RANGE=xrange
if sys.version_info > (2,9): RANGE=range


############################## 
# Example functions: Ones problem
#
def generate_member_basic(bounds):
    return [random.randint(a,b) for a, b in bounds]

#generate num random dna strings
def generate_rand_set_basic(num, bounds):
    return [generate_member_basic(bounds) for i in RANGE(num)]

def ones_fitness(member, ctx):
    return sum(member)

def breedBasic(guy1, guy2):
    return [guy1[i] if i % 2 == 0 else guy2[i] for i in RANGE(len(guy1))]

def mutateBasic(guy, bounds):
    loc = random.randint(0, len(guy)-1)
    guy[loc] = random.randint(bounds[loc][0], bounds[loc][1])
    return guy
################################ End example funcs

################################
# Creater class
#

class Creator(object):

    def __init__(self, breed_func, individual_generator, mutation_func, mutation_rate, bounds, elitism_rate=10, breedsize=10):
        self.elitism = elitism_rate
        self.breed = breed_func
        self.mut_rate = mutation_rate
        self.mutate = mutation_func
        self.mutate_rate = mutation_rate
        self.individual_generator = individual_generator
        self.bounds = bounds
        self.breeder_popsize = breedsize

    # maybe overload this function
    def createPopulation(self, size):
        return [ self.individual_generator(self.bounds) for i in RANGE(size) ]

    def isElitist():
        return not self.elitism == 0

    # overload this function
    def breedPopulation(self, previous_generation, size):
        new_generation = []
        breedpop = int(size * self.breeder_popsize) if self.breeder_popsize < 1.0 else self.breeder_popsize
        if not self.elitism == 0:
            keepnum = int(len(previous_generation)*self.elitism) if self.elitism < 1.0 else self.elitism
            new_generation.extend(previous_generation[:keepnum])

        for i in RANGE(breedpop-1):
            for j in RANGE(i+1, breedpop):
                newguy = self.breed(previous_generation[i], previous_generation[j])
                if random.random() < self.mut_rate: newguy = self.mutate(newguy, self.bounds)
                new_generation.append(newguy)

        genlen = len(new_generation)
        if genlen > size:
            return new_generation[:size]
        elif genlen < size:
            for i in RANGE(genlen, size): new_generation.append(self.individual_generator(self.bounds))

        return new_generation

    # don't overload this
    def getGeneration(self, previous_generation, gen_size):
        if previous_generation:
            return self.breedPopulation(previous_generation, gen_size)
        return self.createPopulation(gen_size)


class breedTournamentBasic(Creator):

    def __init__(self, breed_func, individual_generator, mutation_func, mutation_rate, bounds):
        super.__init__(breed_func, individual_generator, mutation_func, mutation_rate, bounds, 10, 10)


    
###############################
# Genetic Algo
#

def pass_init():
    return None

def runPool(my_group, q, fitness, init=pass_init):
    ctx = init()
    for guy in my_group:
        fit = fitness(guy, ctx)
        q.put( (guy, fit) )
    


def genetic(generations, gen_size, creator, fitness, num_processes=4):
    prev_generation = []
    
    for i in RANGE(generations):
        # generate the new population
        gen_list = creator.getGeneration(prev_generation, gen_size)
        result_list = []
        
        results_q = Queue()
        p = []
        # establish the load (number of individuals) each process will take on
        equal_share = len(gen_list)/(num_processes)
        remainder = len(gen_list) - (equal_share * num_processes)
        load_shares = [equal_share+1,] * remainder
        load_shares.extend([equal_share,] * (equal_share-remainder))

        # create the workers and give them each a bundle of tasks
        n_begin = 0
        for j in RANGE(num_processes):
            n_end = n_begin + load_shares[j]
            niche = gen_list[n_begin:n_end]
            worker = Process(target=runPool, args=(niche, results_q, fitness))
            p.append(worker)
            worker.start()
            n_begin = n_end

        # gather results as they are generated
        # this prevents the Queue from ever
        # becoming full (hopefully)
        while len(result_list) < gen_size:
            if not results_q.empty():
                result_list.append(results_q.get())
                #print str(len(result_list)) + '...'
            #time.sleep(1)

        # do an in-place sort of the results
        gen_score_sorted = sorted(result_list, key=lambda tup: tup[1], reverse=True)
        prev_generation = [result[0] for result in gen_score_sorted]
        #print prev_generation[0], gen_score_sorted[0][1]

    return prev_generation[0], gen_score_sorted[0][1]



if __name__ == "__main__":
    bounds = [(0,1),]*1000
    creator = Creator(breedBasic, generate_member_basic, mutateBasic, 0.05, bounds, 100, 100)
    winner = genetic(10, 10000, creator, ones_fitness)
    print winner


    

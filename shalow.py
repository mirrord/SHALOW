import random
import time
from multiprocessing import Process, Queue

# range/xrange compatibility fix
import sys
RANGE=xrange
if sys.version_info > (2,9): RANGE=range


############################## 

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

def pass_init():
    return None

class breedTournamentBasic:
    elitist = True

    def __init__(self, breed_func, mutation_func, mut_bounds, size=.10, mutation_rate=.05):
        self.size = size
        self.breed = breed_func
        self.mut_rate = mutation_rate
        self.mutate = mutation_func
        self.bounds = mut_bounds

    def breed_generation(self, prev_gen_sorted):
        top_some = prev_gen_sorted[:int(self.size*len(prev_gen_sorted))]
        full_gen = []
        for i in RANGE(len(top_some)):
            for j in RANGE(i+1, len(top_some)):
                newguy = self.breed(top_some[i], top_some[j])
                if random.random() < self.mut_rate: newguy = self.mutate(newguy, self.bounds)
                #print "bred parents:"
                #print str(top_some[i])
                #print str(top_some[j])
                #print "to child:"
                #print str(newguy)
                #time.sleep(1)
                full_gen.append(newguy)

        return full_gen
    
############################### End example funcs

def getGeneration(prev_gen_sorted, breed_scheme, gen_size, pop_generator, bounds):
    if len(prev_gen_sorted) == 0:
        return pop_generator(gen_size, bounds)

    next_gen = []
    if breed_scheme.elitist:
        next_gen.extend(prev_gen_sorted[:int(breed_scheme.size*gen_size)])
    
    children = breed_scheme.breed_generation(prev_gen_sorted)
    num_kids = len(children)
    num_allowed_kids = gen_size-len(next_gen)
    if num_kids > num_allowed_kids:
        next_gen.extend(children[:num_allowed_kids])
    else:
        next_gen.extend(children)

    next_gen.extend(pop_generator(gen_size - len(next_gen), bounds))
        
    return next_gen


def runPool(my_group, q, fitness, init=pass_init):
    ctx = init()
    for guy in my_group:
        fit = fitness(guy, ctx)
        q.put( (guy, fit) )
    


def genetic(generations, breed_scheme, gen_size, population_generator, fitness, num_processes=4):
    prev_generation = []
    
    for i in RANGE(generations):
        # generate the new population
        print "starting generation", i, "..."
        gen_list = getGeneration(prev_generation, breed_scheme, gen_size, population_generator, breed_scheme.bounds)
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
        print "generation", i, "complete..."
        print prev_generation[0], gen_score_sorted[0][1]

    return prev_generation[0], gen_score_sorted[0][1]





if __name__ == "__main__":
    bounds = [(0,1),]*100
    breeder = breedTournamentBasic(breedBasic, mutateBasic, bounds, mutation_rate=0.25)
    breeder.elitist = False
    winner = genetic(10, breeder, 10000, generate_rand_set_basic, ones_fitness)
    print winner


    

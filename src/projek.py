import random as rand
import pandas as pd

units = [
    {'kapasitas': 20, 'interval': 2},
    {'kapasitas': 15, 'interval': 2},
    {'kapasitas': 35, 'interval': 1},
    {'kapasitas': 40, 'interval': 1},
    {'kapasitas': 15, 'interval': 1},
    {'kapasitas': 15, 'interval': 2},
    {'kapasitas': 10, 'interval': 1},
]
jumlah_periode = 6

total_mw = sum([unit['kapasitas'] for unit in units]) # 150
rekomendasi_mwatt = 115 # Syarat fitness cost prioritas
minimal_mwatt = 100 # Syarat fitness cost sekondari

initial_weight_fc_prioritas = 3 # Fitness cost prioritas
initial_weight_fc_sekondari = 1 # Fitness cost sekondari
weight_fc_buruk = -10 # Fitness cost buruk

# Main2 di parameter sini ya guys
populasi_awal = 50
max_population = 50
generasi = 25

def make_random_chromosome():
    unit_ids = [i for i in range(len(units))]
    chromosome = [i for i in range(len(units))]
    while len(unit_ids) > 0: # Assign unit 1-7 ke periode 1-6 yang di random
        unit_id = unit_ids.pop(0)
        if units[unit_id]['interval'] == 1:
            periode = rand.randint(0, jumlah_periode - 1)
            chromosome[unit_id] = periode+1
        elif units[unit_id]['interval'] == 2:
            periode = rand.randint(0, jumlah_periode - 2)
            chromosome[unit_id]=periode+1
    return chromosome

def calc_fitness(chromosome):
    fc = 0
    chromosome_inverted = [[] for _ in range(jumlah_periode)] # Invert chromosome to make it easier to iterate
    for unit_id in range(len(chromosome)):
        if units[unit_id]['interval'] == 1:
            chromosome_inverted[chromosome[unit_id]-1].append(unit_id+1)
        elif units[unit_id]['interval'] == 2:
            chromosome_inverted[chromosome[unit_id]-1].append(unit_id+1)
            chromosome_inverted[int(chromosome[unit_id])].append(unit_id+1)
    for units_dalam_periode in chromosome_inverted:
        sisa_mw = total_mw
        for unit_id in units_dalam_periode:
            sisa_mw -= units[unit_id-1]['kapasitas']
        if sisa_mw >= rekomendasi_mwatt: # For first priority fitness
            mw_kelebihan = sisa_mw - rekomendasi_mwatt
            max_to_priority_delta = total_mw - rekomendasi_mwatt
            gene_fc = initial_weight_fc_prioritas
            gene_fc -= (mw_kelebihan) * initial_weight_fc_prioritas / max_to_priority_delta
            fc += gene_fc
        elif sisa_mw >= minimal_mwatt: # For secondary priority fitness
            mw_kelebihan = sisa_mw - minimal_mwatt
            primary_to_secondary_delta = rekomendasi_mwatt - minimal_mwatt
            gene_fc = initial_weight_fc_sekondari
            gene_fc += mw_kelebihan * (initial_weight_fc_prioritas - initial_weight_fc_sekondari) / primary_to_secondary_delta
            fc += gene_fc
        else: # For bad fitness
            gene_fc = weight_fc_buruk
            fc += gene_fc
    return fc


def selection_roulette_wheel(chromosomes, amount_to_select):
    """
    Seleksi/filter dari seluruh populasi chromosomes dengan cara Roulette Wheel Selection
    :param chromosomes: List chromosomes
    :param amount_to_select: Jumlah chromosomes yang akan di seleksi
    :return: Chromosomes baru dengan jumlah amount_to_select yang sudah di seleksi
    """
    chromosomes_fitness = [[chromosome, calc_fitness(chromosome)] for chromosome in chromosomes]
    chromosomes_fitness.sort(key=lambda x: x[1])
    # print(chromosomes_fitness)
    negative_amount = 0
    if chromosomes_fitness[0][1] <= 0:
        negative_amount = abs(chromosomes_fitness[0][1]) + 1
    fitness_costs = [fc + negative_amount for chromosome, fc in chromosomes_fitness]
    total_fitness = sum(fitness_costs)
    # print(total_fitness)

    selected = []
    for i in range(int(amount_to_select)):
        random_fitness = rand.randint(0, total_fitness)
        # print("Random from", 0, total_fitness, "got", random_fitness)
        cumulative_fitness = 0

        for i in range(len(fitness_costs)):
            cumulative_fitness += fitness_costs[i]
            if cumulative_fitness >= random_fitness:
                selected.append(chromosomes_fitness[i][0])
                # print("SELECTED", chromosomes_fitness[i][0], "FC=", chromosomes_fitness[i][1])
                break
        # print(cumulative_fitness)
    return selected


def select_chromosomes_to_pair(chromosomes, best_percentage):
    """
    Pilih dari chromosomes untuk di pairing secara random berdasarkan best_percentage nya
    :param chromosomes: List chromosomes
    :param best_percentage: Persentase antara 0.0 - 1.0
    :return: Dua chromosome yang telah di pilih
    """
    chromosomes_fitness = [[chromosome, calc_fitness(chromosome)] for chromosome in chromosomes]
    chromosomes_fitness.sort(key=lambda x: x[1], reverse=True)

    best_percentage = int(len(chromosomes) * best_percentage)
    chromosome1 = rand.choice(chromosomes_fitness[:best_percentage])
    chromosome2 = rand.choice(chromosomes_fitness[:best_percentage])
    return chromosome1[0], chromosome2[0]

def crossover(chromosome1, chromosome2):  # Single point crossover
    anak = []
    crossover_point = rand.randint(1, jumlah_periode - 1)
    for i in range(crossover_point):
        anak.append(chromosome1[i])
    for i in range(crossover_point, 7):
        anak.append(chromosome2[i])
    return anak

def mutasi(chromosome):
    while True:
        unit_random1, unit_random2 = rand.sample(range(0, 7), 2)
        if (chromosome[unit_random1] == 6 and units[unit_random2]['interval'] == 2) or \
            (chromosome[unit_random2] == 6 and units[unit_random1]['interval'] == 2):
            continue
        else:
            break
    # print("Switching", unit_random1+1, "with", unit_random2+1)
    temp = chromosome[unit_random1]
    chromosome[unit_random1] = chromosome[unit_random2]
    chromosome[unit_random2] = temp
    return chromosome

def generate_population_and_replace_old(chromosomes):
    chromosomes_fitness = [[chromosome, calc_fitness(chromosome)] for chromosome in chromosomes]
    chromosomes_fitness.sort(key=lambda x: x[1], reverse=True)

    if chromosomes_fitness[0][1] >= 16:
        print("Telah ketemu chromosome terbaik yaitu", chromosomes_fitness[0][0], "dengan fitness cost", chromosomes_fitness[0][1])
        return chromosomes

    print('----- NEW GENERATION -----')
    # List chromosomes baru diambil dari 50% list chromosomes lama pakai roulette wheel selection
    new_chromosomes = selection_roulette_wheel(chromosomes, len(chromosomes)/2)
    print(new_chromosomes)

    # Sisanya di pilih 2 parent, di crossover, di mutasi, repeat hingga populasi baru mencapai max_population
    i=1
    while len(new_chromosomes) < max_population:
        print("ITERASI KE=" + str(i))
        chromosome1, chromosome2 = select_chromosomes_to_pair(new_chromosomes, 0.2)
        anak = crossover(chromosome1, chromosome2)
        mutant = mutasi(anak)
        print("MUTANT=", mutant, 'FC=', calc_fitness(mutant))  # Print in console
        new_chromosomes.append(mutant)
        chromosomes_fc = [[chromosome, calc_fitness(chromosome)] for chromosome in new_chromosomes]
        chromosomes_fc.sort(key=lambda x: x[1], reverse=True)
        print("BEST=", chromosomes_fc[0][0], "FC=", chromosomes_fc[0][1])
        i += 1
    return new_chromosomes

# Contoh sederhana 2 parent only
chrom1 = [1, 1, 3, 4, 5, 5, 6]
# print(calc_fitness(chrom1))
# for i in range(25):
#     print("MUTASI KE-" + str(i))
#     mutated = mutasi(chrom1)
#     print("HASIL MUTASI=", mutated)

for i in range(15):
    chromosome = make_random_chromosome()
    print("i=", i+1, "CHROMOSOME=", chromosome, 'FC=', calc_fitness(chromosome))

# chromosomes = [make_random_chromosome() for _ in range(populasi_awal)]
# for i in range(generasi): # Coba run x generasi
#     print("Generasi ke-" + str(i+1), end=" ")
#     chromosomes = generate_population_and_replace_old(chromosomes)
import random as rand
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

total_mw = sum([unit['kapasitas'] for unit in units])  # 150
rekomendasi_mwatt = 115  # Syarat fitness cost prioritas
minimal_mwatt = 100  # Syarat fitness cost sekondari

initial_weight_fc_prioritas = 3  # Fitness cost prioritas
initial_weight_fc_sekondari = 1  # Fitness cost sekondari
weight_fc_buruk = -10  # Fitness cost buruk

# Main2 di parameter sini ya guys
populasi_awal = 50
max_population = 50
generasi = 100


def make_random_chromosome():
    unit_ids = [i for i in range(len(units))]
    chromosome = [i for i in range(len(units))]
    while len(unit_ids) > 0:  # Assign unit 1-7 ke periode 1-6 yang di random
        unit_id = unit_ids.pop(0)
        if units[unit_id]['interval'] == 1:
            periode = rand.randint(0, jumlah_periode - 1)
            chromosome[unit_id] = periode + 1
        elif units[unit_id]['interval'] == 2:
            periode = rand.randint(0, jumlah_periode - 2)
            chromosome[unit_id] = periode + 1
    return chromosome


def calc_fitness(chromosome):
    fc = 0
    chromosome_inverted = [[] for _ in range(jumlah_periode)]  # Invert chromosome to make it easier to iterate
    for unit_id in range(len(chromosome)):
        if units[unit_id]['interval'] == 1:
            chromosome_inverted[chromosome[unit_id] - 1].append(unit_id + 1)
        elif units[unit_id]['interval'] == 2:
            chromosome_inverted[chromosome[unit_id] - 1].append(unit_id + 1)
            chromosome_inverted[int(chromosome[unit_id])].append(unit_id + 1)
    for units_dalam_periode in chromosome_inverted:
        sisa_mw = total_mw
        for unit_id in units_dalam_periode:
            sisa_mw -= units[unit_id - 1]['kapasitas']
        if sisa_mw >= rekomendasi_mwatt:  # For first priority fitness
            mw_kelebihan = sisa_mw - rekomendasi_mwatt
            max_to_priority_delta = total_mw - rekomendasi_mwatt
            gene_fc = initial_weight_fc_prioritas
            gene_fc -= (mw_kelebihan) * initial_weight_fc_prioritas / max_to_priority_delta
            fc += gene_fc
        elif sisa_mw >= minimal_mwatt:  # For secondary priority fitness
            mw_kelebihan = sisa_mw - minimal_mwatt
            primary_to_secondary_delta = rekomendasi_mwatt - minimal_mwatt
            gene_fc = initial_weight_fc_sekondari
            gene_fc += mw_kelebihan * (
                        initial_weight_fc_prioritas - initial_weight_fc_sekondari) / primary_to_secondary_delta
            fc += gene_fc
        else:  # For bad fitness
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

    new_chromosomes = []
    for i in range(int(amount_to_select)):
        random_fitness = rand.uniform(0, total_fitness)
        # print("Random from", 0, total_fitness, "got", random_fitness)
        cumulative_fitness = 0

        for i in range(len(fitness_costs)):
            cumulative_fitness += fitness_costs[i]
            if cumulative_fitness >= random_fitness:
                new_chromosomes.append(chromosomes_fitness[i][0])
                # print("SELECTED", chromosomes_fitness[i][0], "FC=", chromosomes_fitness[i][1])
                break
        # print(cumulative_fitness)
    return new_chromosomes


def selection_tournament(chromosomes, amount_to_select, tournament_size=3):
    """
    Seleksi/filter dari seluruh populasi chromosomes dengan cara Roulette Wheel Selection
    :param chromosomes: List chromosomes
    :param amount_to_select: Jumlah chromosomes yang akan di seleksi
    :param tournament_size: Jumlah chromosomes yang akan di tandingkan dengan satu sama lainnya
    :return: Chromosomes baru dengan jumlah amount_to_select yang sudah di seleksi
    """
    new_chromosomes = []
    while len(new_chromosomes) < amount_to_select:
        random_chromosomes = rand.sample(chromosomes, tournament_size)
        random_chromosomes_fitness = [[chromosome, calc_fitness(chromosome)] for chromosome in random_chromosomes]
        best_chromosome = max(random_chromosomes_fitness, key=lambda x: x[1])
        new_chromosomes.append(best_chromosome[0])
        chromosomes.pop(chromosomes.index(best_chromosome[0]))
    return new_chromosomes


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


def crossover_single_point(chromosome1, chromosome2): # Single point crossover
    anak = []
    crossover_point = rand.randint(1, jumlah_periode - 1)
    for i in range(crossover_point):
        anak.append(chromosome1[i])
    for i in range(crossover_point, 7):
        anak.append(chromosome2[i])
    return anak


def crossover_double_point(chromosome1, chromosome2): # Double point crossover by Rayner
    anak = []
    crossover_points = sorted(rand.sample(range(1, 7), 2))

    for i in range(crossover_points[0]):
        anak.append(chromosome1[i])
    for i in range(crossover_points[0], crossover_points[1]):
        anak.append(chromosome2[i])
    for i in range(crossover_points[1], 7):
        anak.append(chromosome1[i])
    return anak


def mutation_swap(chromosome):
    """
    Memilih dua gene dalam kromosom secara acak dan menukarkan posisi keduanya.
    :param chromosome: Chromosome
    :return: Mutated Chromosome
    """
    while True:
        unit_random1, unit_random2 = rand.sample(range(0, 7), 2)
        if (chromosome[unit_random1] == 6 and units[unit_random2]['interval'] == 2) or \
                (chromosome[unit_random2] == 6 and units[unit_random1]['interval'] == 2):
            continue
        else:
            break
    temp = chromosome[unit_random1]
    chromosome[unit_random1] = chromosome[unit_random2]
    chromosome[unit_random2] = temp
    return chromosome


def mutation_add_subtract_single(chromosome):
    """
    Memilih satu gene dalam kromosom secara acak dan melakukan adding atau substracting.
    :param chromosome: Chromosome
    :return: Mutated Chromosome
    """
    random = rand.randint(0, 6)
    dobel_interval = False
    if units[random]['interval'] == 2:
        dobel_interval = True

    nilai_baru = chromosome[random]
    plus_minus = rand.randint(0, 1)
    if plus_minus == 0:
        nilai_baru -= 1
    else:
        nilai_baru += 1
    if dobel_interval and nilai_baru > 5:
        nilai_baru -= 5
    elif dobel_interval and nilai_baru < 1:
        nilai_baru += 5
    elif not dobel_interval and nilai_baru > 6:
        nilai_baru -= 6
    elif not dobel_interval and nilai_baru < 1:
        nilai_baru += 6
    chromosome[random] = nilai_baru
    return chromosome


def mutation_add_subtract_double(chromosome):
    """
    Mengubah dua gene random dengan metode adding pada gene pertama dan subtract pada gene kedua pada sebuah chromosome.
    :param chromosome: Chromosome
    :return: Mutated Chromosome
    """
    random = rand.sample(range(0, 6), 2)

    for i in range(2):
        dobel_interval = False
        if units[random[i]]['interval'] == 2:
            dobel_interval = True

        nilai_baru = chromosome[random[i]]
        if i == 0:
            nilai_baru += 1
        else:
            nilai_baru -= 1
        if dobel_interval and nilai_baru > 5:
            nilai_baru -= 5
        elif dobel_interval and nilai_baru < 1:
            nilai_baru += 5
        elif not dobel_interval and nilai_baru > 6:
            nilai_baru -= 6
        elif not dobel_interval and nilai_baru < 1:
            nilai_baru += 6
        chromosome[random[i]] = nilai_baru
    return chromosome


def mutation_random_gene(chromosome):
    """
        Mengubah satu gene secara acak dengan dan di random valuenya (Mengikuti contraint sebuah gene).
        :param chromosome: Chromosome
        :return: Mutated Chromosome
    """
    random = rand.randint(0, 6)
    if units[random]['interval'] == 2:
        random_value = rand.randint(1, 5)
        chromosome[random] = random_value
    elif units[random]['interval'] == 1:
        random_value = rand.randint(1, 6)
        chromosome[random] = random_value
    return chromosome


def generate_population_and_replace_old(chromosomes):
    chromosomes_fitness = [[chromosome, calc_fitness(chromosome)] for chromosome in chromosomes]
    chromosomes_fitness.sort(key=lambda x: x[1], reverse=True)

    if chromosomes_fitness[0][1] >= 16:
        print("Telah ketemu chromosome terbaik yaitu", chromosomes_fitness[0][0], "dengan fitness cost",
              chromosomes_fitness[0][1])
        return chromosomes, True

    # List chromosomes baru diambil dari 50% list chromosomes lama pakai tournament selection
    # new_chromosomes = selection_roulette_wheel(chromosomes, len(chromosomes) / 2) # Gunakan ini untuk roulette wheel selection
    new_chromosomes = selection_tournament(chromosomes, len(chromosomes) / 2) # Gunakan ini untuk tournament selection
    print("TOURNAMENT SELECTIONS =", new_chromosomes)

    # Sisanya di pilih 2 parent, di crossover, di mutasi, repeat hingga populasi baru mencapai max_population
    i = 1
    while len(new_chromosomes) < max_population:
        print("ITERASI KE=" + str(i))
        chromosome1, chromosome2 = select_chromosomes_to_pair(new_chromosomes, 0.2)
        anak = crossover_single_point(chromosome1, chromosome2)
        mutant = mutation_random_gene(anak)
        print("MUTANT=", mutant, 'FC=', calc_fitness(mutant))  # Print in console
        new_chromosomes.append(mutant)
        chromosomes_fc = [[chromosome, calc_fitness(chromosome)] for chromosome in new_chromosomes]
        chromosomes_fc.sort(key=lambda x: x[1], reverse=True)
        print("BEST=", chromosomes_fc[0][0], "FC=", chromosomes_fc[0][1])
        i += 1
    return new_chromosomes, False


# Contoh sederhana 2 parent only
# chrom1 = [1, 1, 3, 4, 5, 5, 6]
# print(calc_fitness(chrom1))
# for i in range(25):
#     print("MUTASI KE-" + str(i))
#     mutated = mutation_add_subtract_single(chrom1)
#     print("HASIL MUTASI=", mutated)
#
# for i in range(15):
#     chromosome = make_random_chromosome()
#     print("i=", i+1, "CHROMOSOME=", chromosome, 'FC=', calc_fitness(chromosome))

# chromosomes = [make_random_chromosome() for _ in range(10)]
# print(chromosomes)
# selection_tournament(chromosomes, 5)
# print(chromosomes)

def initialize():
    chromosomes = [make_random_chromosome() for _ in range(populasi_awal)]
    end = False
    for i in range(generasi):  # Coba run x generasi
        if not end:
            print("GENERASI KE-" + str(i + 1), end=" ")

            # Matplotlib section
            # fig, ax = plt.subplots()
            # bins = np.arange(-20, 18, 1)
            #
            # fitnesses = [calc_fitness(chromosome) for chromosome in chromosomes]
            #
            # n, bins, patches = ax.hist(fitnesses, bins=bins)
            #
            # for patch, bin_edge in zip(patches, bins[:-1]):  # bins[:-1] gives the left edges of bins
            #     if 16 <= bin_edge < 17:
            #         patch.set_facecolor('gold')  # Change color of specific bars
            #
            # ax.set_xlabel('Fitness')
            # ax.set_ylabel('Frequency')
            # ax.set_title('Histogram of Chromosomes Fitness Generation ' + str(i + 1))
            #
            # plt.savefig('generated/chromosomes_fitness_generation_' + str(i + 1) + '.png')
            # plt.close()
            # Matplotlib section end

            chromosomes, end = generate_population_and_replace_old(chromosomes)

    if end:
        bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'July', 'Agustus', 'September', 'Oktober',
                 'November', 'Desember']
        print("JADWAL MAINTENANCE PEMBANGKIT LISTRIK SELAMA 1 TAHUN")
        best_chromosome = chromosomes[0]

        data = []
        for index, gene in enumerate(best_chromosome):
            maintenance_1 = bulan[gene - 1]  # First maintenance month
            maintenance_2 = bulan[gene + 6 - 1]  # Second maintenance month
            if units[index]['interval'] == 2:
                maintenance_1 += " & " + bulan[gene]
                maintenance_2 += " & " + bulan[gene + 6]
            data.append([f"Pembangkit Listrik Unit {index + 1}", maintenance_1, maintenance_2])

        # Make DataFrame
        df = pd.DataFrame(data, columns=['Unit', 'Maintenance 1', 'Maintenance 2'])

        print(df)
        return True
    return False

initialize()

# Testing failure rate untuk 100 test run case (Untuk mengecek mutasi order changing, add subtract single/double)
failure_rate = 0
for i in range(500):
    success = initialize()
    if not success:
        failure_rate += 1
print(failure_rate)

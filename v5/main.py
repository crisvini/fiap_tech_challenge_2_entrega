# Otimização de rotas de viagem com algoritmo genético e custos de hotel variáveis

import pygame
from pygame.locals import *
import random
import itertools
from genetic_algorithm import (
    order_crossover,
    mutate,
    generate_random_population,
    calculate_fitness,
    sort_population,
    precompute_distance_matrix,
    tournament_selection,
    generate_random_individual
)
from draw_pygame import draw_paths, draw_plot, draw_locations, draw_text
import sys

# --- CONFIGURAÇÕES DA TELA E DO JOGO ---
WIDTH, HEIGHT = 1200, 700
NODE_RADIUS = 10
FPS = 30
PLOT_X_OFFSET = 450  # Offset para o gráfico de fitness

# --- CONFIGURAÇÕES DO PROBLEMA (NÚMERO DE PONTOS) ---
N_VISITAS = 65  # Número de locais de visita obrigatória
N_HOTELS = 20  # Número total de hotéis disponíveis para escolha
NUM_HOTELS_TO_VISIT = 5  # Número ALVO de hotéis que devem ser selecionados na rota

# --- PARÂMETROS DO ALGORITMO GENÉTICO ---
POPULATION_SIZE = 400  # Tamanho da população em cada geração
N_GENERATIONS = 1500  # Número máximo de gerações a serem executadas
ELITE_COUNT = 3  # Quantos dos melhores indivíduos passam diretamente para a próxima geração

# --- PARÂMETROS PARA REINICIALIZAÇÃO DA POPULAÇÃO ---
STAGNATION_LIMIT = 200  # Reduzido para testar resets mais frequentes
RESET_POPULATION_PERCENTAGE = 0.50  # Aumentado para maior injeção de diversidade
# --- FIM PARÂMETROS PARA REINICIALIZAÇÃO ---

MUTATION_PROBABILITY = 0.08  # Aumentado ligeiramente para mais exploração
TOURNAMENT_SIZE = 5  # Tamanho do torneio para a seleção dos pais

# --- CONFIGURAÇÕES DE CUSTO PARA O CÁLCULO DE FITNESS (PARA O AG OTIMIZAR) ---
# Fator para escalar os custos de visita e hotel no cálculo de fitness.
# Isso é crucial para que esses custos tenham um peso comparável à distância (em pixels/KM).
# Ajuste este valor se o AG ainda não estiver otimizando bem os hotéis/visitas
COST_SCALE_FACTOR = 10.0

# Custo em "unidades de fitness" para cada visita obrigatória.
VISIT_FITNESS_COST = 5 * COST_SCALE_FACTOR

# Custo em "unidades de fitness" para cada hotel selecionado.
# Custo financeiro mínimo para um hotel (para relatório final)
MIN_HOTEL_FINANCIAL_COST = 100
# Custo financeiro máximo para um hotel (para relatório final)
MAX_HOTEL_FINANCIAL_COST = 500

# --- CONFIGURAÇÕES DE CUSTOS FINANCEIROS REAIS (APENAS PARA O RELATÓRIO FINAL) ---
GAS_PRICE_PER_LITER = 5.0  # Preço do combustível em R$/litro
KM_PER_LITER = 12.0  # Consumo do veículo em km/litro
# Custo financeiro de cada visita obrigatória (R$)
COST_PER_VISIT_FINANCIAL = 5.0

# --- CORES ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)  # Cor para as visitas
GREEN = (0, 255, 0)  # Cor para os hotéis
GRAY = (128, 128, 128)  # Cor para a segunda melhor rota

# --- INICIALIZAÇÃO DO PYGAME ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
map_image = pygame.image.load("mapa.png").convert()
map_image = pygame.transform.scale(map_image, (WIDTH, HEIGHT))
pygame.display.set_caption('Otimização de Rotas com AG')
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)

# --- GERAÇÃO DOS LOCAIS (VISITAS E HOTÉIS) ---
visit_locations = [(random.randint(NODE_RADIUS + PLOT_X_OFFSET, WIDTH - NODE_RADIUS),
                    random.randint(NODE_RADIUS, HEIGHT - NODE_RADIUS))
                   for _ in range(N_VISITAS)
                   ]

hotel_locations = [(random.randint(NODE_RADIUS + PLOT_X_OFFSET, WIDTH - NODE_RADIUS),
                    random.randint(NODE_RADIUS, HEIGHT - NODE_RADIUS))
                   for _ in range(N_HOTELS)
                   ]

all_locations = visit_locations + hotel_locations

hotel_financial_costs_map = [0.0] * N_VISITAS + [random.uniform(
    MIN_HOTEL_FINANCIAL_COST, MAX_HOTEL_FINANCIAL_COST) for _ in range(N_HOTELS)]

distance_matrix = precompute_distance_matrix(all_locations)

population = generate_random_population(
    N_VISITAS, N_HOTELS, NUM_HOTELS_TO_VISIT, POPULATION_SIZE)

# Variáveis para acompanhar o melhor fitness e estagnação
best_fitness_values = []

best_overall_fitness = float('inf')
generations_without_improvement = 0

# --- LOOP PRINCIPAL DO ALGORITMO GENÉTICO ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.K_q:
            running = False

    generation = next(generation_counter)

    if N_GENERATIONS is not None and generation > N_GENERATIONS:
        print(
            f"Critério de parada: Atingido o número máximo de gerações ({N_GENERATIONS}).")
        running = False
        break

    map_area_rect = pygame.Rect(
        PLOT_X_OFFSET, 0, WIDTH - PLOT_X_OFFSET, HEIGHT)
    pygame.draw.rect(screen, WHITE, pygame.Rect(0, 0, PLOT_X_OFFSET, HEIGHT))

    # Desenha o mapa no lado direito
    map_area_rect = pygame.Rect(
        PLOT_X_OFFSET, 0, WIDTH - PLOT_X_OFFSET, HEIGHT)
    screen.blit(map_image, (PLOT_X_OFFSET, 0), map_area_rect)

    population_fitness = []
    for individual_tuple in population:
        current_fitness = calculate_fitness(
            individual_tuple,
            distance_matrix,
            N_VISITAS,
            VISIT_FITNESS_COST,
            hotel_financial_costs_map,
            COST_SCALE_FACTOR
        )
        population_fitness.append(current_fitness)

    population, population_fitness = sort_population(
        population, population_fitness)

    current_best_fitness = population_fitness[0]
    best_solution_tuple = population[0]
    best_selected_hotels_indices = best_solution_tuple[0]
    best_solution_route_indices = best_solution_tuple[1]

    # Lógica de estagnação e REINICIALIZAÇÃO PARCIAL DA POPULAÇÃO
    if current_best_fitness < best_overall_fitness:
        best_overall_fitness = current_best_fitness
        generations_without_improvement = 0
    else:
        generations_without_improvement += 1

    if generations_without_improvement >= STAGNATION_LIMIT:
        print(
            f"Estagnação detectada por {STAGNATION_LIMIT} gerações. Realizando reinicialização parcial da população...")

        # Manter os ELITE_COUNT melhores indivíduos
        new_population = [population[i] for i in range(ELITE_COUNT)]

        # Calcular quantos indivíduos aleatórios serão gerados
        num_random_individuals = int(
            POPULATION_SIZE * RESET_POPULATION_PERCENTAGE)

        # Gerar os novos indivíduos aleatórios
        for _ in range(num_random_individuals):
            new_population.append(generate_random_individual(
                N_VISITAS, N_HOTELS, NUM_HOTELS_TO_VISIT))

        # Preencher o restante da população com indivíduos da elite (ou cópias deles)
        while len(new_population) < POPULATION_SIZE:
            new_population.append(random.choice(population[:ELITE_COUNT]))

        random.shuffle(new_population)
        population = new_population

        generations_without_improvement = 0

        print(f"População parcialmente reinicializada. Nova busca iniciada.")

    best_fitness_values.append(current_best_fitness)

    draw_plot(screen, list(range(len(best_fitness_values))),
              best_fitness_values, y_label='Fitness - Custo Total')

    draw_locations(screen, visit_locations, BLUE, NODE_RADIUS)
    draw_locations(screen, hotel_locations, GREEN, NODE_RADIUS)

    best_solution_coords = [all_locations[idx]
                            for idx in best_solution_route_indices]
    draw_paths(screen, best_solution_coords, BLUE, width=3)

    if POPULATION_SIZE > 1:
        second_best_solution_tuple = population[1]
        second_best_solution_route_indices = second_best_solution_tuple[1]
        second_best_solution_coords = [all_locations[idx]
                                       for idx in second_best_solution_route_indices]
        draw_paths(screen, second_best_solution_coords,
                   rgb_color=GRAY, width=1)

    best_solution_distance = 0
    num_cities_in_display_route = len(best_solution_route_indices)

    for i in range(num_cities_in_display_route):
        current_city_idx = best_solution_route_indices[i]
        next_city_idx = best_solution_route_indices[(
            i + 1) % num_cities_in_display_route]
        best_solution_distance += distance_matrix[(
            current_city_idx, next_city_idx)]

    y_base = 400
    draw_text(screen, f'Geracao: {generation}', BLACK, (10, y_base))
    draw_text(
        screen, f'Fitness: {round(current_best_fitness, 2)}', BLACK, (10, y_base + 20))
    draw_text(
        screen, f'Distancia: {round(best_solution_distance, 2)}', BLACK, (10, y_base + 40))
    draw_text(screen, f'N Visitas: {N_VISITAS}', BLUE, (10, HEIGHT - 50))
    draw_text(
        screen, f'N Hoteis: {N_HOTELS} (Alvo: {NUM_HOTELS_TO_VISIT})', GREEN, (10, HEIGHT - 30))

    travel_speed_km_h = 60
    total_travel_seconds = (best_solution_distance / travel_speed_km_h) * 3600

    days = int(total_travel_seconds // (24 * 3600))
    hours = int((total_travel_seconds % (24 * 3600)) // 3600)
    minutes = int((total_travel_seconds % 3600) // 60)
    seconds = int(total_travel_seconds % 60)

    time_parts = []
    if days > 0:
        time_parts.append(f"{days} dia{'s' if days > 1 else ''}")
    if hours > 0:
        time_parts.append(f"{hours} hora{'s' if hours > 1 else ''}")
    if minutes > 0:
        time_parts.append(f"{minutes} minuto{'s' if minutes > 1 else ''}")
    if seconds > 0 or not time_parts:
        time_parts.append(f"{seconds} segundo{'s' if seconds > 1 else ''}")

    time_str_human_readable = ", ".join(time_parts)
    if not time_str_human_readable:
        time_str_human_readable = "0 segundos"

    # Imprime informações no console para cada geração (resumido)
    print(
        f'Generation {generation}: Fitness = {round(current_best_fitness, 2)}')

    # --- CRIAÇÃO DA NOVA GERAÇÃO ---
    if generations_without_improvement < STAGNATION_LIMIT:
        new_population = [population[i] for i in range(ELITE_COUNT)]

        while len(new_population) < POPULATION_SIZE:
            parent1_tuple = tournament_selection(
                population, population_fitness, TOURNAMENT_SIZE)
            parent2_tuple = tournament_selection(
                population, population_fitness, TOURNAMENT_SIZE)

            # Passa parâmetros adicionais para order_crossover
            child_tuple = order_crossover(
                parent1_tuple, parent2_tuple, N_VISITAS, N_HOTELS, NUM_HOTELS_TO_VISIT)

            # Passa parâmetros adicionais para mutate
            child_tuple = mutate(child_tuple, MUTATION_PROBABILITY, N_VISITAS,
                                 N_HOTELS, NUM_HOTELS_TO_VISIT, distance_matrix)

            new_population.append(child_tuple)

        population = new_population

    pygame.display.flip()
    clock.tick(FPS)

# --- RESULTADOS FINAIS APÓS O TÉRMINO DO ALGORITMO ---
final_best_solution_tuple = population[0]
final_best_solution_route_indices = final_best_solution_tuple[1]
final_selected_hotels_indices = final_best_solution_tuple[0]

final_best_solution_distance = 0

num_cities_in_final_route = len(final_best_solution_route_indices)

for i in range(num_cities_in_final_route):
    current_city_idx = final_best_solution_route_indices[i]
    next_city_idx = final_best_solution_route_indices[(
        i + 1) % num_cities_in_final_route]
    final_best_solution_distance += distance_matrix[(
        current_city_idx, next_city_idx)]


final_best_solution_coords = [all_locations[idx]
                              for idx in final_best_solution_route_indices]

travel_speed_km_h = 60
final_total_travel_seconds = (
    final_best_solution_distance / travel_speed_km_h) * 3600

final_days = int(final_total_travel_seconds // (24 * 3600))
final_hours = int((final_total_travel_seconds % (24 * 3600)) // 3600)
final_minutes = int((final_total_travel_seconds % 3600) // 60)
final_seconds = int(final_total_travel_seconds % 60)

final_time_parts = []
if final_days > 0:
    final_time_parts.append(f"{final_days} dia{'s' if final_days > 1 else ''}")
if final_hours > 0:
    final_time_parts.append(
        f"{final_hours} hora{'s' if final_hours > 1 else ''}")
if final_minutes > 0:
    final_time_parts.append(
        f"{final_minutes} minuto{'s' if final_minutes > 1 else ''}")
if final_seconds > 0 or not final_time_parts:
    final_time_parts.append(
        f"{final_seconds} segundo{'s' if final_seconds > 1 else ''}")

final_time_str_human_readable = ", ".join(final_time_parts)
if not final_time_str_human_readable:
    final_time_str_human_readable = "0 segundos"

cost_hotels_financial = 0
for hotel_idx in final_selected_hotels_indices:
    if hotel_idx >= N_VISITAS:
        cost_hotels_financial += hotel_financial_costs_map[hotel_idx]
    else:
        pass

cost_visits_financial = N_VISITAS * COST_PER_VISIT_FINANCIAL
cost_gasoline = (final_best_solution_distance /
                 KM_PER_LITER) * GAS_PRICE_PER_LITER

print(f'\n--- Custos Financeiros Estimados da Melhor Rota ---')
print(f'Custo de hotéis selecionados = R$ {round(cost_hotels_financial, 2)}')
print(
    f'Custo de visitas (baseado em {COST_PER_VISIT_FINANCIAL} R$/visita) = R$ {round(cost_visits_financial, 2)}')
print(f'Custo de gasolina = R$ {round(cost_gasoline, 2)}')
print(
    f'Custo Total da Viagem (Estimado) = R$ {round(cost_hotels_financial + cost_visits_financial + cost_gasoline, 2)}')

print(f'\n--- Resultados Finais da Otimização ---')
print(f'Execução finalizada após {generation - 1} gerações.')
print(f'Distância Total da Rota: {round(final_best_solution_distance, 2)} km')
print(
    f'Essa viagem de {round(final_best_solution_distance, 2)} KM dura {final_time_str_human_readable}')
print(f'Fitness Final (Melhor Otimização): {round(best_overall_fitness, 2)}')


pygame.quit()
sys.exit()

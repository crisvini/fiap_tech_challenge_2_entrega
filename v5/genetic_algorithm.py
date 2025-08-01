import random
import math

# --- Funções Auxiliares ---


def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def precompute_distance_matrix(locations):
    n = len(locations)
    distance_matrix = {}
    for i in range(n):
        for j in range(i + 1, n):
            dist = euclidean_distance(locations[i], locations[j])
            distance_matrix[(i, j)] = dist
            distance_matrix[(j, i)] = dist
    return distance_matrix

# --- Geração da População ---


def generate_random_individual(n_visitas, n_hotels, num_hotels_to_visit):
    all_hotel_indices_in_all_locations = list(
        range(n_visitas, n_visitas + n_hotels))
    selected_hotels_indices = random.sample(
        all_hotel_indices_in_all_locations, num_hotels_to_visit)

    # A rota inicial inclui todas as visitas e os hotéis selecionados
    base_route_indices = list(range(n_visitas)) + selected_hotels_indices
    # Embaralha para gerar uma rota inicial aleatória
    random.shuffle(base_route_indices)

    return (selected_hotels_indices, base_route_indices)


def generate_random_population(n_visitas, n_hotels, num_hotels_to_visit, population_size):
    return [generate_random_individual(n_visitas, n_hotels, num_hotels_to_visit) for _ in range(population_size)]

# --- Cálculo de Fitness ---


def calculate_fitness(individual_tuple, distance_matrix,  n_visitas, VISIT_FITNESS_COST, hotel_financial_costs_map, COST_SCALE_FACTOR):
    selected_hotels_indices = individual_tuple[0]
    route_indices = individual_tuple[1]

    total_distance = 0.0
    total_point_cost = 0.0

    num_points_in_route = len(route_indices)

    # Verifica se a rota possui os pontos corretos para evitar IndexErrors
    expected_route_points = set(range(n_visitas)).union(
        set(selected_hotels_indices))
    if set(route_indices) != expected_route_points or len(route_indices) != len(expected_route_points):
        # Penalidade pesada para rotas inválidas (pontos faltantes/duplicados)
        return float('inf')

    # Calcula a distância total da rota
    for i in range(num_points_in_route):
        current_idx = route_indices[i]
        next_idx = route_indices[(i + 1) % num_points_in_route]
        total_distance += distance_matrix[(current_idx, next_idx)]

    for idx in route_indices:
        if idx < n_visitas:
            total_point_cost += VISIT_FITNESS_COST  # custo fixo para visitas
        else:
            # custo real do hotel ajustado
            total_point_cost += hotel_financial_costs_map[idx] * \
                COST_SCALE_FACTOR

    # --- FIM Lógica ---

    fitness = total_distance + total_point_cost
    return fitness


def sort_population(population, population_fitness):
    combined = sorted(zip(population, population_fitness), key=lambda x: x[1])
    sorted_population = [item[0] for item in combined]
    sorted_population_fitness = [item[1] for item in combined]
    return sorted_population, sorted_population_fitness

# --- Seleção ---


def tournament_selection(population, population_fitness, tournament_size):
    selected_indices = random.sample(range(len(population)), tournament_size)
    best_competitor_index = selected_indices[0]
    for i in range(1, tournament_size):
        if population_fitness[selected_indices[i]] < population_fitness[best_competitor_index]:
            best_competitor_index = selected_indices[i]
    return population[best_competitor_index]

# --- Crossover (Recombinação) ---


def order_crossover(parent1_tuple, parent2_tuple, n_visitas, n_hotels, num_hotels_to_visit):
    parent1_selected_hotels = parent1_tuple[0]
    parent1_route = parent1_tuple[1]
    parent2_selected_hotels = parent2_tuple[0]
    parent2_route = parent2_tuple[1]

    n_route = len(parent1_route)

    # --- Crossover para os hotéis selecionados (combinação mais inteligente) ---
    combined_hotels = list(
        set(parent1_selected_hotels + parent2_selected_hotels))

    if len(combined_hotels) > num_hotels_to_visit:
        child_selected_hotels = random.sample(
            combined_hotels, num_hotels_to_visit)
    elif len(combined_hotels) == num_hotels_to_visit:
        child_selected_hotels = combined_hotels
    else:  # Se a combinação não tem hotéis suficientes
        child_selected_hotels = combined_hotels
        all_possible_hotel_indices = set(
            range(n_visitas, n_visitas + n_hotels))
        available_to_add = list(
            all_possible_hotel_indices - set(child_selected_hotels))

        missing_count = num_hotels_to_visit - len(child_selected_hotels)
        if len(available_to_add) >= missing_count:
            child_selected_hotels.extend(
                random.sample(available_to_add, missing_count))
        # Se não houver hotéis suficientes disponíveis para adicionar, a penalidade no fitness tratará isso.

    # --- Crossover de Ordem (OX1) para a rota ---
    start_point = random.randint(0, n_route - 1)
    end_point = random.randint(0, n_route - 1)

    if start_point > end_point:
        start_point, end_point = end_point, start_point

    child_route = [None] * n_route
    child_route[start_point:end_point +
                1] = parent1_route[start_point:end_point + 1]

    parent2_index = 0
    for i in range(n_route):
        if child_route[i] is None:
            while parent2_route[parent2_index] in child_route:
                parent2_index += 1
            child_route[i] = parent2_route[parent2_index]
            parent2_index += 1

    return (child_selected_hotels, child_route)

# --- Mutação ---


def mutate(individual_tuple, mutation_probability, n_visitas, n_hotels, num_hotels_to_visit, distance_matrix):
    selected_hotels_indices = list(individual_tuple[0])
    route_indices = list(individual_tuple[1])

    # --- Mutação na seleção de hotéis (troca um hotel selecionado por um não selecionado) ---
    if random.random() < mutation_probability:
        all_possible_hotel_indices = set(
            range(n_visitas, n_visitas + n_hotels))
        currently_selected_hotels_set = set(selected_hotels_indices)
        unselected_hotels = list(
            all_possible_hotel_indices - currently_selected_hotels_set)

        if currently_selected_hotels_set and unselected_hotels:
            hotel_to_remove = random.choice(
                list(currently_selected_hotels_set))
            hotel_to_add = random.choice(unselected_hotels)

            selected_hotels_indices.remove(hotel_to_remove)
            selected_hotels_indices.append(hotel_to_add)

    # --- Garantir que o número de hotéis selecionados esteja EXATAMENTE correto ---
    if len(selected_hotels_indices) != num_hotels_to_visit:
        all_possible_hotel_indices = set(
            range(n_visitas, n_visitas + n_hotels))

        while len(selected_hotels_indices) > num_hotels_to_visit:
            selected_hotels_indices.remove(
                random.choice(selected_hotels_indices))

        while len(selected_hotels_indices) < num_hotels_to_visit:
            available_to_add = list(
                all_possible_hotel_indices - set(selected_hotels_indices))
            if not available_to_add:
                break  # Nao há mais hotéis para adicionar
            selected_hotels_indices.append(random.choice(available_to_add))

    # --- NOVA LÓGICA: Mutação na ordem da rota (mutação por inversão de segmento) ---
    # Esta é uma mutação mais poderosa para otimização de rotas (TSP).
    if random.random() < mutation_probability:
        if len(route_indices) > 2:  # Precisa de pelo menos 3 pontos para ter um segmento para inverter
            idx1, idx2 = random.sample(range(len(route_indices)), 2)
            if idx1 > idx2:
                idx1, idx2 = idx2, idx1

            # Inverte o segmento entre idx1 e idx2 (inclusive)
            route_indices[idx1:idx2+1] = route_indices[idx1:idx2+1][::-1]

    # --- Reconstruir a rota para garantir que contém todos os pontos necessários
    # e tentar otimizar a inserção de novos pontos (especialmente hotéis) ---
    required_points_set = set(range(n_visitas)).union(
        set(selected_hotels_indices))

    # 1. Remove pontos da rota atual que não são mais necessários ou não estão no conjunto final
    current_valid_route = [
        p for p in route_indices if p in required_points_set]

    # 2. Identifica os pontos que precisam ser adicionados
    points_to_add = list(required_points_set - set(current_valid_route))

    # 3. Para cada ponto a ser adicionado, insere na melhor posição que minimiza o custo
    for p_add in points_to_add:
        if not current_valid_route:  # Se a rota estiver vazia, apenas adiciona
            current_valid_route.append(p_add)
        else:
            best_insert_pos = -1
            min_cost_increase = float('inf')

            # Itera por todas as posições possíveis para inserir o ponto
            for i in range(len(current_valid_route) + 1):
                cost_increase_candidate = 0.0

                # Inserir no início da rota (entre o final e o início original)
                if i == 0:
                    # Custo para ligar o novo ponto ao que era o primeiro e ao que era o último (considerando rota cíclica)
                    cost_increase_candidate = distance_matrix[(
                        p_add, current_valid_route[0])] + distance_matrix[(current_valid_route[-1], p_add)]
                # Inserir no final da rota (entre o último e o primeiro original)
                elif i == len(current_valid_route):
                    # Custo para ligar o que era o último ao novo ponto e o novo ponto ao que era o primeiro (considerando rota cíclica)
                    cost_increase_candidate = distance_matrix[(
                        current_valid_route[-1], p_add)] + distance_matrix[(p_add, current_valid_route[0])]
                # Inserir no meio da rota (entre current_valid_route[i-1] e current_valid_route[i])
                else:
                    # Remove o custo da aresta original
                    cost_increase_candidate -= distance_matrix[(
                        current_valid_route[i-1], current_valid_route[i])]
                    # Adiciona o custo das duas novas arestas
                    cost_increase_candidate += distance_matrix[(
                        current_valid_route[i-1], p_add)] + distance_matrix[(p_add, current_valid_route[i])]

                if cost_increase_candidate < min_cost_increase:
                    min_cost_increase = cost_increase_candidate
                    best_insert_pos = i

            if best_insert_pos != -1:
                current_valid_route.insert(best_insert_pos, p_add)
            else:
                # Fallback: Se a busca pela melhor posição falhar por algum motivo, insere aleatoriamente
                current_valid_route.insert(random.randint(
                    0, len(current_valid_route)), p_add)

    # Garante que não há duplicatas e que todos os pontos necessários estão na rota final
    final_route = []
    seen = set()
    for p in current_valid_route:
        if p not in seen and p in required_points_set:  # Verifica se o ponto é único e necessário
            final_route.append(p)
            seen.add(p)

    # Último fallback: se, por algum motivo, a rota ainda não estiver correta (pontos faltando ou sobrando)
    if len(final_route) != len(required_points_set):
        final_route = list(required_points_set)
        random.shuffle(final_route)  # Reinicia com uma rota aleatória válida

    return (selected_hotels_indices, final_route)

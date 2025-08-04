# FIAP Tech Challenge - Fase 2

### Alunos
- **Cristian Vinícius Leoncini Lopes - RM 362011**
- **Júlia de Andrade Bertazzi - RM 361574**
- **Luiz Henrique Beluci Terra - RM 363804**

---

## Perguntas Iniciais

### O que você está otimizando?  
Estamos **minimizando o custo total de uma viagem**, que inclui:
- Distância total percorrida na rota (proporcional a km).
- Custos de visitas obrigatórias.
- Custos dos hotéis selecionados.

O objetivo é encontrar a rota mais eficiente que combine visitas e hospedagens dentro de restrições de orçamento e número de dias.

### Qual é a variável que quer maximizar ou minimizar?  
- **Minimizar:** Distância total + custos financeiros (visitas + hotéis).  
- **Maximizar:** Eficiência da rota (melhor uso do tempo e dinheiro).

### Qual é a representação da solução (genoma)?  
Cada indivíduo (solução) é uma tupla com:
- `selected_hotels_indices`: Lista de índices dos hotéis escolhidos.  
- `route_indices`: Ordem em que todos os pontos (visitas + hotéis selecionados) serão visitados.

### Qual é a função de fitness?  
A função de fitness soma:
1. **Distância total da rota** (usando matriz de distâncias pré-computada).  
2. **Custo fixo por visita obrigatória.**  
3. **Custo financeiro real dos hotéis selecionados (escalado).**

Quanto **menor** o valor de fitness, melhor a solução.

### Qual é o método de seleção?  
**Torneio (Tournament Selection)**:  
- Seleciona aleatoriamente um grupo de indivíduos.  
- O melhor dentro do grupo vence e é escolhido como pai.

### Qual método de crossover?  
**Order Crossover (OX1)**:  
- Mantém a ordem relativa de um segmento da rota de um pai.  
- Preenche o restante com os genes do outro pai, garantindo diversidade e preservação de boas sub-rotas.  
- Os hotéis selecionados passam por uma combinação inteligente entre os dois pais.

### Qual será o método de inicialização?  
- População inicial gerada de forma **aleatória**, garantindo:
  - Seleção de um número fixo de hotéis.
  - Embaralhamento da rota inicial para diversidade.

### Qual o critério de parada?  
- Número máximo de gerações (`N_GENERATIONS`).  
- Reinicialização parcial da população se houver **estagnação** (sem melhorias após X gerações).

---

## Descrição do Problema

O desafio consiste em **planejar uma viagem** passando por vários pontos turísticos e escolhendo um número limitado de hotéis, de forma a **minimizar os custos totais**.  
O problema se assemelha a uma variação do **Traveling Salesman Problem (TSP)**, com a complexidade adicional de incluir:
- Custos financeiros reais.
- Seleção de um subconjunto de hotéis.
- Restrições de orçamento e tempo de viagem.

---

## Abordagem Utilizada

### Algoritmo Genético (AG)
- **Representação:** Cada indivíduo é uma rota completa + seleção de hotéis.  
- **Fitness:** Combina distância e custos financeiros.  
- **Seleção:** Torneio.  
- **Crossover:** OX1 adaptado para manter hotéis e ordem de visitas.  
- **Mutação:**  
  - Troca de hotéis.  
  - Inversão de segmentos da rota (mutation por inversão).  
- **Reinicialização:**  
  - Quando a população entra em estagnação, metade dela é substituída por indivíduos novos para evitar convergência prematura.

### Visualização
- Implementação em **Pygame** mostrando:
  - Rota atual.
  - Evolução do fitness ao longo das gerações.
  - Custos estimados da viagem.

---

## Resultados Obtidos

- O AG foi capaz de encontrar rotas **com custo total significativamente menor** em relação a uma escolha aleatória de pontos.  
- O uso de reinicialização parcial aumentou a diversidade e evitou que o algoritmo ficasse preso em mínimos locais.  
- As soluções finais respeitam:
  - Número alvo de hotéis.
  - Minimização de custos e distância.

Exemplo de resultados finais:
- Custos Financeiros Estimados da Melhor Rota:
  - Custo de hotéis selecionados = R$ 731.82
  - Custo de visitas (baseado em 5.0 R$/visita) = R$ 325.0
  - Custo de gasolina = R$ 2059.24
  - Custo Total da Viagem (Estimado) = R$ 3116.06

- Resultados Finais da Otimização:
  - Execução finalizada após 2000 gerações.
  - Distância Total da Rota: 4942.17 km
  - Essa viagem de 4942.17 KM dura 3 dias, 10 horas, 22 minutos, 10 segundos
  - Fitness Final (Melhor Otimização): 15510.39

---

## Conclusões

- O uso de Algoritmos Genéticos para problemas de otimização de rotas é **eficaz** quando a busca exata é inviável devido ao espaço de soluções ser muito grande.  
- A combinação de **crossover de ordem (OX1)** + **mutação por inversão** demonstrou bons resultados na preservação de sub-rotas eficientes.  
- A inclusão de **custos reais** (hotéis e combustível) permitiu que o AG buscasse soluções mais próximas de cenários práticos.  
- A **reinicialização parcial** foi essencial para manter a diversidade e evitar convergência prematura.

---

## Como Executar

1. Certifique-se de ter o Python 3 instalado em seu sistema.

2. Instale as dependências do projeto:

```bash
pip install pygame matplotlib numpy
```
3. Execute o algoritmo com o comando:

```bash
python main.py
```
4. A janela será aberta mostrando:
  - O mapa com os pontos turísticos e hotéis.
  - As rotas otimizadas em tempo real.
  - O gráfico de evolução do fitness.
  - Informações como tempo estimado de viagem, distância e custos.

---

## Observações Finais

- A inclusão de fatores reais, como preços de hotéis e consumo de combustível, torna o modelo mais próximo de um cenário realista.
- A visualização interativa via Pygame facilita a compreensão do comportamento do AG ao longo das gerações.

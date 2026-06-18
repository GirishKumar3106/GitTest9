from flask import Flask, render_template, request, jsonify
import math
import heapq

app = Flask(__name__)

# Weighted Social Network Graph
social_graph = {
    'Alice': {'Bob': 2, 'Charlie': 4, 'Diana': 1},
    'Bob': {'Alice': 2, 'Eve': 3, 'Frank': 5},
    'Charlie': {'Alice': 4, 'Grace': 2},
    'Diana': {'Alice': 1, 'Harry': 4},
    'Eve': {'Bob': 3, 'Ivy': 2},
    'Frank': {'Bob': 5, 'Grace': 1},
    'Grace': {'Charlie': 2, 'Frank': 1, 'Jack': 3},
    'Harry': {'Diana': 4, 'Jack': 2},
    'Ivy': {'Eve': 2},
    'Jack': {'Grace': 3, 'Harry': 2}
}

# Coordinates for A* and IDA*
coords = {
    'Alice': (0, 0),
    'Bob': (1, 1),
    'Charlie': (-1, 1),
    'Diana': (0, -1),
    'Eve': (2, 2),
    'Frank': (0, 2),
    'Grace': (-2, 2),
    'Harry': (-1, -2),
    'Ivy': (3, 3),
    'Jack': (-2, -1)
}


def get_heuristic(node, goal):
    x1, y1 = coords.get(node, (0, 0))
    x2, y2 = coords.get(goal, (0, 0))

    return math.sqrt(
        (x1 - x2) ** 2 +
        (y1 - y2) ** 2
    )


def calculate_cost(path):
    if len(path) < 2:
        return 0

    total = 0

    for i in range(len(path) - 1):
        total += social_graph[path[i]][path[i + 1]]

    return total


def dijkstra_path(graph, start, goal):

    if start not in graph or goal not in graph:
        return []

    queue = [(0, start, [start])]
    visited = {}

    while queue:

        cost, node, path = heapq.heappop(queue)

        if node == goal:
            return path

        if node in visited and visited[node] <= cost:
            continue

        visited[node] = cost

        for neighbor, weight in graph[node].items():

            heapq.heappush(
                queue,
                (
                    cost + weight,
                    neighbor,
                    path + [neighbor]
                )
            )

    return []


def a_star_path(graph, start, goal):

    if start not in graph or goal not in graph:
        return []

    queue = []

    heapq.heappush(
        queue,
        (
            get_heuristic(start, goal),
            0,
            [start]
        )
    )

    g_costs = {
        start: 0
    }

    while queue:

        _, current_cost, path = heapq.heappop(queue)

        node = path[-1]

        if node == goal:
            return path

        for adjacent, weight in graph[node].items():

            new_cost = current_cost + weight

            if (
                adjacent not in g_costs
                or
                new_cost < g_costs[adjacent]
            ):

                g_costs[adjacent] = new_cost

                f_cost = (
                    new_cost +
                    get_heuristic(adjacent, goal)
                )

                heapq.heappush(
                    queue,
                    (
                        f_cost,
                        new_cost,
                        path + [adjacent]
                    )
                )

    return []


def ida_star_path(graph, start, goal):

    if start not in graph or goal not in graph:
        return []

    bound = get_heuristic(start, goal)

    path = [start]

    def search(node, g, bound):

        f = g + get_heuristic(node, goal)

        if f > bound:
            return f, None

        if node == goal:
            return "FOUND", list(path)

        minimum = float('inf')

        for adjacent, weight in graph[node].items():

            if adjacent not in path:

                path.append(adjacent)

                result, found_path = search(
                    adjacent,
                    g + weight,
                    bound
                )

                if result == "FOUND":
                    return "FOUND", found_path

                minimum = min(minimum, result)

                path.pop()

        return minimum, None

    while True:

        result, found_path = search(
            start,
            0,
            bound
        )

        if result == "FOUND":
            return found_path

        if result == float('inf'):
            return []

        bound = result


@app.route('/')
def index():

    nodes = sorted(
        list(social_graph.keys())
    )

    return render_template(
        'index.html',
        nodes=nodes
    )


@app.route('/get_graph')
def get_graph():

    return jsonify(social_graph)


@app.route('/add_connection', methods=['POST'])
def add_connection():

    data = request.get_json()

    p1 = data.get(
        'person1',
        ''
    ).strip()

    p2 = data.get(
        'person2',
        ''
    ).strip()

    weight = int(
        data.get(
            'weight',
            1
        )
    )

    if not p1 or not p2:

        return jsonify({
            'success': False,
            'error': 'Both names required.'
        })

    if p1 not in social_graph:
        social_graph[p1] = {}

    if p2 not in social_graph:
        social_graph[p2] = {}

    social_graph[p1][p2] = weight
    social_graph[p2][p1] = weight

    return jsonify({
        'success': True
    })


@app.route('/find_path', methods=['POST'])
def find_path():

    data = request.get_json()

    start_node = data.get('start')
    end_node = data.get('end')

    algorithm = data.get(
        'algorithm',
        'dijkstra'
    )

    if algorithm == 'astar':

        path = a_star_path(
            social_graph,
            start_node,
            end_node
        )

    elif algorithm == 'idastar':

        path = ida_star_path(
            social_graph,
            start_node,
            end_node
        )

    else:

        path = dijkstra_path(
            social_graph,
            start_node,
            end_node
        )

    cost = calculate_cost(path)

    algo_properties = {

        'dijkstra': {
            'time': 'O((V + E) log V)',
            'complete': 'Yes',
            'optimal': 'Yes'
        },

        'astar': {
            'time': 'O(b^d)',
            'complete': 'Yes',
            'optimal': 'Yes'
        },

        'idastar': {
            'time': 'O(b^d)',
            'complete': 'Yes',
            'optimal': 'Yes'
        }
    }

    return jsonify({
        'path': path,
        'cost': cost,
        'properties': algo_properties.get(
            algorithm,
            algo_properties['dijkstra']
        )
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
import csv
import os
import pandas as pd
from gurobipy import Model, GRB, quicksum
from pprint import pprint

from wip_utils import time_it, load_data, generate_output_df
from preprocessing import generate_combinations

@time_it
def build_wip_even_model_1(preprocess_result, wip_ids, wip_qtime, time_matrix, wip_from, cart_loc, cart_capacity, h=1, M=10000):
    """
    Build and solve WIP dispatching model (even case) using pair-based assignment with cart-route combinations.

    Args:
        preprocess_result (dict): {(wip1, wip2): {path: ((first_wip, second_wip), (time1, time2)), ...}}
        wip_ids (list): list of WIP IDs.
        wip_qtime (dict): mapping wip_id to q-time constraint.
        time_matrix (dict): matrix of travel times.
        wip_from (dict): mapping wip_id to from location.
        cart_loc (dict): mapping cart_id to location.
        cart_capacity (int): number of WIPs per cart (default 2).
        h (float): cost coefficient.
        M (float): penalty coefficient.

    Returns:
        tuple: (model, x) where
            - model is the solved Gurobi model.
            - x is a dict of assignment binary variables (cart, wip1, wip2).
    """

    model = Model("WIP_Even_Model")

    # Sets
    C = list(cart_loc.keys())
    C = C[:len(wip_ids)//cart_capacity]
    W = wip_ids
    Q = wip_qtime

    # Decision variables: x[c, pair] = 1 if cart c uses pair
    x = model.addVars(C, preprocess_result.keys(), vtype=GRB.BINARY, name="route")

    # Constraint 1: Each WIP assigned exactly once
    for w in W:
        model.addConstr(
            quicksum(
                x[c, (w1, w2)]
                for c in C
                for (w1, w2) in preprocess_result.keys()
                if w in (w1, w2)
            ) == 1,
            name=f"assign_{w}"
        )

    # Constraint 2: Each cart assigned at most one pair
    for c in C:
        model.addConstr(
            quicksum(
                x[c, pair]
                for pair in preprocess_result.keys()
            ) <= 1,
            name=f"cart_use_limit_{c}"
        )

    # Objective components
    total_cost = quicksum(
        x[c, (w1, w2)] * min(
            time_matrix[cart_loc[c]][wip_from[path[0]]] + info[1][1]
            for path, info in preprocess_result[(w1, w2)].items()
        )
        for c in C
        for (w1, w2) in preprocess_result.keys()
    )

    total_penalty = quicksum(
        x[c, (w1, w2)] * (
            max(0, min(
                time_matrix[cart_loc[c]][wip_from[path[0]]] + info[1][0] - Q[info[0][0]]
                for path, info in preprocess_result[(w1, w2)].items()
            )) +
            max(0, min(
                time_matrix[cart_loc[c]][wip_from[path[0]]] + info[1][1] - Q[info[0][1]]
                for path, info in preprocess_result[(w1, w2)].items()
            ))
        )
        for c in C
        for (w1, w2) in preprocess_result.keys()
    )

    model.setObjective(h * total_cost + M * total_penalty, GRB.MINIMIZE)
    model.update()
    model.optimize()

    return model, x


@time_it
def build_wip_even_model_2(preprocess_result, wip_ids, wip_qtime, time_matrix, wip_from, cart_loc, cart_capacity, h=1, M=10000):
    """
    Build and solve WIP dispatching model (even case) using scalable formulation with cart-WIP assignment and pairwise path evaluation.

    Args:
        preprocess_result (dict): {(wip1, wip2): {path: ((first_wip, second_wip), (time1, time2)), ...}}
        wip_ids (list): list of WIP IDs.
        wip_qtime (dict): mapping wip_id to q-time constraint.
        time_matrix (dict): matrix of travel times.
        wip_from (dict): mapping wip_id to from location.
        cart_loc (dict): mapping cart_id to location.
        cart_capacity (int): number of WIPs per cart (default 2).
        h (float): cost coefficient.
        M (float): penalty coefficient.

    Returns:
        tuple: (model, x) where
            - model is the solved Gurobi model.
            - x is a dict of assignment binary variables (cart, wip).
    """

    model = Model("WIP_Dispatch_Scaled_Model")

    # Sets
    C = list(cart_loc.keys())
    C = C[:len(wip_ids)//cart_capacity]
    W = wip_ids
    Q = wip_qtime

    # Decision variables: x[c, w] = 1 if wip w is assigned to cart c
    x = model.addVars(C, W, vtype=GRB.BINARY, name="assign")

    # Constraint 1: Each WIP assigned exactly once
    for w in W:
        model.addConstr(
            quicksum(x[c, w] for c in C) == 1,
            name=f"assign_{w}"
        )

    # Constraint 2: Each cart assigned exactly cart_capacity WIPs
    for c in C:
        model.addConstr(
            quicksum(x[c, w] for w in W) == cart_capacity,
            name=f"cart_capacity_{c}"
        )

    total_cost = 0
    total_penalty = 0

    for c in C:
        for (w1, w2), paths in preprocess_result.items():
            if w1 not in W or w2 not in W:
                continue

            min_cost = min(
                time_matrix[cart_loc[c]][wip_from[path[0]]] + info[1][1]
                for path, info in paths.items()
            )
            penalty_first = min(
                time_matrix[cart_loc[c]][wip_from[path[0]]] + info[1][0] - Q[info[0][0]]
                for path, info in paths.items()
            )
            penalty_second = min(
                time_matrix[cart_loc[c]][wip_from[path[0]]] + info[1][1] - Q[info[0][1]]
                for path, info in paths.items()
            )
            penalty = max(0, penalty_first) + max(0, penalty_second)

            # Linearization of x[c,w1]*x[c,w2]
            z = model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name=f"z_{c}_{w1}_{w2}")
            model.addConstr(z <= x[c, w1])
            model.addConstr(z <= x[c, w2])
            model.addConstr(z >= x[c, w1] + x[c, w2] - 1)

            total_cost += h * z * min_cost
            total_penalty += M * z * penalty

    model.setObjective(total_cost + total_penalty, GRB.MINIMIZE)
    model.update()
    model.optimize()

    return model, x


@time_it
def build_set_covering_model(preprocess_result, wip_ids, wip_qtime, time_matrix, wip_from, cart_loc, cart_capacity, h=1, M=100000):
    """
    Build and solve set covering dispatch model selecting WIP pairs to cover all WIPs.

    Args:
        preprocess_result (dict): {(wip1, wip2): {path: ((first_wip, second_wip), (time1, time2)), ...}}
        wip_ids (list): list of WIP IDs.
        wip_qtime (dict): mapping wip_id to q-time constraint.
        time_matrix (dict): matrix of travel times.
        wip_from (dict): mapping wip_id to from location.
        cart_loc (dict): mapping cart_id to location (uses first cart as reference here).
        cart_capacity (int): number of WIPs per cart (default 2).
        h (float): cost coefficient.
        M (float): penalty coefficient.

    Returns:
        tuple: (model, y, cost_s, penalty_s) where
            - model is the solved Gurobi model.
            - y is a dict of selected set binary variables.
            - cost_s is dict of cost for each set.
            - penalty_s is dict of penalty for each set.
    """

    model = Model("Set_Covering_Dispatch")

    W = wip_ids
    S = list(preprocess_result.keys())
    c_loc = cart_loc[next(iter(cart_loc))]

    # Calculate cost and penalty for each set
    cost_s = {}
    penalty_s = {}
    for (w1, w2), paths in preprocess_result.items():
        min_cost = min(
            time_matrix[c_loc][wip_from[path[0]]] + info[1][1]
            for path, info in paths.items()
        )
        penalty_first = min(
            time_matrix[c_loc][wip_from[path[0]]] + info[1][0] - wip_qtime[info[0][0]]
            for path, info in paths.items()
        )
        penalty_second = min(
            time_matrix[c_loc][wip_from[path[0]]] + info[1][1] - wip_qtime[info[0][1]]
            for path, info in paths.items()
        )
        penalty = max(0, penalty_first) + max(0, penalty_second)

        cost_s[(w1, w2)] = min_cost
        penalty_s[(w1, w2)] = penalty

    # Decision variables
    y = model.addVars(S, vtype=GRB.BINARY, name="select_set")

    # Constraints: each WIP covered exactly once
    for w in W:
        model.addConstr(
            quicksum(y[s] for s in S if w in s) == 1,
            name=f"cover_{w}"
        )

    # Objective
    obj = quicksum(
        (h * cost_s[s] + M * penalty_s[s]) * y[s]
        for s in S
    )

    model.setObjective(obj, GRB.MINIMIZE)
    model.update()
    model.optimize()


    return model, y, cost_s, penalty_s


# === Example usage ===
if __name__ == "__main__":

    # Parameters
    M = 100000
    h = 1
    cart_capacity = 2

    # Path
    time_matrix_path = "time_matrix.csv"
    cart_data_path = "cart_data.csv"
    wip_data_folder = "wip_data"
    output_folder = "output_results"
    os.makedirs(output_folder, exist_ok=True)

    for wip_data_file in os.listdir(wip_data_folder)[2:]:
        wip_data_path = os.path.join(wip_data_folder, wip_data_file)
        time_matrix, wip_ids, wip_from, wip_to, wip_qtime, cart_ids, cart_loc = load_data(
            time_matrix_path,
            cart_data_path,
            wip_data_path
        )
        core_part = wip_data_file.replace("wip_data_", "").replace(".csv", "")
        output_path = os.path.join(output_folder, f"wip_{core_part}_even.csv")

        preprocess_result = generate_combinations(wip_ids, wip_from, wip_to, time_matrix, cart_capacity)

        model, x = build_wip_even_model_1(
            preprocess_result,
            wip_ids,
            wip_qtime,
            time_matrix,
            wip_from,
            cart_loc,
            cart_capacity,
            h,
            M
        )

        df = generate_output_df(model, x, preprocess_result, time_matrix, cart_loc, wip_from, wip_to)

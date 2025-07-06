import pandas as pd
import functools
import time
from typing import Tuple, List, Dict, Any


def time_it(func):
    """Decorator to measure the execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.6f} seconds")
        return result
    return wrapper


@time_it
def load_data(
    time_matrix_path: str,
    cart_data_path: str,
    wip_data_path: str
) -> Tuple[pd.DataFrame, List[str], Dict[str, str], Dict[str, str], Dict[str, float], List[str], Dict[str, str]]:
    """
    Load time matrix, WIP data, and cart data for model input.
    """
    # Time matrix
    time_df = pd.read_csv(time_matrix_path)
    locations = sorted(time_df['FROM'].unique(), key=lambda x: int(x.replace('LOC', '')))
    time_matrix = time_df.pivot(index='FROM', columns='TO', values='XFER_TIME').reindex(index=locations, columns=locations)

    # WIP data
    wip_df = pd.read_csv(wip_data_path)
    wip_ids = wip_df['WIP_ID'].tolist()
    wip_from = dict(zip(wip_df['WIP_ID'], wip_df['FROM']))
    wip_to = dict(zip(wip_df['WIP_ID'], wip_df['TO']))
    wip_qtime = dict(zip(wip_df['WIP_ID'], wip_df['Remaining Q-Time']))

    # Cart data
    cart_df = pd.read_csv(cart_data_path)
    cart_ids = cart_df['CART_ID'].tolist()
    cart_loc = dict(zip(cart_df['CART_ID'], cart_df['INIT_LOC']))

    return time_matrix, wip_ids, wip_from, wip_to, wip_qtime, cart_ids, cart_loc


@time_it
def cal_obj_val(
    output_path: str,
    wip_data_path: str,
    M: float = 100000,
    h: float = 1
) -> Dict[str, float]:
    """
    Calculate objective value (penalty + transport cost) from output and WIP data.
    """
    output_df = pd.read_csv(output_path).sort_values(by="CART_ID")
    wip_df = pd.read_csv(wip_data_path)

    qtime_dict = dict(zip(wip_df['WIP_ID'], wip_df['Remaining Q-Time']))

    # Calculate total penalty
    delivery_df = output_df[output_df['ACTION'] == 'DELIVERY'].copy()
    delivery_df['LATENESS'] = delivery_df.apply(
        lambda row: max(0, row['COMPLETE_TIME'] - qtime_dict.get(row['WIP_ID'], float('inf'))),
        axis=1
    )
    total_penalty = delivery_df['LATENESS'].sum() * M

    # Calculate total transport
    total_transport = output_df.groupby('CART_ID')['COMPLETE_TIME'].max().sum() * h

    return {
        'total_penalty': total_penalty,
        'total_transport': total_transport,
        'total_cost': total_penalty + total_transport
    }


@time_it
def show_assigned_routes(
    model: Any,
    x: Dict[Tuple[str, str, str], Any],
    preprocess_result: Dict,
    time_matrix: pd.DataFrame,
    cart_loc: Dict[str, str],
    wip_from: Dict[str, str],
    wip_to: Dict[str, str]
) -> None:
    """
    Display optimized assigned routes in console.
    """
    print("=== Assigned Routes ===")
    for (c, w1, w2), var in x.items():
        if var.X > 0.5:
            optimal_path, info = min(
                preprocess_result[(w1, w2)].items(),
                key=lambda item: time_matrix.loc[cart_loc[c], wip_from[item[0][0]]] + item[1][1][1]
            )
            arrival_order, arrival_times = info
            t_start = time_matrix.loc[cart_loc[c], wip_from[optimal_path[0]]]

            print(f"Cart: {c}")
            print(f"  Assigned Pair: ({w1}, {w2})")
            print(f"  Optimal Path: {optimal_path}")
            print(f"  First Arrival: {arrival_order[0]} at {arrival_times[0] + t_start}")
            print(f"  Second Arrival: {arrival_order[1]} at {arrival_times[1] + t_start}")
            print("-" * 30)


@time_it
def generate_output_df(
    model: Any,
    x: Dict[Tuple[str, str, str], Any],
    preprocess_result: Dict,
    time_matrix: pd.DataFrame,
    cart_loc: Dict[str, str],
    wip_from: Dict[str, str],
    wip_to: Dict[str, str]
) -> pd.DataFrame:
    """
    Generate output DataFrame from optimized model.
    """
    rows = []
    touch_count = {w: 0 for w in wip_from}

    for (c, w1, w2), var in x.items():
        if var.X > 0.5:
            optimal_path, info = min(
                preprocess_result[(w1, w2)].items(),
                key=lambda item: time_matrix.loc[cart_loc[c], wip_from[item[0][0]]] + item[1][1][1]
            )
            curr_time = 0
            curr_loc = cart_loc[c]

            for idx, action_wip in enumerate(optimal_path):
                action = "PICKUP" if touch_count[action_wip] == 0 else "DELIVERY"
                next_loc = wip_from[action_wip] if action == "PICKUP" else wip_to[action_wip]

                travel_time = time_matrix.loc[curr_loc, next_loc]
                curr_time += travel_time

                rows.append({
                    "CART_ID": c,
                    "ORDER": idx + 1,
                    "WIP_ID": action_wip,
                    "ACTION": action,
                    "COMPLETE_TIME": curr_time
                })

                touch_count[action_wip] += 1
                curr_loc = next_loc

    return pd.DataFrame(rows, columns=["CART_ID", "ORDER", "WIP_ID", "ACTION", "COMPLETE_TIME"])


@time_it
def build_output_from_selected_sets(
    y: Dict,
    cost_s: Dict,
    penalty_s: Dict,
    preprocess_result: Dict,
    time_matrix: pd.DataFrame,
    wip_from: Dict[str, str],
    wip_to: Dict[str, str],
    initial_cart_loc: str
) -> pd.DataFrame:
    """
    Build dispatch output DataFrame from selected feasible sets using cost_s to find optimal path.
    """
    selected_sets = [s for s in preprocess_result if y[s].X > 0.5]

    rows = []
    cart_counter = 1

    for s in selected_sets:
        cart_id = f"C{cart_counter:02d}"
        cart_counter += 1
        curr_loc = initial_cart_loc

        path_dict = preprocess_result[s]

        # Identify optimal paths matching cost_s within tolerance
        optimal_paths = [
            (path, info) for path, info in path_dict.items()
            if abs(time_matrix.loc[curr_loc, wip_from[path[0]]] + info[1][1] - cost_s[s]) < 1e-5
        ]

        if not optimal_paths:
            raise ValueError(f"No optimal path found for set {s} matching cost {cost_s[s]}")

        # Select path with earliest first completion
        optimal_path, (arrival_order, arrival_times) = min(optimal_paths, key=lambda x: x[1][1][0])

        touch = {wip: 0 for wip in s}
        curr_time = 0

        for i, wip in enumerate(optimal_path):
            action = "PICKUP" if touch[wip] == 0 else "DELIVERY"
            target_loc = wip_from[wip] if action == "PICKUP" else wip_to[wip]

            travel_time = time_matrix.loc[curr_loc, target_loc]
            curr_time += travel_time

            rows.append([cart_id, i + 1, wip, action, curr_time])

            touch[wip] += 1
            curr_loc = target_loc

    return pd.DataFrame(rows, columns=["CART_ID", "ORDER", "WIP_ID", "ACTION", "COMPLETE_TIME"])

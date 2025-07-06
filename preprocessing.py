from itertools import permutations, combinations
from wip_utils import time_it


@time_it
def generate_combinations(wip_ids, wip_from, wip_to, time_matrix, cart_capacity=2):
    """
    Generate all feasible pickup-delivery path combinations for WIP pairs.

    Args:
        wip_ids (list): List of WIP IDs.
        wip_from (dict): Mapping {wip_id: from_location}.
        wip_to (dict): Mapping {wip_id: to_location}.
        time_matrix (DataFrame): Adjacency matrix DataFrame indexed and columned by locations.
        cart_capacity (int): Number of WIPs the cart can carry (currently assumed 2).

    Returns:
        dict: Nested result dictionary structured as:
            {
                (wip_1, wip_2): {
                    path_key: ((first_arrive_wip, second_arrive_wip), (first_arrive_time, second_arrive_time)),
                    ...
                },
                ...
            }
    """
    result_dict = {}

    # Generate all unique WIP pairs
    for wip_pair in combinations(wip_ids, cart_capacity):
        wip_1, wip_2 = wip_pair
        path_dict = {}

        # Build the 4 pickup/drop-off location points
        locs = [
            (wip_1, 'from', wip_from[wip_1]),
            (wip_1, 'to', wip_to[wip_1]),
            (wip_2, 'from', wip_from[wip_2]),
            (wip_2, 'to', wip_to[wip_2])
        ]

        # Generate all permutations of the 4 points
        for perm in permutations(locs):
            # Ensure 'from' precedes 'to' for each WIP
            seen_pickup = set()
            valid_order = True

            for wip_id, typ, _ in perm:
                if typ == 'from':
                    seen_pickup.add(wip_id)
                elif typ == 'to' and wip_id not in seen_pickup:
                    valid_order = False
                    break

            if not valid_order:
                continue

            # Calculate cumulative travel times along the permutation
            cum_times = [0]
            total_cost = 0

            for i in range(len(perm) - 1):
                loc_from = perm[i][2]
                loc_to = perm[i + 1][2]
                travel_time = time_matrix.loc[loc_from, loc_to]
                total_cost += travel_time
                cum_times.append(total_cost)

            # Extract arrival times at each WIP's drop-off location
            arrival_times = {
                wip_id: cum_times[idx]
                for idx, (wip_id, typ, _) in enumerate(perm)
                if typ == 'to'
            }

            # Determine arrival order
            sorted_arrivals = sorted(arrival_times.items(), key=lambda x: x[1])
            arrival_wips = tuple(wip for wip, _ in sorted_arrivals)
            arrival_time_values = tuple(time for _, time in sorted_arrivals)

            # Store this feasible path and arrival info
            path_key = tuple(wip_id for wip_id, _, _ in perm)
            path_dict[path_key] = (arrival_wips, arrival_time_values)

        result_dict[wip_pair] = path_dict

    return result_dict

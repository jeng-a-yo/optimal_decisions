import os
from preprocessing import generate_combinations
from wip_utils import load_data, build_output_from_selected_sets
from wip_even_model import build_set_covering_model


# === Constants ===
TIME_MATRIX_PATH = "time_matrix.csv"
CART_DATA_PATH = "cart_data.csv"
WIP_DATA_FOLDER = "wip_data"
OUTPUT_FOLDER = "output_results"

M = 100_000
H = 1
CART_CAPACITY = 2


def ensure_output_folder(path: str):
    os.makedirs(path, exist_ok=True)


def process_wip_file(wip_data_file: str):
    """
    Process a single WIP data file: load data, preprocess, build model, solve, and export results.
    """
    wip_data_path = os.path.join(WIP_DATA_FOLDER, wip_data_file)

    # Load data
    time_matrix, wip_ids, wip_from, wip_to, wip_qtime, cart_ids, cart_loc = load_data(
        TIME_MATRIX_PATH,
        CART_DATA_PATH,
        wip_data_path
    )

    # Preprocessing
    preprocess_result = generate_combinations(
        wip_ids, wip_from, wip_to, time_matrix, CART_CAPACITY
    )

    # Build and solve model
    model, y, cost_s, penalty_s = build_set_covering_model(
        preprocess_result=preprocess_result,
        wip_ids=wip_ids,
        wip_qtime=wip_qtime,
        time_matrix=time_matrix,
        wip_from=wip_from,
        cart_loc=cart_loc,
        cart_capacity=CART_CAPACITY,
        h=H,
        M=M
    )

    # Build output DataFrame
    initial_cart_loc = cart_loc[next(iter(cart_loc))]
    output_df = build_output_from_selected_sets(
        y,
        cost_s=cost_s,
        penalty_s=penalty_s,
        preprocess_result=preprocess_result,
        time_matrix=time_matrix,
        wip_from=wip_from,
        wip_to=wip_to,
        initial_cart_loc=initial_cart_loc
    )

    # Save output
    core_part = wip_data_file.replace("wip_data_", "").replace(".csv", "")
    output_path = os.path.join(OUTPUT_FOLDER, f"wip_{core_part}_even.csv")
    output_df.to_csv(output_path, index=False)

    print(f"Processed {wip_data_file} -> {output_path}")


def main():
    """
    Main workflow:
    - Ensure output folder exists
    - Iterate over WIP data files
    - Process each file
    """
    ensure_output_folder(OUTPUT_FOLDER)

    wip_files = sorted(os.listdir(WIP_DATA_FOLDER))
    for wip_file in wip_files:
        process_wip_file(wip_file)

    # === Best Model ===
    # Future implementation placeholder


if __name__ == "__main__":
    main()

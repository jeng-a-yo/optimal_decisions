import os
from pprint import pprint
from wip_utils import cal_obj_val


# === Constants ===
WIP_DATA_FOLDER = "wip_data"
OUTPUT_FOLDER = "output_results"


def ensure_folder_exists(path: str):
    """
    Ensure the specified folder exists.
    """
    os.makedirs(path, exist_ok=True)


def evaluate_wip_file(wip_data_file: str):
    """
    Evaluate a single WIP file by calculating its objective value.
    """
    wip_data_path = os.path.join(WIP_DATA_FOLDER, wip_data_file)

    # Determine output file path based on naming convention
    core_part = wip_data_file.replace("wip_data_", "").replace(".csv", "")
    output_file = f"wip_{core_part}_even.csv"
    output_path = os.path.join(OUTPUT_FOLDER, output_file)

    # Perform evaluation
    print(f"Evaluating: {wip_data_file}")
    obj_val = cal_obj_val(output_path, wip_data_path)

    # Print results
    pprint({
        "WIP Data Path": wip_data_path,
        "Output Path": output_path,
        "Objective Value": obj_val
    })
    print("=" * 70)


def main():
    """
    Main workflow to evaluate all WIP files in the data folder.
    """
    ensure_folder_exists(OUTPUT_FOLDER)

    wip_files = sorted(os.listdir(WIP_DATA_FOLDER))
    if not wip_files:
        print(f"No files found in '{WIP_DATA_FOLDER}'.")
        return

    for wip_file in wip_files:
        evaluate_wip_file(wip_file)



if __name__ == "__main__":
    main()

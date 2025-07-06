PRJ1: Optimal WIP Transport Scheduling

📌 Project Overview

This project aims to develop optimization models for Work In Progress (WIP) transport scheduling using multiple carts in a factory. Each WIP has:

- A remaining Q-time (deadline)
- An initial location (FROM)
- A destination location (TO)

The goal is to assign transport tasks to carts such that the total cost is minimized, where the total cost is defined as:

- Penalty for late delivery: M = 100000 per unit time delay
- Cart operating time cost: h = 1 per unit time

The penalty cost dominates, so satisfying deadlines is critical.

---

Repository Structure

optimal_decisions/
├── output_results/
│ ├── wip_10_1_even.csv
│ ├── wip_10_2_even.csv
│ └── wip_40_0_even.csv
│
├── sample_results/
│ ├── wip_10_1_best.csv
│ ├── wip_10_1_even.csv
│ ├── wip_10_2_best.csv
│ ├── wip_10_2_even.csv
│ ├── wip_40_0_best.csv
│ └── wip_40_0_even.csv
│
├── wip_data/
│ ├── wip_data_10_1.csv
│ ├── wip_data_10_2.csv
│ └── wip_data_40_0.csv
│
├── app.py
├── cart_data.csv
├── check_answer.py
├── get_time.py
├── preprocessing.py
├── prj1_description.pptx
├── README.md
├── time_matrix.csv
├── wip_best_model.py
├── wip_even_model.py
└── wip_utils.py

Key files:

- app.py: Main application runner.
- preprocessing.py: Data preprocessing and loading scripts.
- wip_even_model.py: Contains three candidate models for even distribution (basic case), where each cart transports exactly 2 WIPs.
- wip_best_model.py: Placeholder for the best (extension case) model, not yet developed.
- check_answer.py: Evaluates solutions for feasibility and calculates penalties.
- get_time.py: Utilities for runtime analysis.
- prj1_description.pptx: Problem specification and requirements.

---

✅ Current Progress

- Implemented three models in wip_even_model.py.
- The third model produces an objective value of 851 for the 40-WIP even test case, matching the reference solution.

⚠️ Known Issues

- Although the objective function value is correct, check_answer.py flags a penalty on WIP pair ("W11", "W37").
- This indicates potential bugs in constraint formulations or penalty calculations.
- Due to this uncertainty, the best model development is not started yet.

---

📝 Problem Description (Summary)

- Basic (even) case:  
  Each cart carries exactly 2 WIPs. Example: 40 WIPs and 20 carts → 2 WIPs per cart.

- Extension (best) case:  
  No strict distribution; carts may carry different numbers of WIPs (3, 4, 5, etc.), but at most 2 simultaneously loaded.

Inputs:

1. cart_data.csv: CART_ID, INIT_LOC
2. time_matrix.csv: FROM, TO, XFER_TIME for 50 locations
3. wip_data_XX_YY.csv: WIP_ID, Remaining Q-Time, FROM, TO

Outputs:

A CSV containing:

CART_ID | ORDER | WIP_ID | ACTION (PICKUP/DELIVERY) | COMPLETE_TIME

---

💡 Next Steps

1. Debug penalty calculation in wip_even_model.py third model to ensure feasibility.
2. Start best model development after confirming even model correctness.
3. Refactor and modularize code for clarity and scalability.

---

📖 Reference Objective Values

| Case     | Even Objective | Best Objective |
| -------- | -------------- | -------------- |
| wip_10_1 | 249            | 249            |
| wip_10_2 | 249            | 234            |
| wip_40_0 | 851            | 592            |

---

🔧 Usage

1. Run the main application:

python app.py

2. Check solution feasibility:

python check_answer.py

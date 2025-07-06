# PRJ1 Short Report: Optimal WIP Transport Scheduling

**Name:** 鄭丞佑

---

## 🔹 Problem Overview

This project develops optimization models for Work In Progress (WIP) transport scheduling using multiple carts in a factory. Each WIP has:

- A remaining Q-time (deadline)
- An initial location (FROM)
- A destination location (TO)

**Objective:** Minimize total cost defined as:

- **Penalty for late delivery:** M = 100000 per unit time delay
- **Cart operating time cost:** h = 1 per unit time

Meeting deadlines is critical due to the dominating penalty cost.

---

## 🔹 Parameter Definitions

**Sets**

$$
\begin{aligned}
& C : \text{ set of carts (index c)} \\
& W : \text{ set of WIPs (index w)} \\
& L : \text{ set of locations}
\end{aligned}
$$

**Parameters**

$$
\begin{aligned}
& q_w : \text{ remaining Q-time for WIP } w \\
& t_{i,j} : \text{ transfer time from location } i \text{ to } j \\
& from_w : \text{ initial location of WIP } w \\
& to_w : \text{ destination location of WIP } w \\
& init_c : \text{ initial location of cart } c \\
& M : \text{ penalty cost per unit time delay (100000)} \\
& h : \text{ cart operating time cost per unit time (1)}
\end{aligned}
$$

**Variables**

$$
\begin{aligned}
& x_{c,w} \in \{0,1\} : \text{ 1 if WIP } w \text{ assigned to cart } c, \text{ else 0} \\
& s_{c,w} \ge 0 : \text{ start time for WIP } w \text{ by cart } c \\
& d_{c,w} \ge 0 : \text{ delivery time for WIP } w \text{ by cart } c
\end{aligned}
$$

---

## 🔹 Model 1: Simple Sequential Assignment

**Objective**

Minimize total cost:

$$
\min \sum_{c \in C} \sum_{w \in W} \left[ h \times (d_{c,w} - s_{c,w}) + M \times \max(0, d_{c,w} - q_w) \right]
$$

**Constraints**

1. Each WIP is assigned to exactly one cart:

$$
\sum_{c \in C} x_{c,w} = 1, \quad \forall w \in W
$$

2. Each cart carries exactly two WIPs:

$$
\sum_{w \in W} x_{c,w} = 2, \quad \forall c \in C
$$

3. Service time calculated sequentially without routing optimization.

---

## 🔹 Model 2: Improved Time-Indexed Assignment

**Objective**

Same as Model 1.

**Key Improvements**

- Uses time matrix routes explicitly for service time calculations.
- Defines pickup and delivery order within each cart.

**Additional Constraints**

1. Ordering constraints:

$$
s_{c,w_2} \ge d_{c,w_1} + t_{to_{w_1}, from_{w_2}}, \quad \text{if } w_1 \text{ before } w_2
$$

2. Delivery time:

$$
d_{c,w} = s_{c,w} + t_{from_w, to_w}
$$

3. Start time includes cart’s initial travel time:

$$
s_{c,w_1} \ge t_{init_c, from_{w_1}}
$$

---

## 🔹 Model 3: Feasibility-Driven Sequential Optimization

**Objective**

Same as Models 1 and 2.

**Key Characteristics**

- Optimized routing within each cart to minimize total travel time.
- Hard constraints to guarantee feasibility (no deadline violation).

**Additional Constraints**

1. No lateness (hard) constraint:

$$
d_{c,w} \le q_w, \quad \forall c, w
$$

2. Full sequential route time calculation including cart initial travel, pickup-to-delivery time, and inter-WIP transfer if two WIPs are assigned.

---

## 🔹 Short Discussion

Model 3 produces the correct objective (851 for the 40-WIP even case) but `check_answer.py` flagged a penalty for WIP pair (W11, W37). This suggests potential bugs in formulation or penalty calculation logic.

**Key Learning Points**

- Accurate sequencing and time calculations are critical in transport scheduling.
- Hard feasibility constraints simplify deadline satisfaction but may restrict solution flexibility.
- Even when the objective value matches the reference, feasibility violations can occur due to:
  - Incorrect deadline constraint implementation.
  - Missing constraints to enforce WIP delivery order consistency.
  - Errors in time matrix usage for pickup-to-delivery or inter-WIP routing.
- The penalty function is extremely sensitive because of the large penalty coefficient (M=100000). Small formulation or implementation errors will dominate the objective value and result in infeasible solutions despite optimal-looking costs.

**Debugging Insights**

- The flagged penalty for W11 and W37 indicates that at least one WIP in this pair is delivered later than its Q-time.
- Possible causes include:
  - Miscalculating the start time of the second WIP on a cart.
  - Missing transfer time between the delivery of the first WIP and the pickup of the second WIP.
  - Incorrect initialization of cart starting locations in the model.
- Stepwise debugging approach:
  1. Verify time calculations for both WIPs assigned to each cart.
  2. Print intermediate decision variable values (start time, delivery time) to cross-check feasibility.
  3. Compare modeled sequence logic with time matrix data for consistency.

**Practical Implications**

- This problem reflects real factory transport scheduling where feasibility (meeting deadlines) is more important than minimizing operating costs.
- Strict constraints ensure that production flows are not interrupted by late deliveries, which can cause line downtime and heavy penalties in manufacturing contracts.

**Next Steps**

1. Debug penalty calculation and constraint formulation in Model 3 to ensure all delivery deadlines are respected.
2. Extend the model to the best (extension) case, allowing variable WIP assignments per cart, after confirming the even case correctness.
3. Modularize code for clarity and maintainability to support scalable testing on larger WIP datasets in future projects.

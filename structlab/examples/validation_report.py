"""Print solver results next to the closed-form (hand-calculation) answers.

    python examples/validation_report.py
"""
from structlab.solver import member_diagram, solve
from structlab.templates import textbook as T

rows = []


def check(case, quantity, computed, exact, unit=""):
    err = abs(computed - exact) / abs(exact) * 100 if exact else abs(computed)
    rows.append((case, quantity, computed, exact, err, unit))


# 1. triangle truss
m, e = T.triangle_truss(); r = solve(m)
for mid, F in e["F"].items():
    check("Triangle truss", f"member {mid} force", r.members[mid].axial, F, "N")
check("Triangle truss", "reaction R_A", r.reaction(1)[1], e["R_A"][1], "N")
check("Triangle truss", "apex deflection", r.displacement(3)[1], e["uy_C"], "m")

# 2. axial bar
m, e = T.axial_bar(); r = solve(m)
check("Axial bar", "delta = PL/AE", r.displacement(2)[0], e["delta"], "m")

# 3. cantilever
m, e = T.cantilever_beam(1); r = solve(m)
check("Cantilever", "tip deflection PL^3/3EI", r.displacement(e["tip_node"])[1], e["tip_deflection"], "m")
check("Cantilever", "fixed-end moment PL", r.reaction(e["root_node"])[2], e["M_fixed"], "N*m")

# 4. simply supported beam, UDL (single element, diagram is exact)
m, e = T.simply_supported_beam(1); r = solve(m)
d = member_diagram(r.members[1], 601)
check("SS beam UDL", "max moment wL^2/8", d.M.max(), e["M_max"], "N*m")
check("SS beam UDL", "max deflection 5wL^4/384EI", d.v.min(), e["delta_max"], "m")

# 5. propped cantilever (indeterminate)
m, e = T.propped_cantilever(2); r = solve(m)
check("Propped cantilever", "prop reaction 3wL/8", r.reaction(e["prop_node"])[1], e["R_prop"], "N")
check("Propped cantilever", "fixed moment wL^2/8", r.reaction(e["fixed_node"])[2], e["M_fixed"], "N*m")

print(f"{'case':<20}{'quantity':<30}{'solver':>14}{'hand calc':>14}{'error %':>11}")
for case, q, c, x, err, u in rows:
    print(f"{case:<20}{q:<30}{c:>14.6g}{x:>14.6g}{err:>11.2e}  {u}")

"""Recover member forces, stresses and diagrams from the solved displacements."""
from __future__ import annotations

import math

import numpy as np

from ..materials.library import MaterialLibrary
from .assembly import MemberData
from .elements import beam2d, truss
from .results import MemberDiagram, MemberResult

N_STRESS_SAMPLES = 41


def recover_member(md: MemberData, u_global: np.ndarray, library: MaterialLibrary,
                   warnings: list[str]) -> MemberResult:
    """Member end forces, stresses and status from the global displacement vector."""
    u_g = u_global[md.dofs]
    if md.is_frame:
        T = beam2d.transformation(md.c, md.s)
        k_loc = beam2d.local_stiffness(md.E, md.A, md.Iz, md.L)
        u_loc = T @ u_g
        # Forces the NODES exert on the element:  f = k u - f_eq   (element equilibrium)
        f = k_loc @ u_loc - md.f_eq_local
        N_i, V_i, M_i = -f[0], f[1], -f[2]       # internal-force sign convention (see results.py)
        N_j, V_j, M_j = f[3], -f[4], f[5]
        u6 = tuple(float(x) for x in u_loc)
    else:
        T = truss.transformation(md.c, md.s)
        k_loc = truss.local_stiffness(md.E, md.A, md.L)
        u4 = T @ u_g
        f = k_loc @ u4 - md.f_eq_local
        N_i, N_j = -f[0], f[2]
        V_i = V_j = M_i = M_j = 0.0
        u6 = (float(u4[0]), float(u4[1]), 0.0, float(u4[2]), float(u4[3]), 0.0)

    elongation = u6[3] - u6[0]
    mat = library.get(md.material)
    res = MemberResult(
        id=md.id, kind=md.kind, node_i=md.node_i, node_j=md.node_j, length=md.L,
        N_i=float(N_i), N_j=float(N_j), V_i=float(V_i), V_j=float(V_j),
        M_i=float(M_i), M_j=float(M_j),
        axial_stress=0.0, max_tension_stress=0.0, max_compression_stress=0.0,
        strain=elongation / md.L, elongation=elongation, fos=math.inf, state="zero", status="OK",
        material=md.material, u_local=u6, loads_local=tuple(md.w_local), E=md.E, A=md.A, Iz=md.Iz)

    # ---- stresses: sigma = N/A +- M c / I  (flexure formula, Beer & Johnston eq. 4.15) ----
    sigma_t, sigma_c = 0.0, 0.0
    if md.is_frame:
        d = member_diagram(res, N_STRESS_SAMPLES)
        sig_axial = d.N / md.A
        if math.isnan(md.c_y):
            warnings.append(f"Member {md.id}: section has no c_y, so bending stress was not computed.")
            bend = np.zeros_like(d.M)
        else:
            bend = np.abs(d.M) * md.c_y / md.Iz
        sigma_t = max(0.0, float(np.max(sig_axial + bend)))
        sigma_c = min(0.0, float(np.min(sig_axial - bend)))
    else:
        s = res.axial / md.A
        sigma_t, sigma_c = max(0.0, s), min(0.0, s)
    res.axial_stress = res.axial / md.A
    res.max_tension_stress, res.max_compression_stress = sigma_t, sigma_c

    scale = max(abs(sigma_t), abs(sigma_c), 1e-6 * mat.yield_strength)
    if abs(res.axial) < 1e-9 * max(1.0, md.E * md.A) and not md.is_frame:
        res.state = "zero"
    elif res.axial > 0:
        res.state = "tension"
    elif res.axial < 0:
        res.state = "compression"

    allow_t = mat.yield_strength
    allow_c = mat.compressive_strength or mat.yield_strength
    ratios = []
    if mat.compression_only and sigma_t > 1e-6 * mat.yield_strength:
        res.status = "tension in compression-only material"
        res.fos = 0.0
    else:
        if sigma_t > 0 and not mat.compression_only:
            ratios.append(allow_t / sigma_t)
        if sigma_c < 0:
            ratios.append(allow_c / -sigma_c)
        res.fos = min(ratios) if ratios else math.inf
        res.status = "yields" if res.fos < 1.0 else "OK"
    return res


def member_diagram(r: MemberResult, n: int = 51) -> MemberDiagram:
    """Exact N(x), V(x), M(x), rotation and deflection along a member (local axes).

    Starting from the known end-i values and integrating the load, which varies
    linearly:  w(x) = w1 + a x   with  a = (w2 - w1)/L  (local y load wy, local x load wx).

        dN/dx = -wx          N(x) = N_i - (wx1 x + ax x^2/2)
        dV/dx =  wy          V(x) = V_i + wy1 x + ay x^2/2
        dM/dx =  V           M(x) = M_i + V_i x + wy1 x^2/2 + ay x^3/6
        EI v'' = M           theta, v by integrating twice from the end-i displacements

    (sagging-positive M with y up gives v'' = +M/EI).  This is exact for the
    Euler-Bernoulli theory, independent of how many elements the member has.
    """
    L = r.length
    x = np.linspace(0.0, L, n)
    wx1, wx2, wy1, wy2 = r.loads_local
    ax = (wx2 - wx1) / L
    ay = (wy2 - wy1) / L
    N = r.N_i - (wx1 * x + ax * x**2 / 2)
    if r.kind != "frame":
        z = np.zeros_like(x)
        return MemberDiagram(x, np.full_like(x, r.axial), z, z, z, z)
    V = r.V_i + wy1 * x + ay * x**2 / 2
    M = r.M_i + r.V_i * x + wy1 * x**2 / 2 + ay * x**3 / 6
    EI = r.E * r.Iz
    u_i, v_i, th_i = r.u_local[0], r.u_local[1], r.u_local[2]
    theta = th_i + (r.M_i * x + r.V_i * x**2 / 2 + wy1 * x**3 / 6 + ay * x**4 / 24) / EI
    v = v_i + th_i * x + (r.M_i * x**2 / 2 + r.V_i * x**3 / 6 + wy1 * x**4 / 24 + ay * x**5 / 120) / EI
    return MemberDiagram(x, N, V, M, theta, v)

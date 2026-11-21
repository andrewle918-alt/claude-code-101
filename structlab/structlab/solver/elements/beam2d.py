"""2D Euler-Bernoulli frame element (axial + bending), 3 DOFs per node.

Element DOFs (local axes):  [u_i, v_i, theta_i, u_j, v_j, theta_j]
    u = along the member, v = transverse (local +y), theta = CCW rotation.
"""
from __future__ import annotations

import numpy as np


def local_stiffness(E: float, A: float, I: float, L: float) -> np.ndarray:
    """Standard 6x6 beam-column stiffness (Przemieniecki; Logan eq. 5.3.x).

        axial :  EA/L
        bending: 12EI/L^3, 6EI/L^2, 4EI/L, 2EI/L   (cubic Hermite shape functions)
    """
    a = E * A / L
    b12 = 12 * E * I / L**3
    b6 = 6 * E * I / L**2
    b4 = 4 * E * I / L
    b2 = 2 * E * I / L
    return np.array([
        [a,    0,    0,   -a,    0,    0],
        [0,  b12,   b6,    0, -b12,   b6],
        [0,   b6,   b4,    0,  -b6,   b2],
        [-a,   0,    0,    a,    0,    0],
        [0, -b12,  -b6,    0,  b12,  -b6],
        [0,   b6,   b2,    0,  -b6,   b4],
    ], dtype=float)


def transformation(c: float, s: float) -> np.ndarray:
    """6x6 rotation matrix with  u_local = T @ u_global  (rotation DOF unchanged)."""
    R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], dtype=float)
    T = np.zeros((6, 6))
    T[:3, :3] = R
    T[3:, 3:] = R
    return T


def equivalent_load_local(L: float, wx1: float, wx2: float, wy1: float, wy2: float) -> np.ndarray:
    """Consistent (equivalent) nodal loads for a linearly varying distributed load.

    Loads are in the member's LOCAL axes, intensity going from w1 at node i to
    w2 at node j.  They are the loads that, applied at the nodes, produce the
    same work as the distributed load (Logan sect. 4.7 / Cook table):

        transverse:  F_i = L (7 w1 + 3 w2)/20      M_i =  L^2 (3 w1 + 2 w2)/60
                     F_j = L (3 w1 + 7 w2)/20      M_j = -L^2 (2 w1 + 3 w2)/60
        axial:       P_i = L (2 b1 + b2)/6         P_j = L (b1 + 2 b2)/6

    Check for a uniform load (w1 = w2 = w):  F = wL/2,  M = +-wL^2/12.
    """
    return np.array([
        L * (2 * wx1 + wx2) / 6.0,
        L * (7 * wy1 + 3 * wy2) / 20.0,
        L**2 * (3 * wy1 + 2 * wy2) / 60.0,
        L * (wx1 + 2 * wx2) / 6.0,
        L * (3 * wy1 + 7 * wy2) / 20.0,
        -(L**2) * (2 * wy1 + 3 * wy2) / 60.0,
    ], dtype=float)


def thermal_load_local(E: float, A: float, alpha: float, delta_t: float) -> np.ndarray:
    """Uniform temperature change: only the axial DOFs see a load, f = E A alpha dT [-1,0,0,1,0,0]."""
    f = E * A * alpha * delta_t
    return np.array([-f, 0.0, 0.0, f, 0.0, 0.0])

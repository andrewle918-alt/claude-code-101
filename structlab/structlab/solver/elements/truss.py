"""2D pin-jointed bar (truss) element.

Element DOFs (local axes):  [u_i, v_i, u_j, v_j]   (u along the bar, v across it)
Element DOFs (global axes): [ux_i, uy_i, ux_j, uy_j]
"""
from __future__ import annotations

import numpy as np


def local_stiffness(E: float, A: float, L: float) -> np.ndarray:
    """Axial bar stiffness in local axes:  k = (EA/L) [[1,-1],[-1,1]]  (Hibbeler / Logan eq. 3.1.x).

    Written as 4x4 so it uses the same (x, y) DOFs per node as the global system;
    the transverse (v) rows are zero because a pin-jointed bar has no shear stiffness.
    """
    k = E * A / L
    return np.array([[k, 0, -k, 0],
                     [0, 0, 0, 0],
                     [-k, 0, k, 0],
                     [0, 0, 0, 0]], dtype=float)


def transformation(c: float, s: float) -> np.ndarray:
    """Rotation matrix T with  u_local = T @ u_global,  c = cos(theta), s = sin(theta)."""
    return np.array([[c, s, 0, 0],
                     [-s, c, 0, 0],
                     [0, 0, c, s],
                     [0, 0, -s, c]], dtype=float)


def lumped_load_local(L: float, wx1: float, wx2: float, wy1: float, wy2: float) -> np.ndarray:
    """Distributed load (linear, i -> j) on a bar, lumped to the two nodes.

    A bar cannot bend, so the load is carried to the end nodes exactly as a
    simply supported strip would:  P_i = (2 w1 + w2) L / 6,  P_j = (w1 + 2 w2) L / 6.
    This preserves both the force and moment resultants of the load.
    """
    fi = lambda a, b: (2 * a + b) * L / 6.0
    fj = lambda a, b: (a + 2 * b) * L / 6.0
    return np.array([fi(wx1, wx2), fi(wy1, wy2), fj(wx1, wx2), fj(wy1, wy2)], dtype=float)


def thermal_load_local(E: float, A: float, alpha: float, delta_t: float) -> np.ndarray:
    """Equivalent nodal load of a uniform temperature change (fully restrained bar).

    Thermal strain eps0 = alpha * dT, restrained force = E A eps0 pushing both ends outward:
    f = E A alpha dT [-1, 0, +1, 0].
    """
    f = E * A * alpha * delta_t
    return np.array([-f, 0.0, f, 0.0])

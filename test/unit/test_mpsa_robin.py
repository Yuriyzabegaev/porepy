import numpy as np
import scipy.sparse as sps
import unittest

import porepy as pp

class RobinBoundTest(unittest.TestCase):
    def test_dir_rob(self):
        nx = 2
        ny = 2
        g = pp.CartGrid([nx, ny], physdims=[1, 1])
        g.compute_geometry()
        c = pp.FourthOrderTensor(2, np.ones(g.num_cells), np.ones(g.num_cells))
        alpha = np.pi

        bot = g.face_centers[1] < 1e-10
        top = g.face_centers[1] > 1 - 1e-10
        left = g.face_centers[0] < 1e-10
        right = g.face_centers[0] > 1 - 1e-10

        dir_ind = np.ravel(np.argwhere(left + bot + top))
        neu_ind = np.ravel(np.argwhere([]))
        rob_ind = np.ravel(np.argwhere(right))

        names = ['dir']*len(dir_ind) + ['rob'] * len(rob_ind)
        bnd_ind = np.hstack((dir_ind, rob_ind))
        bnd = pp.BoundaryCondition(g, bnd_ind, names)

        def u_ex(x):
            return np.vstack((x[0], 0 * x[1]))

        def T_ex(faces):
            if np.size(faces) == 0:
                return np.atleast_2d(np.array([]))
            sigma = np.array([[3, 0], [0, 1]])
            T_r = [np.dot(sigma, g.face_normals[:2, f]) for f in faces]
            return np.vstack(T_r).T

        u_bound = np.zeros((2, g.num_faces))

        sgn_n = pp.numerics.fracture_deformation.sign_of_faces(g, neu_ind)
        sgn_r = pp.numerics.fracture_deformation.sign_of_faces(g, rob_ind)
        
        u_bound[:, dir_ind] = u_ex(g.face_centers[:, dir_ind])
        u_bound[:, neu_ind] = T_ex(neu_ind) * sgn_n
        u_bound[:, rob_ind] = (
        T_ex(rob_ind) * sgn_r
        + alpha * u_ex(g.face_centers[:, rob_ind]) * g.face_areas[rob_ind]
        )
        u, T = self.solve_mpsa(g, c, alpha, bnd, u_bound)

        assert np.allclose(u, u_ex(g.cell_centers).ravel('F'))
        assert np.allclose(T, T_ex(np.arange(g.num_faces)).ravel('F'))

    def test_dir_neu_rob(self):
        nx = 2
        ny = 3
        g = pp.CartGrid([nx, ny], physdims=[1, 1])
        g.compute_geometry()
        c = pp.FourthOrderTensor(2, np.ones(g.num_cells), np.ones(g.num_cells))
        alpha = np.pi

        bot = g.face_centers[1] < 1e-10
        top = g.face_centers[1] > 1 - 1e-10
        left = g.face_centers[0] < 1e-10
        right = g.face_centers[0] > 1 - 1e-10

        dir_ind = np.ravel(np.argwhere(left))
        neu_ind = np.ravel(np.argwhere(top))
        rob_ind = np.ravel(np.argwhere(right + bot))

        names = ['dir']*len(dir_ind) + ['rob'] * len(rob_ind)
        bnd_ind = np.hstack((dir_ind, rob_ind))
        bnd = pp.BoundaryCondition(g, bnd_ind, names)

        def u_ex(x):
            return np.vstack((x[0], 0 * x[1]))

        def T_ex(faces):
            if np.size(faces) == 0:
                return np.atleast_2d(np.array([]))
            sigma = np.array([[3, 0], [0, 1]])
            T_r = [np.dot(sigma, g.face_normals[:2, f]) for f in faces]
            return np.vstack(T_r).T

        u_bound = np.zeros((2, g.num_faces))

        sgn_n = pp.numerics.fracture_deformation.sign_of_faces(g, neu_ind)
        sgn_r = pp.numerics.fracture_deformation.sign_of_faces(g, rob_ind)
        
        u_bound[:, dir_ind] = u_ex(g.face_centers[:, dir_ind])
        u_bound[:, neu_ind] = T_ex(neu_ind) * sgn_n
        u_bound[:, rob_ind] = (
        T_ex(rob_ind) * sgn_r
        + alpha * u_ex(g.face_centers[:, rob_ind]) * g.face_areas[rob_ind]
        )
        u, T = self.solve_mpsa(g, c, alpha, bnd, u_bound)

        assert np.allclose(u, u_ex(g.cell_centers).ravel('F'))
        assert np.allclose(T, T_ex(np.arange(g.num_faces)).ravel('F'))

    def solve_mpsa(self, g, c, alpha, bnd, u_bound):
        stress, bound_stress = pp.numerics.fv.mpsa._mpsa_local(g, c, bnd, alpha=alpha)
        div = pp.fvutils.vector_divergence(g)
        a = div * stress
        b = -div * bound_stress * u_bound.ravel('F')

        u = np.linalg.solve(a.A, b)
        T = stress * u + bound_stress * u_bound.ravel('F')
        return u, T

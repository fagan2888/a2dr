import numpy as np
from cvxpy import *
from a2dr.proximal import *
from a2dr.tests.base_test import BaseTest

class TestProximal(BaseTest):

    def setUp(self):
        np.random.seed(1)
        self.TOLERANCE = 1e-6
        self.t = 5*np.abs(np.random.randn()) + self.TOLERANCE
        self.c = np.random.randn()
        self.v = np.random.randn(100)
        self.v_small = np.random.randn(10)

        self.B = np.random.randn(50,10)
        self.B_small = np.random.randn(10,5)
        self.B_square = np.random.randn(10,10)

        self.B_symm = np.random.randn(10,10)
        self.B_symm = (self.B_symm + self.B_symm.T) / 2.0
        self.B_psd = np.random.randn(10,10)
        self.B_psd = self.B_psd.T.dot(self.B_psd)

    def prox_cvxpy(self, v, fun, constr_fun = None, t = 1, scale = 1, offset = 0, lin_term = 0, quad_term = 0, *args, **kwargs):
        x_var = Variable() if np.isscalar(v) else Variable(v.shape)
        expr = t * fun(scale * x_var - offset) + sum(multiply(lin_term, x_var)) + quad_term * sum_squares(x_var)
        constrs = [] if constr_fun is None else constr_fun(scale * x_var - offset)
        Problem(Minimize(expr + 0.5 * sum_squares(x_var - v)), constrs).solve(*args, **kwargs)
        return x_var.value

    def check_composition(self, prox, fun, v_init, places = 4, *args, **kwargs):
        x_a2dr = prox(v_init)
        x_cvxpy = self.prox_cvxpy(v_init, fun, *args, **kwargs)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = places)

        x_a2dr = prox(v_init, t = self.t)
        x_cvxpy = self.prox_cvxpy(v_init, fun, t = self.t, *args, **kwargs)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = places)

        x_a2dr = prox(v_init, scale = -1)
        x_cvxpy = self.prox_cvxpy(v_init, fun, scale = -1, *args, **kwargs)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = places)

        x_a2dr = prox(v_init, scale = 2, offset = 0.5)
        x_cvxpy = self.prox_cvxpy(v_init, fun, scale = 2, offset = 0.5, *args, **kwargs)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = places)

        x_a2dr = prox(v_init, t = self.t, scale = 2, offset = 0.5, lin_term = 1.5, quad_term = 2.5)
        x_cvxpy = self.prox_cvxpy(v_init, fun, t = self.t, scale = 2, offset = 0.5, lin_term = 1.5, quad_term = 2.5,
                                  *args, **kwargs)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = places)

        if np.isscalar(v_init):
            offset = np.random.randn()
            lin_term = np.random.randn()
        else:
            offset = np.random.randn(*v_init.shape)
            lin_term = np.random.randn(*v_init.shape)
        x_a2dr = prox(v_init, t = self.t, scale = 0.5, offset = offset, lin_term = lin_term, quad_term = 2.5)
        x_cvxpy = self.prox_cvxpy(v_init, fun, t = self.t, scale = 0.5, offset = offset, lin_term = lin_term,
                                  quad_term = 2.5, *args, **kwargs)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = places)

    def check_elementwise(self, prox, places = 4):
        # Vector input.
        x_vec1 = prox(self.v_small)
        x_vec2 = np.array([prox(self.v_small[i]) for i in range(self.v_small.shape[0])])
        self.assertItemsAlmostEqual(x_vec1, x_vec2, places = places)

        x_vec1 = prox(self.v_small, t = self.t)
        x_vec2 = np.array([prox(self.v_small[i], t = self.t) for i in range(self.v_small.shape[0])])
        self.assertItemsAlmostEqual(x_vec1, x_vec2, places = places)

        offset = np.random.randn(*self.v_small.shape)
        lin_term = np.random.randn(*self.v_small.shape)
        x_vec1 = prox(self.v_small, t = self.t, scale = 0.5, offset = offset, lin_term = lin_term, quad_term = 2.5)
        x_vec2 = np.array([prox(self.v_small[i], t = self.t, scale = 0.5, offset = offset[i], lin_term = lin_term[i], \
                                quad_term = 2.5) for i in range(self.v_small.shape[0])])
        self.assertItemsAlmostEqual(x_vec1, x_vec2, places = places)

        # Matrix input.
        x_mat1 = prox(self.B_small)
        x_mat2 = [[prox(self.B_small[i,j]) for j in range(self.B_small.shape[1])] for i in range(self.B_small.shape[0])]
        x_mat2 = np.array(x_mat2)
        self.assertItemsAlmostEqual(x_mat1, x_mat2, places = places)

        x_mat1 = prox(self.B_small, t = self.t)
        x_mat2 = [[prox(self.B_small[i,j], t = self.t) for j in range(self.B_small.shape[1])] \
                    for i in range(self.B_small.shape[0])]
        x_mat2 = np.array(x_mat2)
        self.assertItemsAlmostEqual(x_mat1, x_mat2, places = places)

        offset = np.random.randn(*self.B_small.shape)
        lin_term = np.random.randn(*self.B_small.shape)
        x_mat1 = prox(self.B_small, t = self.t, scale = 0.5, offset = offset, lin_term = lin_term, quad_term = 2.5)
        x_mat2 = [[prox(self.B_small[i,j], t = self.t, scale = 0.5, offset = offset[i,j], lin_term = lin_term[i,j], \
                        quad_term = 2.5) for j in range(self.B_small.shape[1])] for i in range(self.B_small.shape[0])]
        x_mat2 = np.array(x_mat2)
        self.assertItemsAlmostEqual(x_mat1, x_mat2, places = places)

    def test_box_constr(self):
        # Projection onto a random interval.
        lo = np.random.randn()
        hi = lo + 5*np.abs(np.random.randn())

        x_a2dr = prox_box_constr(self.v, self.t, v_lo = lo, v_hi = hi)
        self.assertTrue(np.all(lo - self.TOLERANCE <= x_a2dr) and np.all(x_a2dr <= hi + self.TOLERANCE))

        # Projection onto a random interval with affine composition.
        scale = 2 * np.abs(np.random.randn()) + self.TOLERANCE
        if np.random.rand() < 0.5:
            scale = -scale
        offset = np.random.randn(*self.v.shape)
        lin_term = np.random.randn(*self.v.shape)
        quad_term = np.abs(np.random.randn())
        x_a2dr = prox_box_constr(self.v, self.t, v_lo = lo, v_hi = hi, scale = scale, offset = offset, \
                                    lin_term = lin_term, quad_term = quad_term)
        x_scaled = scale*x_a2dr - offset
        self.assertTrue(np.all(lo - self.TOLERANCE <= x_scaled) and np.all(x_scaled <= hi + self.TOLERANCE))

        # Common box intervals.
        bounds = [(0, 0), (-1, 1), (0, np.inf), (-np.inf, 0)]
        for bound in bounds:
            lo, hi = bound
            self.check_composition(lambda v, *args, **kwargs: prox_box_constr(v, v_lo = lo, v_hi = hi, *args, **kwargs),
                                   lambda x: 0, self.v, constr_fun = lambda x: [lo <= x, x <= hi])
            self.check_composition(lambda v, *args, **kwargs: prox_box_constr(v, v_lo = lo, v_hi = hi, *args, **kwargs),
                                   lambda x: 0, self.B, constr_fun = lambda x: [lo <= x, x <= hi])

    def test_nonneg_constr(self):
        x_a2dr = prox_nonneg_constr(self.v, self.t)
        self.assertTrue(np.all(x_a2dr >= -self.TOLERANCE))

        x_a2dr = prox_nonneg_constr(self.v, self.t, scale = -2, offset = 0)
        self.assertTrue(np.all(-2*x_a2dr >= -self.TOLERANCE))

        scale = 2*np.abs(np.random.randn()) + self.TOLERANCE
        if np.random.rand() < 0.5:
            scale = -scale
        offset = np.random.randn(*self.v.shape)
        lin_term = np.random.randn(*self.v.shape)
        quad_term = np.abs(np.random.randn())

        x_a2dr = prox_nonneg_constr(self.v, self.t, scale = scale, offset = offset, lin_term = lin_term, \
                                    quad_term = quad_term)
        self.assertTrue(np.all(scale*x_a2dr - offset) >= -self.TOLERANCE)

        self.check_composition(prox_nonneg_constr, lambda x: 0, self.v, constr_fun = lambda x: [x >= 0])
        self.check_composition(prox_nonneg_constr, lambda x: 0, self.B, constr_fun = lambda x: [x >= 0], places = 3)

    def test_nonpos_constr(self):
        x_a2dr = prox_nonpos_constr(self.v, self.t)
        self.assertTrue(np.all(x_a2dr <= self.TOLERANCE))

        x_a2dr = prox_nonpos_constr(self.v, self.t, scale=-2, offset=0)
        self.assertTrue(np.all(-2*x_a2dr <= self.TOLERANCE))

        scale = 2 * np.abs(np.random.randn()) + self.TOLERANCE
        if np.random.rand() < 0.5:
            scale = -scale
        offset = np.random.randn(*self.v.shape)
        lin_term = np.random.randn(*self.v.shape)
        quad_term = np.abs(np.random.randn())

        x_a2dr = prox_nonpos_constr(self.v, self.t, scale=scale, offset=offset, lin_term=lin_term, \
                                    quad_term=quad_term)
        self.assertTrue(np.all(scale * x_a2dr - offset) <= self.TOLERANCE)

        self.check_composition(prox_nonpos_constr, lambda x: 0, self.v, constr_fun=lambda x: [x <= 0])
        self.check_composition(prox_nonpos_constr, lambda x: 0, self.B, constr_fun=lambda x: [x <= 0], places = 3)

    def test_psd_cone(self):
        # Projection onto the PSD cone.
        B_a2dr = prox_psd_cone(self.B_symm, self.t)
        self.assertTrue(np.all(np.linalg.eigvals(B_a2dr) >= -self.TOLERANCE))

        # Projection onto the PSD cone with affine composition.
        scale = 2 * np.abs(np.random.randn()) + self.TOLERANCE
        if np.random.rand() < 0.5:
            scale = -scale
        offset = np.random.randn(*self.B_symm.shape)
        lin_term = np.random.randn(*self.B_symm.shape)
        quad_term = np.abs(np.random.randn())
        B_a2dr = prox_psd_cone(self.B_symm, self.t, scale = scale, offset = offset, lin_term = lin_term, \
                                  quad_term = quad_term)
        B_scaled = scale*B_a2dr - offset
        self.assertTrue(np.all(np.linalg.eigvals(B_scaled) >= -self.TOLERANCE))

        # Simple composition.
        B_a2dr = prox_psd_cone(self.B_symm, t = self.t, scale = 2, offset = 0.5, lin_term = 1.5, quad_term = 2.5)
        B_cvxpy = self.prox_cvxpy(self.B_symm, lambda X: 0, constr_fun = lambda X: [X >> 0], t = self.t, scale = 2, \
                                  offset = 0.5, lin_term = 1.5, quad_term = 2.5)
        self.assertItemsAlmostEqual(B_a2dr, B_cvxpy)

    def test_soc(self):
        # Projection onto the SOC.
        x_a2dr = prox_soc(self.v, self.t)
        self.assertTrue(np.linalg.norm(x_a2dr[:-1],2) <= x_a2dr[-1] + self.TOLERANCE)

        # Projection onto the SOC with affine composition.
        x_a2dr = prox_soc(self.v, self.t, scale=2, offset=0.5)
        x_scaled = 2*x_a2dr - 0.5
        self.assertTrue(np.linalg.norm(x_scaled[:-1],2) <= x_scaled[-1] + self.TOLERANCE)

        scale = 2 * np.abs(np.random.randn()) + self.TOLERANCE
        if np.random.rand() < 0.5:
            scale = -scale
        offset = np.random.randn(*self.v.shape)
        lin_term = np.random.randn(*self.v.shape)
        quad_term = np.abs(np.random.randn())

        x_a2dr = prox_soc(self.v, self.t, scale=scale, offset=offset, lin_term=lin_term, quad_term=quad_term)
        x_scaled = scale*x_a2dr - offset
        self.assertTrue(np.linalg.norm(x_scaled[:-1], 2) <= x_scaled[-1] + self.TOLERANCE)

        self.check_composition(prox_soc, lambda x: 0, self.v, constr_fun = lambda x: [SOC(x[-1], x[:-1])], \
                               places = 3, solver = "SCS")

    def test_abs(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_abs, places = 4)

        # General composition tests.
        self.check_composition(prox_abs, cvxpy.abs, self.c, places=4)
        self.check_composition(prox_abs, lambda x: sum(abs(x)), self.v, places=4)
        self.check_composition(prox_abs, lambda x: sum(abs(x)), self.B, places=3)

    def test_constant(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_constant, places = 4)

        # General composition tests.
        self.check_composition(prox_constant, lambda x: 0, self.c, places = 4)
        self.check_composition(prox_constant, lambda x: 0, self.v, places = 4)
        self.check_composition(prox_constant, lambda x: 0, self.B, places = 4)

    def test_exp(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_exp, places = 4)

        # General composition tests.
        self.check_composition(prox_exp, cvxpy.exp, self.c, places=4)
        self.check_composition(prox_exp, lambda x: sum(exp(x)), self.v, places=4)
        self.check_composition(prox_exp, lambda x: sum(exp(x)), self.B, places=3)

    def test_huber(self):
        for M in [0, 0.5, 1, 2]:
            # Elementwise consistency tests.
            self.check_elementwise(lambda v, *args, **kwargs: prox_huber(v, *args, **kwargs, M = M), places = 4)

            # Scalar input.
            self.check_composition(lambda v, *args, **kwargs: prox_huber(v, M = M, *args, **kwargs),
                                   lambda x: huber(x, M = M), self.c, places = 4)
            # Vector input.
            self.check_composition(lambda v, *args, **kwargs: prox_huber(v, M = M, *args, **kwargs),
                                   lambda x: sum(huber(x, M = M)), self.v, places = 4)
            # Matrix input.
            self.check_composition(lambda v, *args, **kwargs: prox_huber(v, M = M, *args, **kwargs),
                                   lambda x: sum(huber(x, M = M)), self.B, places = 4)

    def test_identity(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_identity, places = 4)

        # General composition tests.
        self.check_composition(prox_identity, lambda x: x, self.c, places = 4)
        self.check_composition(prox_identity, lambda x: sum(x), self.v, places = 4)
        self.check_composition(prox_identity, lambda x: sum(x), self.B, places = 4)

    def test_logistic(self):
        # General composition tests.
        self.check_composition(prox_logistic, lambda x: logistic(x), self.c, places = 4, solver='ECOS')
        self.check_composition(prox_logistic, lambda x: sum(logistic(x)), self.v, places = 3, solver = 'SCS')
        self.check_composition(prox_logistic, lambda x: sum(logistic(x)), self.B, places = 3, solver = "SCS")

        # f(x) = \sum_i log(1 + exp(-y_i*x_i)).
        y = np.random.randn(*self.v.shape)
        self.check_composition(lambda v, *args, **kwargs: prox_logistic(v, y = y, *args, **kwargs),
                               lambda x: sum(logistic(-multiply(y,x))), self.v, places = 2, solver = "SCS")

        # Multi-task logistic regression: f(B) = \sum_i log(1 + exp(-Y_{ij}*B_{ij}).
        Y_mat = np.random.randn(*self.B.shape)
        self.check_composition(lambda v, *args, **kwargs: prox_logistic(v, y = Y_mat, *args, **kwargs),
                               lambda B: sum(logistic(-multiply(Y_mat,B))), self.B, places = 2, solver = "SCS")

    def test_pos(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_pos, places = 4)

        # General composition tests.
        self.check_composition(prox_pos, cvxpy.pos, self.c, places=4)
        self.check_composition(prox_pos, lambda x: sum(pos(x)), self.v, places=4)
        self.check_composition(prox_pos, lambda x: sum(pos(x)), self.B, places=4)

    def test_neg(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_neg, places = 4)

        # General composition tests.
        self.check_composition(prox_neg, cvxpy.neg, self.c, places=4)
        self.check_composition(prox_neg, lambda x: sum(neg(x)), self.v, places=4)
        self.check_composition(prox_neg, lambda x: sum(neg(x)), self.B, places=4)

    def test_neg_entr(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_neg_entr, places = 4)

        # General composition tests.
        self.check_composition(prox_neg_entr, lambda x: -entr(x), self.c, places=4)
        self.check_composition(prox_neg_entr, lambda x: sum(-entr(x)), self.v, places=4)
        self.check_composition(prox_neg_entr, lambda x: sum(-entr(x)), self.B, places=2, solver = "ECOS")

    def test_neg_log(self):
        # Elementwise consistency tests.
        self.check_elementwise(prox_neg_log, places = 4)

        # General composition tests.
        self.check_composition(prox_neg_log, lambda x: -log(x), self.c, places=4)
        self.check_composition(prox_neg_log, lambda x: sum(-log(x)), self.v, places=4)
        self.check_composition(prox_neg_log, lambda x: sum(-log(x)), self.B, places=2, solver="SCS")

    def test_neg_log_det(self):
        # TODO: Poor accuracy with scaling/compositions.
        # General composition tests.
        # self.check_composition(prox_neg_log_det, lambda B: -log_det(B), self.B_symm, places = 3, solver = "SCS")
        # self.check_composition(prox_neg_log_det, lambda B: -log_det(B), self.B_psd, places = 3, solver = "SCS")

        # Sparse inverse covariance estimation: f(B) = -log det(B) for symmetric positive definite B.
        B_spd = self.B_psd + np.eye(self.B_psd.shape[0])
        B_a2dr = prox_neg_log_det(B_spd, self.t)
        B_cvxpy = self.prox_cvxpy(B_spd, lambda B: -log_det(B), t = self.t, solver = "SCS")
        self.assertItemsAlmostEqual(B_a2dr, B_cvxpy, places = 2)

    def test_max(self):
        # General composition tests.
        self.check_composition(prox_max, cvxpy.max, self.c, places = 4)
        self.check_composition(prox_max, cvxpy.max, self.v, places = 4)
        self.check_composition(prox_max, cvxpy.max, self.B, places = 3, solver = "SCS")

    def test_norm1(self):
        # General composition tests.
        self.check_composition(prox_norm1, norm1, self.c, places = 4)
        self.check_composition(prox_norm1, norm1, self.v, places = 4)
        self.check_composition(prox_norm1, norm1, self.B, places = 4)

        # l1 trend filtering: f(x) = \alpha*||x||_1
        alpha = 0.5 + np.abs(np.random.randn())
        x_a2dr = prox_norm1(self.v, t = alpha*self.t)
        x_cvxpy = self.prox_cvxpy(self.v, norm1, t = alpha*self.t)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = 4)

        # Sparse inverse covariance estimation: f(B) = \alpha*||B||_1
        B_symm_a2dr = prox_norm1(self.B_symm, t = alpha*self.t)
        B_symm_cvxpy = self.prox_cvxpy(self.B_symm, norm1, t = alpha*self.t)
        self.assertItemsAlmostEqual(B_symm_a2dr, B_symm_cvxpy, places = 4)

    def test_norm2(self):
        # General composition tests.
        self.check_composition(prox_norm2, norm2, np.random.randn(), places = 4)
        self.check_composition(prox_norm2, norm2, self.v, places = 4, solver ="SCS")
        self.check_composition(prox_norm2, lambda B: cvxpy.norm(B, 'fro'), self.B, places = 3, solver ="SCS")

        # f(x) = \alpha*||x||_2
        alpha = 0.5 + np.abs(np.random.randn())
        x_a2dr = prox_norm2(self.v, t = alpha*self.t)
        x_cvxpy = self.prox_cvxpy(self.v, norm2, t = alpha*self.t)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = 4)

    # def test_norm_inf(self):
    #     # General composition tests.
    #     self.check_composition(prox_norm_inf, norm_inf, self.c, places = 4)
    #     self.check_composition(prox_norm_inf, norm_inf, self.v, places = 4)
    #     self.check_composition(prox_norm_inf, norm_inf, self.B, places = 3, solver="SCS")

    #     # f(x) = \alpha*||x||_{\infty}
    #     alpha = 0.5 + np.abs(np.random.randn())
    #     x_a2dr = prox_norm_inf(self.v, t = alpha*self.t)
    #     x_cvxpy = self.prox_cvxpy(self.v, norm_inf, t = alpha*self.t)
    #     self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = 4)

    def test_norm_nuc(self):
        # General composition tests.
        self.check_composition(prox_norm_nuc, normNuc, self.B, places = 3, solver='SCS')

        # Multi-task logistic regression: f(B) = \beta*||B||_*
        beta = 1.5 + np.abs(np.random.randn())
        B_a2dr = prox_norm_nuc(self.B, t = beta*self.t)
        B_cvxpy = self.prox_cvxpy(self.B, normNuc, t = beta*self.t, solver='SCS')
        self.assertItemsAlmostEqual(B_a2dr, B_cvxpy, places = 3)

    def test_group_lasso(self):
        # General composition tests.
        groupLasso = lambda B: sum([norm2(B[:,j]) for j in range(B.shape[1])])
        self.check_composition(prox_group_lasso, groupLasso, self.B, places = 3, solver ="SCS")

        # Multi-task logistic regression: f(B) = \alpha*||B||_{2,1}
        alpha = 1.5 + np.abs(np.random.randn())
        B_a2dr = prox_group_lasso(self.B, t = alpha*self.t)
        B_cvxpy = self.prox_cvxpy(self.B, groupLasso, t = alpha*self.t)
        self.assertItemsAlmostEqual(B_a2dr, B_cvxpy, places = 3)

        # Compare with taking l2-norm separately on each column.
        B_norm2 = [prox_norm2(self.B[:,j], t = alpha*self.t) for j in range(self.B.shape[1])]
        B_norm2 = np.vstack(B_norm2)
        self.assertItemsAlmostEqual(B_a2dr, B_norm2, places = 3)

    # def test_sigma_max(self):
    #     # General composition tests.
    #     self.check_composition(prox_sigma_max, sigma_max, self.B, places = 4)

    def test_sum_squares(self):
        # General composition tests.
        self.check_composition(prox_sum_squares, sum_squares, self.v, places = 4)
        self.check_composition(prox_sum_squares, sum_squares, self.B, places = 4)

        # f(x) = (1/2)*||x - offset||_2^2
        offset = np.random.randn(*self.v.shape)
        x_a2dr = prox_sum_squares(self.v, t = 0.5*self.t, offset = offset)
        x_cvxpy = self.prox_cvxpy(self.v, sum_squares, t = 0.5*self.t, offset = offset)
        self.assertItemsAlmostEqual(x_a2dr, x_cvxpy, places = 4)

    def test_sum_squares_affine(self):
        # Scalar terms.
        F = np.random.randn()
        g = np.random.randn()
        v = np.random.randn()

        self.check_composition(lambda v, *args, **kwargs: prox_sum_squares_affine(v, F = F, g = g, method ="lsqr",
                                                                                  *args, **kwargs), lambda x: sum_squares(F*x - g), v)
        self.check_composition(lambda v, *args, **kwargs: prox_sum_squares_affine(v, F = F, g = g, method ="lstsq",
                                                                                  *args, **kwargs), lambda x: sum_squares(F*x - g), v)

        # Simple sum of squares.
        n = 100
        F = np.eye(n)
        g = np.zeros(n)
        v = np.random.randn(n)

        self.check_composition(lambda v, *args, **kwargs: prox_sum_squares_affine(v, F = F, g = g, method ="lsqr",
                                                                                  *args, **kwargs), lambda x: sum_squares(F*x - g), v)
        self.check_composition(lambda v, *args, **kwargs: prox_sum_squares_affine(v, F = F, g = g, method ="lstsq",
                                                                                  *args, **kwargs), lambda x: sum_squares(F*x - g), v)

        # General composition tests.
        m = 1000
        n = 100
        F = 10 + 5*np.random.randn(m,n)
        x = 2*np.random.randn(n)
        g = F.dot(x) + 0.01*np.random.randn(m)
        v = np.random.randn(n)

        self.check_composition(lambda v, *args, **kwargs: prox_sum_squares_affine(v, F = F, g = g, method ="lsqr",
                                                                                  *args, **kwargs), lambda x: sum_squares(F*x - g), v)
        self.check_composition(lambda v, *args, **kwargs: prox_sum_squares_affine(v, F = F, g = g, method ="lstsq",
                                                                                  *args, **kwargs), lambda x: sum_squares(F*x - g), v)

    def test_quad_form(self):
        # Simple quadratic.
        v = np.random.randn(1)
        Q = np.array([[5]])
        self.check_composition(lambda v, *args, **kwargs: prox_quad_form(v, Q = Q, *args, **kwargs),
                               lambda x: quad_form(x, P = Q), v)

        # General composition tests.
        n = 10
        v = np.random.randn(n)
        Q = np.random.randn(n,n)
        Q = Q.T.dot(Q) + 0.5*np.eye(n)
        self.check_composition(lambda v, *args, **kwargs: prox_quad_form(v, Q = Q, *args, **kwargs),
                               lambda x: quad_form(x, P = Q), v)

    def test_trace(self):
        # General composition tests.
        self.check_composition(prox_trace, cvxpy.trace, self.B_square, places = 4)

        C = np.random.randn(*self.B.shape)
        self.check_composition(lambda B, *args, **kwargs: prox_trace(B, C = C, *args, **kwargs),
                               lambda X: cvxpy.trace(C.T * X), self.B, places = 4)

        # Sparse inverse covariance estimation: f(B) = tr(BQ) for symmetric positive semidefinite Q.
        Q = np.random.randn(*self.B_square.shape)
        Q = Q.T.dot(Q)
        B_a2dr = prox_trace(self.B_square, t = self.t, C = Q.T)   # tr(BQ) = tr(QB) = tr((Q^T)^TB)
        B_cvxpy = self.prox_cvxpy(self.B_square, lambda X: cvxpy.trace(X * Q), t = self.t)
        self.assertItemsAlmostEqual(B_a2dr, B_cvxpy, places = 4)

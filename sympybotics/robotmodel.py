
import sys
import numpy

from .geometry import Geometry
from .kinematics import Kinematics
from .dynamics import Dynamics
from .symcode import Subexprs, code_to_func

def _fprint(x):
    print(x)
    sys.stdout.flush()


class RobotAllSymb(object):
    """
    Robot geometric, kinematic, and dynamic models in single symbolic
    expressions.
    """

    def __init__(self, rbtdef):

        self.rbtdef = rbtdef
        self.dof = rbtdef.dof

        self.geo = Geometry(self.rbtdef)
        self.kin = Kinematics(self.rbtdef, self.geo)

        self.dyn = Dynamics(self.rbtdef, self.geo)
        self.dyn.gen_all()


class RobotDynCode(object):

    """Robot dynamic model in code form."""

    def __init__(self, rbtdef, verbose=False):

        if verbose:
            p = _fprint
        else:
            p = lambda x: None

        self.rbtdef = rbtdef
        self.dof = rbtdef.dof

        p('generating geometric model')
        self.geo = Geometry(self.rbtdef)

        p('generating kinematic model')
        self.kin = Kinematics(self.rbtdef, self.geo)

        self.dyn = Dynamics(self.rbtdef, self.geo)

        p('generating tau code')
        tau_se = Subexprs()
        self.dyn.gen_tau(tau_se.collect)
        self.tau_code = tau_se.get(self.dyn.tau)

        p('generating gravity term code')
        g_se = Subexprs()
        self.dyn.gen_gravityterm(g_se.collect)
        self.g_code = g_se.get(self.dyn.gravityterm)

        p('generating coriolis term code')
        c_se = Subexprs()
        self.dyn.gen_coriolisterm(c_se.collect)
        self.c_code = c_se.get(self.dyn.coriolisterm)

        p('generating inertia matrix code')
        M_se = Subexprs()
        self.dyn.gen_inertiamatrix(M_se.collect)
        self.M_code = M_se.get(self.dyn.inertiamatrix)

        p('generating regressor matrix code')
        H_se = Subexprs()
        self.dyn.gen_regressor(H_se.collect)
        self.H_code = H_se.get(self.dyn.regressor)
        self._H_se = H_se._subexp_iv

        self._codes = ['tau_code', 'g_code', 'c_code', 'M_code', 'H_code']

        if self.rbtdef.frictionmodel is not None:
            p('generating friction term code')
            f_se = Subexprs()
            self.dyn.gen_frictionterm(f_se.collect)
            self.f_code = f_se.get(self.dyn.frictionterm)
            self._codes.append('f_code')

        p('done')

    def calc_base_parms(self, verbose=False):

        q_subs = {q: 'q[%d]' % i for i, q in enumerate(self.rbtdef.q)}
        q_subs.update(
            {dq: 'dq[%d]' % i for i, dq in enumerate(self.rbtdef.dq)})
        q_subs.update(
            {ddq: 'ddq[%d]' % i for i, ddq in enumerate(self.rbtdef.ddq)})
        func_def_regressor = code_to_func(
            'python', self.H_code, 'regressor_func', ['q', 'dq', 'ddq'],
            q_subs)
        global sin, cos, sign
        sin = numpy.sin
        cos = numpy.cos
        sign = numpy.sign
        exec(func_def_regressor)

        if verbose:
            _fprint('calculating base parameters and regressor code')

        self.dyn.calc_base_parms(regressor_func)

        H_se = Subexprs()
        H_se._subexp_iv = self._H_se
        self.Hb_code = H_se.get(self.dyn.regressor * self.dyn.Pb)

        self._codes.append('Hb_code')

        if verbose:
            _fprint('done')

import sympy

from . import symcode


def _gen_q_dq_ddq_subs(dof):
    subs = {}
    for i in reversed(range(dof)):
        subs[sympy.Symbol(r'\ddot{q}_' + str(i + 1))] = 'ddq[' + str(i) + ']'
        subs[sympy.Symbol(r'\dot{q}_' + str(i + 1))] = 'dq[' + str(i) + ']'
        subs[sympy.Symbol('q' + str(i + 1))] = 'q[' + str(i) + ']'
    return subs


def _gen_parms_subs(parms_symbols, name='parms'):
    subs = {}
    for i, parm in enumerate(parms_symbols):
        subs[parm] = name + '[' + str(i) + ']'
    return subs


def dyn_code_to_func(lang, code, funcname, qderivlevel, dof,
                     dynparam_symbols=None):
    func_parms = []
    subs_pairs = {}
    if dynparam_symbols:
        func_parms.append('parms')
        subs_pairs.update(_gen_parms_subs(dynparam_symbols, 'parms'))
    if qderivlevel >= 0:
        for i in range(qderivlevel + 1):
            func_parms.append('d' * i + 'q')
        subs_pairs.update(_gen_q_dq_ddq_subs(dof))
    return symcode.generation.code_to_func(lang, code, funcname, func_parms,
                                           subs_pairs)
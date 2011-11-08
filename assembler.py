""" Assembles functions to linear integer-based codes.
"""

import vm_insn
import asmparser

class Assembler(object):
    def __init__(self, funcs):
        self.raw_funcs = funcs
        self.insns = []
        self.func_map = {}
        self.code_segment = None

    def assemble(self):
        func_addrs = {}
        curr_offset = 0
        codes = []
        main_addr = 0

        # pass 1 -- assemble function and fix their size
        for raw_func in self.raw_funcs:
            name = raw_func.name
            if name.sval == 'main':
                main_addr = curr_offset
            code = Code(raw_func)
            codes.append(code)
            func_addrs[name] = curr_offset
            curr_offset += len(code.insns)

        # pass 2 -- resolve absolute addr for func calls
        for code in codes:
            for stmt, w_insn_id in code.calls:
                opname = stmt.op.sval
                op_num = vm_insn.insn_names['op_' + opname]
                args = stmt.args
                a = code.locals_map[args[0]] # return slot
                func_name = args[1]
                b = code.locals_map[args[2]] # first arg
                c = args[3].to_int() # argc
                code.insns[w_insn_id.to_int()] = vm_insn.pack(
                    op_num, a, b, c, func_addrs[func_name]
                )

        # pass 3 -- merge all codes
        all_codes = []
        for code in codes:
            all_codes.extend(code.insns)

        self.code_segment = all_codes
        self.main_addr = main_addr


class Code(object):
    def __init__(self, raw_func):
        locals_map = {}
        for attr, value in raw_func.proto.items():
            if attr.sval == 'args' or attr.sval == 'locals': # arg/locals
                for arg in value:
                    assert isinstance(arg, asmparser.W_Symbol)
                    frame_idx = len(locals_map)
                    locals_map[arg] = frame_idx
            else:
                raise ValueError(attr.sval)

        # reverse all so as to make caller pushing args easiler.
        for key in locals_map:
            val = locals_map[key]
            locals_map[key] = len(locals_map) - val - 1
        # func(a, b) local c, d ->
        # a = 3, b = 2, c = 1, d = 0

        insns = []
        labels = {} # symbol->label's index
        unresolved_branches = [] # (stmt, w_insn_idx)
        unresolved_calls = [] # (stmt, w_insn_idx)
        insns.append(vm_insn.pack(vm_insn.insn_names['op_enter'], 0,
                                  imm=len(locals_map)))
        for stmt in raw_func.body:
            opname = stmt.op.sval
            try:
                op_num = vm_insn.insn_names['op_' + opname]
            except KeyError: # label
                op_num = 0
            args = stmt.args
            if opname == 'movei':
                a = locals_map[args[0]]
                imm = args[1].to_int()
                insns.append(vm_insn.pack(op_num, a, imm=imm))
            elif opname == 'add' or opname == 'sub':
                a = locals_map[args[0]]
                b = locals_map[args[1]]
                c = locals_map[args[2]]
                insns.append(vm_insn.pack(op_num, a, b, c))
            elif opname == 'addi':
                a = locals_map[args[0]]
                b = locals_map[args[1]]
                imm = args[2].to_int()
                insns.append(vm_insn.pack(op_num, a, b, imm=imm))
            elif opname == 'blt' or opname == 'blti' or opname == 'j':
                unresolved_branches.append((stmt, asmparser.W_Int(len(insns))))
                insns.append(0) # dummy
            elif opname == 'label':
                labels[args[0]] = len(insns)
            elif opname == 'halt':
                insns.append(vm_insn.pack(op_num, a=0))
            elif opname == 'ret': # restore sp.
                a = locals_map[args[0]]
                imm = len(locals_map)
                insns.append(vm_insn.pack(op_num, a, imm=imm))
            elif opname == 'print':
                a = locals_map[args[0]]
                insns.append(vm_insn.pack(op_num, a))
            elif opname == 'call': # a:ret-slot imm:func b:first-arg c:argc
                #a = locals_map[args[0]]
                #imm = args[1]
                #b = locals_map[args[2]]
                #c = args[3].to_int()
                unresolved_calls.append((stmt, asmparser.W_Int(len(insns))))
                insns.append(0) # dummy
            else:
                raise ValueError(opname)

        # resolve labels.
        for stmt, w_insn_idx in unresolved_branches:
            opname = stmt.op.sval
            op_num = vm_insn.insn_names['op_' + opname]
            args = stmt.args
            if opname == 'blt': # lhs rhs label
                a = locals_map[args[0]]
                b = locals_map[args[1]]
                lbl = args[2]
                insns[w_insn_idx.to_int()] = vm_insn.pack(
                    op_num, a, b, imm=labels[lbl] - w_insn_idx.to_int() - 1
                )
            elif opname == 'blti': # lhs imm label
                a = locals_map[args[0]]
                imm = args[1].to_int()
                lbl = args[2]
                insns[w_insn_idx.to_int()] = vm_insn.pack(
                    op_num, a, b=imm, imm=labels[lbl] - w_insn_idx.to_int() - 1
                )
            elif opname == 'j': # label
                lbl = args[0]
                insns[w_insn_idx.to_int()] = vm_insn.pack(
                    op_num, a=0, imm=labels[lbl] - w_insn_idx.to_int() - 1
                )

        # for func calls, resolve them later.
        self.insns = insns
        self.calls = unresolved_calls
        self.locals_map = locals_map


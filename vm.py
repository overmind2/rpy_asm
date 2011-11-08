
import vm_insn
#from pypy.rlib.jit import JitDriver, elidable, hint

#jitdriver = JitDriver(greens=['insn', 'pc', 'op', 'a'],
#                      reds=['frame', 'vm'])

FRAMESIZE = 1024

class AsmVM(object):
    def __init__(self, code, main_addr, main_framesize):
        self.code = code
        self.frame = [0] * FRAMESIZE
        self.pc = main_addr
        self.sp = main_framesize

    def set(self, idx, val):
        self.frame[self.sp - idx] = val

    def at(self, idx):
        return self.frame[self.sp - idx]

    def run(self):
        op = 0
        insn = 0
        a = 0
        while True:
            #jitdriver.jit_merge_point(insn=insn, op=op, pc=self.pc, a=a,
            #                          vm=self, frame=self.frame)
            insn = self.code[self.pc]
            self.pc += 1 # rip mutation should be placed otherwhere?
            op = vm_insn.unpack_op(insn)
            a = vm_insn.unpack_a(insn)
            #self.dis(self.pc, op, insn)
            self.insn_dispatch(op, a, insn)

    insn_dispatch = vm_insn.insn_dispatch

    def dis(self, pc, op, insn):
        print '#%d %s %s, %s, %s, %s' % ((pc - 1), vm_insn.idx2name[op],
                vm_insn.unpack_a(insn), vm_insn.unpack_b(insn),
                vm_insn.unpack_c(insn), vm_insn.unpack_imm(insn))



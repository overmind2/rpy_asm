
from pypy.rlib.jit import elidable

def pack(op, a, b=0, c=0, imm=0):
    return op | (a << 8) | (b << 16) | (c << 24) | (imm << 32)

@elidable
def unpack_op(insn):
    return insn & 0xff

@elidable
def unpack_a(insn):
    return (insn >> 8) & 0xff

@elidable
def unpack_b(insn):
    b = (insn >> 16) & 0xff
    if b > 0x7f:
        b -= 0x100
    return b

@elidable
def unpack_c(insn):
    return (insn >> 24) & 0xff

@elidable
def unpack_imm(insn):
    imm = (insn >> 32) & 0xffffffff
    if imm >= 0x7fffffff:
        imm -= 0x100000000
    return imm

for name, func in globals().items():
    if name.startswith('unpack'):
        func._always_inline_ = True
del name
del func

insn_names = {}
idx2name = []
func_table = {}

def handles(name):
    name = 'op_%s' % name
    def wrap(func, name=name):
        insn_id = len(insn_names)
        insn_names[name] = insn_id
        func_table[name] = func
        idx2name.append(name)
        #func._always_inline_ = True
    return wrap

def make_dispatcher():
    d = func_table.copy()
    fmt = []
    prefix = ''
    fmt.append('def insn_dispatch(self, op, a, insn):')
    for name, func in func_table.iteritems():
        fmt.append('    %(prefix)sif op == %(insn_id)s:' % {
            'prefix': prefix,
            'insn_id': insn_names[name]
        })
        fmt.append('        %(func_name)s(self, a, insn)' % {
            'func_name': name
        })
        prefix = 'el'

    code = '\n'.join(fmt)
    #print code
    exec code in d
    retval = d['insn_dispatch']
    retval._always_inline_ = True
    return retval

@handles('movei')
def _movei(vm, a, insn):
    vm.set(a, unpack_imm(insn))

@handles('add')
def _add(vm, a, insn):
    b = unpack_b(insn)
    c = unpack_c(insn)
    vm.set(a, vm.at(b) + vm.at(c))

@handles('addi')
def _addi(vm, a, insn):
    b = unpack_b(insn)
    imm = unpack_imm(insn)
    vm.set(a, vm.at(b) + imm)

@handles('sub')
def _sub(vm, a, insn):
    b = unpack_b(insn)
    c = unpack_c(insn)
    vm.set(a, vm.at(b) - vm.at(c))

@handles('j')
def _j(vm, a, insn):
    imm = unpack_imm(insn)
    vm.pc += imm

@handles('blt')
def _blt(vm, a, insn):
    b = unpack_b(insn)
    if vm.at(a) < vm.at(b):
        imm = unpack_imm(insn)
        vm.pc += imm

@handles('blti')
def _blti(vm, a, insn):
    b = unpack_b(insn)
    if vm.at(a) < b:
        imm = unpack_imm(insn)
        vm.pc += imm

# inside callee
@handles('enter')
def _enter(vm, a, insn):
    imm = unpack_imm(insn)
    vm.sp += imm

@handles('call')
def _call(vm, a, insn):
    # save pc. sp is restored by callee
    first_arg = unpack_b(insn)
    argc = unpack_c(insn)
    # push args
    for dsp in range(argc):
        #print 'moving argument from %d' % (first_arg - dsp)
        #print 'to %d' % (2 + dsp)
        # +2 is for saved pc and a and +1 is for space.
        vm.frame[vm.sp + 3 + dsp] = vm.at(first_arg - dsp)

    func_addr = unpack_imm(insn) # absolute addr
    pc = vm.pc
    vm.sp += 2
    # push pc
    vm.set(0, pc)
    vm.set(1, a)
    # jump. sp will be adjust on entering the func
    vm.pc = func_addr

@handles('ret')
def _ret(vm, a, insn):
    # restore sp and pc
    imm = unpack_imm(insn)
    retval = vm.at(a)
    vm.sp -= imm
    saved_pc = vm.at(0)
    ret_addr = vm.at(1)
    vm.sp -= 2
    vm.pc = saved_pc
    vm.set(ret_addr, retval)

@handles('print')
def _print(vm, a, insn):
    print vm.at(a)

@handles('halt')
def _halt(vm, a, insn):
    raise SystemExit

insn_dispatch = make_dispatcher()


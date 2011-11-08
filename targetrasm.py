import asmparser
import assembler
import vm
from pypy.rlib.streamio import open_file_as_stream as open

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def main(argv):
    f = open(argv[1])
    src = f.readall()
    f.close()
    code = asmparser.AsmParser(src).program()
    asm = assembler.Assembler(code)
    asm.assemble()
    interp = vm.AsmVM(asm.code_segment, asm.main_addr, 8)
    try:
        interp.run()
    except SystemExit:
        pass
    return 0

def target(*argl):
    return main, None

if __name__ == '__main__':
    import sys
    main(sys.argv)


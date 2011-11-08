import __pypy_path__
from pypy.rlib.parsing.makepackrat import (PackratParser,
        BacktrackException, Status)

class W_Expr(object):
    def to_int(self):
        raise TypeError

class W_Symbol(W_Expr):
    obarray = {}
    def __init__(self, sval):
        self.sval = sval

    def __repr__(self):
        return self.sval

def make_symbol(s):
    if s in W_Symbol.obarray:
        return W_Symbol.obarray[s]
    else:
        sym = W_Symbol(s)
        W_Symbol.obarray[s] = sym
        return sym

class W_Int(W_Expr):
    def __init__(self, ival):
        self.ival = ival

    def to_int(self):
        return self.ival

    def __repr__(self):
        return str(self.ival)

class W_Function(W_Expr):
    def __init__(self, proto, body):
        self.proto = {}
        for attr in proto[1:]:
            name = attr.name
            value = attr.value
            self.proto[name] = value

        self.body = body

        attr = proto[0]
        assert isinstance(attr, W_FuncAttr)
        assert isinstance(attr.name, W_Symbol)
        self.name = attr.value[0]

    def __repr__(self):
        return 'function %s %s %s' % (self.name, self.proto, self.body)

class W_FuncAttr(W_Expr):
    def __init__(self, name, value):
        self.name = name
        self.value = clean_up(value)

    def __repr__(self):
        return 'funcattr %s %s' % (self.name, self.value)

class W_FuncStmt(W_Expr):
    def __init__(self, op, args):
        self.op = op
        self.args = clean_up(args)

    def __repr__(self):
        return 'funcstmt %s %s' % (self.op, self.args)

def clean_up(line):
    return line
    line = line.strip(' ')
    if not line:
        return []
    else:
        return [s.strip(' ') for s in line.split(',')]

class AsmParser(PackratParser):
    r'''
    IGNORE:
        ` |#[^\n]*`;

    INTEGER:
        c = `-?(0|([1-9][0-9]*))`
        IGNORE*
        return {W_Int(int(c))};

    SYMBOL:
        c = `[a-zA-Z_][a-zA-Z0-9_]*`
        IGNORE*
        return {make_symbol(c)};

    EOF:
        !__any__;

    NEWLINE:
        `[ ]*\n|#[^\n]*`;

    REST_OF_LINE:
        l = `[^#\n]*`
        IGNORE*
        return {l};

    program:
        s = func_def*
        NEWLINE*
        IGNORE*
        EOF
        return {s};

    func_def:
        NEWLINE*
        proto = func_proto
        body = func_body
        func_end
        return {W_Function(proto, body)};

    func_end:
        IGNORE*
        `\.endfunction`
        NEWLINE*;

    func_proto:
        attrs = func_attr*
        return {attrs};

    func_attr:
        IGNORE*
        '.'
        attr = SYMBOL
        args = arguments
        NEWLINE*
        return {W_FuncAttr(attr, args)};

    func_body:
        s = stmt*
        return {s};

    stmt:
        NEWLINE*
        IGNORE*
        op = SYMBOL
        args = arguments
        NEWLINE*
        IGNORE*
        return {W_FuncStmt(op, args)};

    arguments:
        a = (
            argument
            [IGNORE* ',' IGNORE*]
        )*
        last = argument
        return {a + [last]}
      | return {[]};

    argument:
        SYMBOL
      | INTEGER;

    '''
    packrat_using_default_init = True

def test():
    test_str = '''
# hai
    .function fibo # foo
    .args a, b # bar
    .locals c, d
    add a, b, 2
    sub c, d, -1
    label hai
    .endfunction

    .function main
    ret
    .endfunction

    '''
    p = AsmParser(test_str)
    print p.program()

if __name__ == '__main__':
    test()



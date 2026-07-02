"""Main compiler entry point — orchestrates Lexer → Parser → BASIC/PRG."""

from .lexer import Lexer
from .parser import Parser
from .token_types import C64PY_BUILTINS, C64PY_TYPES, C64PY_KEYWORDS
from .ast_nodes import TYPE_SIZE, is_fixed_type, fp_scale, promote_types, builtin_ret_type
from .basic_gen import BASICGenerator
from .code_emitter import PRG_LOAD_ADDR, PRG_CODE_OFFSET


def hex2(n):
    return f'${(n & 0xFF):02X}'


def hex4(n):
    return f'${(n & 0xFFFF):04X}'


class CompileResult:
    def __init__(self):
        self.tokens = []
        self.lex_errors = []
        self.ast = None
        self.parse_errors = []
        self.sem = None
        self.planner = None
        self.builder = None
        self.uses_float = False
        self.basic_code = ''
        self.success = False


def analyze_ast(ast):
    uses_float = False
    local_vars = 0
    global_vars = 0
    call_count = 0
    func_count = 0
    max_depth = 0
    depth = 0

    def walk(node):
        nonlocal uses_float, local_vars, global_vars, call_count, func_count, max_depth, depth
        if node is None:
            return
        d = depth
        max_depth = max(max_depth, depth)
        k = node.get('k', '')
        if k == 'Program':
            for g in node.get('globals', []):
                walk(g)
            for f in node.get('funcs', []):
                walk(f)
        elif k == 'VarDecl':
            global_vars += 1
            if node.get('type') == 'float' or node.get('init', {}).get('kind') == 'float':
                uses_float = True
            if node.get('init'):
                walk(node['init'])
        elif k == 'FuncDecl':
            func_count += 1
            if node.get('ret') == 'float':
                uses_float = True
            walk(node.get('body'))
        elif k in ('Block', 'then', 'else'):
            for s in node.get('stmts', []):
                walk(s)
        elif k in ('Assign', 'BinaryOp', 'UnaryOp', 'PostfixOp', 'Cast'):
            for child in ('target', 'value', 'left', 'right', 'operand', 'expr'):
                if child in node:
                    walk(node[child])
        elif k == 'Call':
            call_count += 1
            if node.get('name') in ('sin', 'cos', 'tan', 'sqr', 'log', 'exp', 'floor',
                                    'rnd', 'fadd', 'fsub', 'fmul', 'fdiv', 'fpow', 'float_to_str'):
                uses_float = True
            for a in node.get('args', []):
                walk(a)
        elif k == 'Literal':
            if node.get('kind') == 'float':
                uses_float = True
        elif k in ('If', 'While', 'DoWhile', 'For'):
            for child in ('cond', 'then', 'else', 'body', 'init', 'incr'):
                if child in node:
                    depth += 1
                    walk(node[child])
                    depth -= 1
        elif k in ('Return', 'Break', 'Continue', 'ExprStmt'):
            for child in ('value', 'expr'):
                if child in node:
                    walk(node[child])
        elif k in ('Ident', 'ArrayAccess'):
            pass

    walk(ast)
    return {
        'usesFloat': uses_float,
        'globalVars': global_vars,
        'localVars': max(0, local_vars - global_vars),
        'callCount': call_count,
        'funcCount': func_count,
        'maxDepth': max_depth,
    }


def compile_source(src):
    """Compile a C64PY source string. Returns CompileResult."""
    result = CompileResult()

    # 1. Lexer
    try:
        lexer = Lexer(src)
        tokens, lex_errors = lexer.tokenize()
        result.tokens = tokens
        result.lex_errors = lex_errors
    except Exception as e:
        result.lex_errors.append({'msg': str(e), 'line': 0, 'col': 0})
        return result

    if lex_errors:
        return result

    # 2. Parser
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        result.ast = ast
        result.parse_errors = parser.errors
    except Exception as e:
        result.parse_errors.append({'msg': str(e), 'line': 0, 'col': 0})
        return result

    if parser.errors:
        return result

    # 2b. Optimize
    from .optimizer import optimize_ast
    try:
        ast = optimize_ast(ast)
        result.ast = ast
    except Exception as e:
        pass

    # 3. Analyze
    try:
        qk = analyze_ast(ast)
        result.uses_float = qk['usesFloat']
    except Exception as e:
        pass

    # 4. BASIC Generation
    try:
        basic_gen = BASICGenerator(ast)
        result.basic_code = basic_gen.generate()
    except Exception as e:
        pass

    result.success = True
    return result


def compile_to_prg(src):
    """Compile C64PY source to PRG bytes."""
    from .code_emitter import PRG_CODE_OFFSET

    result = compile_source(src)
    if not result.success or result.lex_errors or result.parse_errors:
        return None, result

    ast = result.ast
    qk = analyze_ast(ast)
    uses_float = qk['usesFloat']

    # Create a scope for variables
    class SimpleScope:
        def __init__(self):
            self.symbols = {}

        def define(self, name, info):
            self.symbols[name] = info

        def lookup(self, name):
            return self.symbols.get(name)

    scope = SimpleScope()
    for g in ast.get('globals', []):
        scope.define(g['name'], {
            'type': g['type'], 'kind': 'var',
            'isArr': g.get('isArr', False),
            'line': g.get('line', 0)
        })
    for f in ast.get('funcs', []):
        scope.define(f['name'], {
            'type': f.get('ret', 'void'), 'kind': 'func',
            'params': f.get('params', []),
            'line': f.get('line', 0)
        })

    # Memory planner (simplified)
    class SimplePlanner:
        def __init__(self):
            self.globals = []
            self.func_layouts = {}
            self.bss_size = 0
            self.uses_float = uses_float
            self.zp_next = 0x02
            self.zp_end = 0x8B
            self._zp_black = set()
            self._init_blacklist()

        def _init_blacklist(self):
            blk = [0x00, 0x01]
            blk.extend(range(0x03, 0x07))
            blk.append(0x54)
            blk.extend(range(0x61, 0x8B))
            blk.extend(range(0x90, 0xFB))
            blk.extend([0xFB, 0xFC, 0xFD, 0xFE, 0xFF])
            if self.uses_float:
                blk.append(0x12)
                blk.extend(range(0x22, 0x2B))
                blk.extend([0x55, 0x56])
                blk.extend(range(0x57, 0x61))
                blk.extend(range(0x8B, 0x90))
            self._zp_black = set(blk)

        def _zp_alloc(self, n):
            start = self.zp_next
            while start + n <= self.zp_end:
                ok = True
                for i in range(n):
                    if (start + i) in self._zp_black:
                        start = start + i + 1
                        ok = False
                        break
                if ok:
                    self.zp_next = start + n
                    return start
            return None

        def plan(self):
            for g in ast.get('globals', []):
                t = g['type']
                arr_cnt = g.get('arrSize', {}).get('value', 0) if g.get('isArr') else 0
                base = TYPE_SIZE.get(t, 1)
                size = base * max(arr_cnt, 1) if g.get('isArr') else base
                addr = None
                is_zp = False
                if not g.get('isArr') and t != 'string' and t != 'float':
                    addr = self._zp_alloc(size)
                    if addr is not None:
                        is_zp = True
                if not is_zp:
                    self.bss_size += size
                self.globals.append({
                    'name': g['name'], 'type': t, 'size': size,
                    'addr': addr, 'isZP': is_zp,
                    'isArr': g.get('isArr', False),
                    'arrCount': max(arr_cnt, 0) if g.get('isArr') else 0,
                    'kind': 'global'
                })
            for f in ast.get('funcs', []):
                locals_ = []
                for p in f.get('params', []):
                    p_size = TYPE_SIZE.get(p['type'], 1)
                    p_addr = self._zp_alloc(p_size) if p['type'] != 'float' else None
                    locals_.append({
                        'name': p['name'], 'type': p['type'], 'size': p_size,
                        'kind': 'param', 'addr': p_addr, 'isZP': p_addr is not None
                    })
                self._collect_locals(f.get('body', {}), locals_)
                for v in locals_:
                    if v['kind'] == 'local' and not v.get('isArr') and v['addr'] is None:
                        if v['type'] != 'float':
                            v['addr'] = self._zp_alloc(v['size'])
                            v['isZP'] = v['addr'] is not None
                frame = sum(v['size'] for v in locals_ if not v.get('isArr'))
                if self.uses_float:
                    self.bss_size += frame
                self.func_layouts[f['name']] = {
                    'locals': locals_, 'frameBytes': frame, 'ret': f.get('ret', 'void')
                }
            return self

        def _collect_locals(self, node, out):
            if not node:
                return
            if node.get('k') == 'VarDecl':
                base = TYPE_SIZE.get(node['type'], 1)
                cnt = node.get('arrSize', {}).get('value', 0) if node.get('isArr') else 0
                sz = base * max(cnt, 1) if node.get('isArr') else base
                out.append({
                    'name': node['name'], 'type': node['type'], 'size': sz,
                    'kind': 'local', 'isArr': node.get('isArr', False),
                    'arrCount': cnt, 'addr': None, 'isZP': False
                })
                return
            if node.get('k') == 'Block':
                for s in node.get('stmts', []):
                    self._collect_locals(s, out)
            if node.get('k') in ('If',):
                self._collect_locals(node.get('then', {}), out)
                self._collect_locals(node.get('else', {}), out)
            if node.get('k') in ('While', 'DoWhile'):
                self._collect_locals(node.get('body', {}), out)
            if node.get('k') == 'For':
                self._collect_locals(node.get('init', {}), out)
                self._collect_locals(node.get('body', {}), out)

    planner = SimplePlanner().plan()

    # PRG Builder
    from .prg_builder import PRGBuilder
    builder = PRGBuilder(ast, planner, uses_float, scope).build()

    result.planner = planner
    result.builder = builder

    if builder.fixup_errs:
        result.success = False
        return None, result

    return builder.to_prg(), result

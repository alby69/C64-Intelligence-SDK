"""Optimizer — Optimization passes for PYC64 AST."""

def optimize_ast(ast):
    """
    Apply optimization passes to the AST.
    Current passes:
    - Constant folding
    """
    if ast is None:
        return None

    return fold_constants(ast)

def fold_constants(node):
    if node is None:
        return None

    # Process children first (bottom-up)
    if node['k'] == 'Program':
        for g in node.get('globals', []):
            fold_constants(g)
        for f in node.get('funcs', []):
            fold_constants(f)
    elif node['k'] == 'VarDecl':
        if node.get('init'):
            node['init'] = fold_constants(node['init'])
    elif node['k'] == 'FuncDecl':
        node['body'] = fold_constants(node['body'])
    elif node['k'] == 'Block':
        new_stmts = []
        for s in node.get('stmts', []):
            new_s = fold_constants(s)
            if new_s:
                new_stmts.append(new_s)
        node['stmts'] = new_stmts
    elif node['k'] == 'ExprStmt':
        node['expr'] = fold_constants(node['expr'])
    elif node['k'] == 'Assign':
        node['value'] = fold_constants(node['value'])
    elif node['k'] == 'If':
        node['cond'] = fold_constants(node['cond'])
        node['then'] = fold_constants(node['then'])
        if node.get('else'):
            node['else'] = fold_constants(node['else'])
    elif node['k'] == 'While':
        node['cond'] = fold_constants(node['cond'])
        node['body'] = fold_constants(node['body'])
    elif node['k'] == 'For':
        if node.get('init'): node['init'] = fold_constants(node['init'])
        if node.get('cond'): node['cond'] = fold_constants(node['cond'])
        if node.get('incr'): node['incr'] = fold_constants(node['incr'])
        node['body'] = fold_constants(node['body'])
    elif node['k'] == 'Return':
        if node.get('value'): node['value'] = fold_constants(node['value'])
    elif node['k'] == 'Call':
        new_args = []
        for a in node.get('args', []):
            new_args.append(fold_constants(a))
        node['args'] = new_args
    elif node['k'] == 'BinaryOp':
        node['left'] = fold_constants(node['left'])
        node['right'] = fold_constants(node['right'])

        # Try folding
        if node['left']['k'] == 'Literal' and node['right']['k'] == 'Literal':
            lval = node['left']['value']
            rval = node['right']['value']
            op = node['op']

            # Simple integer folding
            if isinstance(lval, int) and isinstance(rval, int):
                res = None
                if op == '+': res = lval + rval
                elif op == '-': res = lval - rval
                elif op == '*': res = lval * rval
                elif op == '/': res = lval // rval if rval != 0 else 0
                elif op == '&': res = lval & rval
                elif op == '|': res = lval | rval
                elif op == '^': res = lval ^ rval

                if res is not None:
                    return {'k': 'Literal', 'value': res, 'kind': 'int', '_type': node.get('_type', 'int')}

    elif node['k'] == 'UnaryOp':
        node['operand'] = fold_constants(node['operand'])
        if node['operand']['k'] == 'Literal':
            val = node['operand']['value']
            op = node['op']
            if op == '-':
                return {'k': 'Literal', 'value': -val, 'kind': 'int', '_type': node.get('_type', 'int')}
            elif op == '!':
                return {'k': 'Literal', 'value': 0 if val else 1, 'kind': 'bool', '_type': 'bool'}

    return node

// ═══════════════════════════════════════════════════════════════════════════
//  ANALISI AST — Fase 2b
// ═══════════════════════════════════════════════════════════════════════════

function analyzeAST(ast) {
  let usesFloat   = false;   // richiede BASIC ROM $A000
  let localVars   = 0;
  let globalVars  = 0;
  let callCount   = 0;
  let funcCount   = 0;
  let maxDepth    = 0;
  let depth       = 0;

  function walk(node) {
    if (!node) return;
    depth++;
    if (depth > maxDepth) maxDepth = depth;

    switch(node.k) {
      case 'Program':
        globalVars = node.globals.length;
        funcCount  = node.funcs.length;
        node.globals.forEach(walk);
        node.funcs.forEach(walk);
        break;
      case 'FuncDecl':
        walk(node.body);
        break;
      case 'VarDecl':
        if (node.type === 'float') usesFloat = true;
        localVars++;
        walk(node.init);
        walk(node.arrSize);
        if (node.arrInit) node.arrInit.forEach(walk);
        break;
      case 'Call':
        callCount++;
        if (FLOAT_KERNAL_BUILTINS.has(node.name)) usesFloat = true;
        node.args.forEach(walk);
        break;
      case 'Cast':
        if (node.type === 'float') usesFloat = true;
        walk(node.expr);
        break;
      case 'Literal':
        if (node.kind === 'float') usesFloat = true;
        break;
      case 'BinaryOp':
        walk(node.left); walk(node.right);
        break;
      case 'UnaryOp': case 'PostfixOp':
        walk(node.operand);
        break;
      case 'Assign':
        walk(node.target); walk(node.value);
        break;
      case 'If':
        walk(node.cond); walk(node.then); walk(node.else);
        break;
      case 'While': case 'DoWhile':
        walk(node.cond); walk(node.body);
        break;
      case 'For':
        walk(node.init); walk(node.cond); walk(node.incr); walk(node.body);
        break;
      case 'Return':
        walk(node.value);
        break;
      case 'Block':
        node.stmts.forEach(walk);
        break;
      case 'ArrayAccess':
        walk(node.idx);
        break;
    }
    depth--;
  }

  walk(ast);
  // globalVars conteggiati separatamente
  localVars = Math.max(0, localVars - globalVars);
  return { usesFloat, globalVars, localVars, callCount, funcCount, maxDepth };
}
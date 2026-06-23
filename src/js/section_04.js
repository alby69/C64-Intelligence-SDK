// ═══════════════════════════════════════════════════════════════════════════
//  AST NODE FACTORY — Fase 2b
// ═══════════════════════════════════════════════════════════════════════════
const N = {
  Program:     (globals, funcs)                 => ({k:'Program',    globals, funcs}),
  FuncDecl:    (name, params, ret, body, line)  => ({k:'FuncDecl',   name, params, ret, body, line}),
  VarDecl:     (type, name, init, isArr, arrSize, arrInit, line) => ({k:'VarDecl', type, name, init, isArr, arrSize, arrInit, line}),
  Block:       (stmts)                          => ({k:'Block',      stmts}),
  Assign:      (target, value, line)            => ({k:'Assign',     target, value, line}),
  If:          (cond, then_, else_, line)       => ({k:'If',         cond, then:then_, else:else_, line}),
  While:       (cond, body, line)               => ({k:'While',      cond, body, line}),
  DoWhile:     (body, cond, line)               => ({k:'DoWhile',    body, cond, line}),
  For:         (init, cond, incr, body, line)   => ({k:'For',        init, cond, incr, body, line}),
  Return:      (value, line)                    => ({k:'Return',     value, line}),
  Break:       (line)                           => ({k:'Break',      line}),
  Continue:    (line)                           => ({k:'Continue',   line}),
  Call:        (name, args, line)               => ({k:'Call',       name, args, line}),
  BinaryOp:    (op, left, right)                => ({k:'BinaryOp',   op, left, right}),
  UnaryOp:     (op, operand)                    => ({k:'UnaryOp',    op, operand}),
  PostfixOp:   (op, operand)                   => ({k:'PostfixOp',  op, operand}),
  Literal:     (kind, value, raw)               => ({k:'Literal',    kind, value, raw}),
  Ident:       (name, line)                     => ({k:'Ident',      name, line}),
  ArrayAccess: (name, idx, line)                => ({k:'ArrayAccess',name, idx, line}),
  Cast:        (type, expr, line)               => ({k:'Cast',       type, expr, line}),
  ExprStmt:    (expr, line)                     => ({k:'ExprStmt',    expr, line}),
};

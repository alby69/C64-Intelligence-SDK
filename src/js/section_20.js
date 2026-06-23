// ═══════════════════════════════════════════════════════════════════════════
//  RENDER AST — Tab visuale
// ═══════════════════════════════════════════════════════════════════════════
function renderAST(ast) {
  const area = document.getElementById('ast-area');
  area.innerHTML = '';
  const root = document.createElement('div');
  root.className = 'ast-root';
  root.appendChild(buildASTNode(ast, 0));
  area.appendChild(root);
}

function buildASTNode(node, depth) {
  if (!node) return null;
  const item = document.createElement('div');
  item.className = 'ast-item';

  const label = document.createElement('div');
  label.className = 'ast-label';

  const toggle = document.createElement('span');
  toggle.className = 'ast-toggle';

  const kind = document.createElement('span');
  const children = [];

  switch(node.k) {

    case 'Program': {
      kind.textContent = '◈ PROGRAM';
      kind.className = 'ast-k-Program';
      const meta = el('span','ast-meta', `${node.funcs.length}f · ${node.globals.length}g`);
      label.append(toggle, kind, meta);
      node.globals.forEach(g => children.push(buildASTNode(g, depth+1)));
      node.funcs.forEach(f => children.push(buildASTNode(f, depth+1)));
      break;
    }
    case 'FuncDecl': {
      kind.className = 'ast-k-FuncDecl';
      const retBadge = badge(node.ret, 'type');
      const params = node.params.length
        ? el('span','ast-meta', `(${node.params.map(p=>p.type+' '+p.name).join(', ')})`)
        : el('span','ast-meta','()');
      kind.textContent = 'func ' + node.name;
      label.append(toggle, kind, params, retBadge);
      children.push(buildASTNode(node.body, depth+1));
      break;
    }
    case 'VarDecl': {
      kind.className = 'ast-k-VarDecl';
      const tb = badge(node.type, 'type');
      const arr = node.isArr ? el('span','ast-meta', `[${node.arrSize ? nodeInline(node.arrSize) : ''}]`) : null;
      kind.textContent = node.name;
      label.append(toggle, tb, kind);
      if (arr) label.append(arr);
      if (node.init) { label.append(el('span','ast-meta','=')); children.push(buildASTNode(node.init, depth+1)); }
      if (node.arrInit) { label.append(el('span','ast-meta',`= [${node.arrInit.length} elem]`)); node.arrInit.forEach(x=>children.push(buildASTNode(x,depth+1))); }
      // Dimensione tipo (se disponibile)
      const sz = TYPE_SIZE[node.type];
      if (sz) label.append(el('span','ast-meta',`${sz}B`));
      break;
    }
    case 'Block': {
      kind.className = 'ast-k-Block';
      kind.textContent = `{ ${node.stmts.length} stmt }`;
      label.append(toggle, kind);
      node.stmts.forEach(s => { if(s) children.push(buildASTNode(s, depth+1)); });
      break;
    }
    case 'Assign': {
      kind.className = 'ast-k-Assign';
      kind.textContent = nodeInline(node.target) + ' =';
      label.append(toggle, kind);
      children.push(buildASTNode(node.value, depth+1));
      break;
    }
    case 'If': {
      kind.className = 'ast-k-If';
      kind.textContent = 'if';
      label.append(toggle, kind, el('span','ast-meta', nodeInline(node.cond)));
      children.push(buildASTNode(node.then, depth+1));
      if (node.else) {
        const elseLabel = el('span','ast-k-If','else');
        const elseWrap = document.createElement('div');
        elseWrap.className='ast-item';
        const elseHead = document.createElement('div');
        elseHead.className='ast-label';
        const elseToggle=el('span','ast-toggle','');
        elseHead.append(elseToggle, elseLabel);
        elseWrap.append(elseHead);
        const elseChild = buildASTNode(node.else, depth+1);
        if (elseChild) {
          const elseChildDiv = document.createElement('div');
          elseChildDiv.className='ast-children';
          elseChildDiv.appendChild(elseChild);
          elseWrap.appendChild(elseChildDiv);
          setupToggle(elseToggle, elseWrap);
        }
        children.push(elseWrap);
      }
      break;
    }
    case 'While': {
      kind.className = 'ast-k-While';
      kind.textContent = 'while';
      label.append(toggle, kind, el('span','ast-meta', '('+nodeInline(node.cond)+')'));
      children.push(buildASTNode(node.body, depth+1));
      break;
    }
    case 'DoWhile': {
      kind.className = 'ast-k-DoWhile';
      kind.textContent = 'do…while';
      label.append(toggle, kind, el('span','ast-meta','('+nodeInline(node.cond)+')'));
      children.push(buildASTNode(node.body, depth+1));
      break;
    }
    case 'For': {
      kind.className = 'ast-k-For';
      kind.textContent = 'for';
      label.append(toggle, kind);
      if (node.init) children.push(buildASTNode(node.init, depth+1));
      if (node.cond) children.push(buildASTNode(node.cond, depth+1));
      if (node.incr) children.push(buildASTNode(node.incr, depth+1));
      children.push(buildASTNode(node.body, depth+1));
      break;
    }
    case 'Return': {
      kind.className = 'ast-k-Return';
      kind.textContent = 'return';
      label.append(toggle, kind);
      if (node.value) children.push(buildASTNode(node.value, depth+1));
      break;
    }
    case 'Break':    { kind.className='ast-k-Break';    kind.textContent='break';    label.append(toggle,kind); break; }
    case 'Continue': { kind.className='ast-k-Continue'; kind.textContent='continue'; label.append(toggle,kind); break; }

    case 'Call': {
      kind.className = 'ast-k-Call';
      kind.textContent = node.name + '()';
      label.append(toggle, kind, el('span','ast-meta',`${node.args.length} arg`));
      if (node._type && node._type !== 'void') label.append(typeBadge(node._type));
      node.args.forEach(a => children.push(buildASTNode(a, depth+1)));
      break;
    }
    case 'BinaryOp': {
      kind.className = 'ast-k-BinaryOp';
      kind.textContent = 'BinaryOp';
      label.append(toggle, kind, badge(node.op,'op'));
      if (node._type) label.append(typeBadge(node._type));
      children.push(buildASTNode(node.left,  depth+1));
      children.push(buildASTNode(node.right, depth+1));
      break;
    }
    case 'UnaryOp': {
      kind.className = 'ast-k-UnaryOp';
      kind.textContent = 'UnaryOp';
      label.append(toggle, kind, badge(node.op,'op'));
      children.push(buildASTNode(node.operand, depth+1));
      break;
    }
    case 'PostfixOp': {
      kind.className = 'ast-k-PostfixOp';
      kind.textContent = 'PostfixOp';
      label.append(toggle, kind, badge(node.op,'op'));
      children.push(buildASTNode(node.operand, depth+1));
      break;
    }
    case 'Literal': {
      const isFloat = node.kind==='float';
      const isStr   = node.kind==='str';
      kind.className = isStr ? 'ast-k-LitStr' : isFloat ? 'ast-k-LitFloat' : 'ast-k-Literal';
      kind.textContent = 'Literal';
      const valStr = isStr ? `"${String(node.value).slice(0,20)}"` : (node.raw ?? String(node.value));
      const vbadge = badge(valStr, isFloat?'float':isStr?'str':'val');
      label.append(toggle, kind, badge(node.kind,'type'), vbadge);
      break;
    }
    case 'Ident': {
      kind.className = 'ast-k-Ident';
      kind.textContent = node.name;
      label.append(toggle, kind);
      if (node._type) label.append(typeBadge(node._type));
      break;
    }
    case 'ArrayAccess': {
      kind.className = 'ast-k-ArrayAccess';
      kind.textContent = node.name + '[]';
      label.append(toggle, kind);
      children.push(buildASTNode(node.idx, depth+1));
      break;
    }
    case 'Cast': {
      kind.className = 'ast-k-Cast';
      kind.textContent = 'Cast';
      label.append(toggle, kind, badge(node.type,'type'));
      if (node.expr?._type) label.append(el('span','ast-meta','←'), typeBadge(node.expr._type));
      children.push(buildASTNode(node.expr, depth+1));
      break;
    }
    default: {
      kind.textContent = node.k || '?';
      label.append(toggle, kind);
    }
  }

  item.appendChild(label);

  const validChildren = children.filter(Boolean);
  if (validChildren.length > 0) {
    const childDiv = document.createElement('div');
    childDiv.className = 'ast-children';
    validChildren.forEach(c => childDiv.appendChild(c));
    item.appendChild(childDiv);
    setupToggle(toggle, item);
    // Collassa automaticamente nodi profondi
    if (depth >= 3) item.classList.add('ast-collapsed');
  } else {
    toggle.textContent = '';
  }

  return item;
}

function setupToggle(toggleEl, itemEl) {
  toggleEl.textContent = itemEl.classList.contains('ast-collapsed') ? '▶' : '▼';
  toggleEl.parentElement.addEventListener('click', e => {
    e.stopPropagation();
    itemEl.classList.toggle('ast-collapsed');
    toggleEl.textContent = itemEl.classList.contains('ast-collapsed') ? '▶' : '▼';
  });
}

// Rappresentazione inline compatta di un nodo (per preview in label)
function nodeInline(node) {
  if (!node) return '';
  switch(node.k) {
    case 'Literal':     return node.raw ?? String(node.value);
    case 'Ident':       return node.name;
    case 'ArrayAccess': return `${node.name}[${nodeInline(node.idx)}]`;
    case 'BinaryOp':    return `${nodeInline(node.left)} ${node.op} ${nodeInline(node.right)}`;
    case 'UnaryOp':     return `${node.op}${nodeInline(node.operand)}`;
    case 'PostfixOp':   return `${nodeInline(node.operand)}${node.op}`;
    case 'Call':        return `${node.name}(${node.args.map(nodeInline).join(',')})`;
    case 'Cast':        return `${node.type}(${nodeInline(node.expr)})`;
    case 'Assign':      return `${nodeInline(node.target)}=${nodeInline(node.value)}`;
    default:            return node.k;
  }
}

function el(tag, cls, text='') {
  const e = document.createElement(tag);
  e.className = cls; e.textContent = text; return e;
}
function badge(text, kind) {
  const b = document.createElement('span');
  b.className = `ast-badge ast-badge-${kind}`;
  b.textContent = text; return b;
}
function typeBadge(t) {
  const b = document.createElement('span');
  const col = typeColor(t);
  b.className = 'ast-badge';
  b.style.cssText = `color:${col};border-color:${col}44;font-size:9px;padding:0 3px;border-radius:2px;border:1px solid`;
  b.textContent = t; return b;
}
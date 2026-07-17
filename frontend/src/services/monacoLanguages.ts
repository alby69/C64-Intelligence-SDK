import { Monaco } from '@monaco-editor/react';

export function registerC64Languages(monaco: Monaco) {
  // Registra il linguaggio C64PY (Python-like per 6502)
  if (!monaco.languages.getLanguages().some(lang => lang.id === 'c64py')) {
    monaco.languages.register({ id: 'c64py' });
    monaco.languages.setMonarchTokensProvider('c64py', {
      keywords: [
        'def', 'return', 'byte', 'word', 'if', 'else', 'while', 'for', 'in', 'and', 'or', 'not', 'asm'
      ],
      builtins: [
        'poke', 'peek', 'wait', 'sys', 'kernal'
      ],
      tokenizer: {
        root: [
          [/[a-z_$][\w$]*/, {
            cases: {
              '@keywords': 'keyword',
              '@builtins': 'predefined',
              '@default': 'identifier'
            }
          }],
          [/#.*/, 'comment'],
          [/\$[0-9a-fA-F]+/, 'number.hex'],
          [/0x[0-9a-fA-F]+/, 'number.hex'],
          [/[0-9]+/, 'number'],
          [/"([^"\\]|\\.)*"/, 'string']
        ]
      }
    });

    // Configurazione dei commenti e delle parentesi per c64py
    monaco.languages.setLanguageConfiguration('c64py', {
      comments: {
        lineComment: '#',
      },
      brackets: [
        ['{', '}'],
        ['[', ']'],
        ['(', ')'],
      ],
      autoClosingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"', notIn: ['string'] },
        { open: '\'', close: '\'', notIn: ['string', 'comment'] },
      ]
    });
  }

  // Registra il linguaggio BASIC V2 Commodore
  if (!monaco.languages.getLanguages().some(lang => lang.id === 'basic64')) {
    monaco.languages.register({ id: 'basic64' });
    monaco.languages.setMonarchTokensProvider('basic64', {
      keywords: [
        'PRINT', 'GOTO', 'GOSUB', 'RETURN', 'IF', 'THEN', 'FOR', 'TO', 'STEP', 'NEXT',
        'POKE', 'SYS', 'PEEK', 'DATA', 'READ', 'RESTORE', 'DIM', 'REM', 'END', 'RUN',
        'LOAD', 'SAVE', 'VERIFY', 'NEW', 'CONT', 'LIST', 'CLR', 'INPUT', 'GET', 'ON'
      ],
      tokenizer: {
        root: [
          [/^[0-9]+/, 'keyword.line-number'],
          [/[A-Z]+/, {
            cases: {
              '@keywords': 'keyword',
              '@default': 'identifier'
            }
          }],
          [/REM.*/, 'comment'],
          [/"([^"\\]|\\.)*"/, 'string'],
          [/[0-9]+/, 'number']
        ]
      }
    });

    // Configurazione dei commenti per BASIC V2
    monaco.languages.setLanguageConfiguration('basic64', {
      comments: {
        lineComment: 'REM',
      },
      brackets: [
        ['(', ')'],
      ],
      autoClosingPairs: [
        { open: '(', close: ')' },
        { open: '"', close: '"', notIn: ['string'] },
      ]
    });
  }
}

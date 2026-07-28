#!/usr/bin/env python3
"""List all available plugins with their commands."""
import sys
sys.path.insert(0, 'services/core_service')
from plugin_loader import PluginLoader

loader = PluginLoader()
plugins = loader.discover()
print('╔══ 10 Plugin disponibili ══╗')
for name, p in sorted(plugins.items()):
    cmds = ', '.join(c.name for c in p.commands)
    print(f'║ {name:20s}  {cmds}')
print('╚════════════════════════════╝')
print()
print('Usa: python3 plugins/<nome>/wrapper.py <comando>')
print('Oppure: make ide  (per l\'interfaccia grafica)')

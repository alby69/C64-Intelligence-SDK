import os

def assemble(output_filename, is_preview=False):
    with open('src/html/header.html', 'r') as f:
        header = f.read()

    with open('src/css/style.css', 'r') as f:
        css = f.read()

    with open('src/html/ui.html', 'r') as f:
        ui = f.read()

    # We want to use OUR versions of Lexer and Parser, but keep the original infrastructure for the rest.
    # The original Lexer is in section_03, Parser in section_05.
    # We will exclude those sections and use our lexer_py.js and parser_py.js.
    # Also TT is in section_02, we use token_types_py.js.

    js_files = []

    # Core Infrastructure (Pre-Lexer/Parser)
    for i in range(0, 2):
        js_files.append(f'section_{i:02d}.js')

    # Our Pythonic Core
    js_files.append('token_types_py.js')
    js_files.append('cm_mode.js')
    js_files.append('lexer_py.js')
    js_files.append('parser_py.js')
    js_files.append('basic_gen.js')
    js_files.append('examples_py.js')

    # Utility sections (Section 4 is N node factory)
    js_files.append('section_04.js')

    # Post-Parser sections (Semantic analysis starts around section 06/07 usually)
    for i in range(6, 28):
        js_files.append(f'section_{i:02d}.js')

    full_js = ""
    for js_file in js_files:
        path = f'src/js/{js_file}'
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
                # If it's a section that we want to partially override or if it contains things we need
                full_js += content + "\n\n"
        else:
            print(f"Warning: {js_file} not found")

    final_html = f"""{header}
<style>
{css}
</style>
</head>
<body>
{ui}
<script>
{full_js}
</script>
</body>
</html>"""

    with open(output_filename, 'w') as f:
        f.write(final_html)

assemble('c64py.html')
assemble('c64py_preview.html', is_preview=True)

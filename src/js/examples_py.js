EXAMPLES = { // OVERRIDE ORIGINAL
  hello: `# ─── Hello World ─────────────────────────────
def main():
    clear_screen()
    border_color(0)
    screen_color(6)
    print_at(10, 12, "HELLO, WORLD!")
    print_at(10, 14, "C64PY V0.6")
    print_at(0, 22, "BYTE=")   print(42)
    print_at(0, 23, "SCORE=")  print(1234)
    wait(60)
`,
  pong: `# ─── PONG ─────────────────────────────────────
VIC_SPE: word = $D015
JOY2: word = $DC00

def main():
    clear_screen()
    print_at(17, 0, "PONG")
    x: byte = 160
    y: byte = 100
    while True:
        poke($D000, x)
        poke($D001, y)
        joy: byte = peek(JOY2)
        if (joy & 1) == 0: y = y - 2
        if (joy & 2) == 0: y = y + 2
        wait_frames(1)
`
};
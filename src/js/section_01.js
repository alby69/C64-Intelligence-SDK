// ═══════════════════════════════════════════════════════════════════════════
//  EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════
var EXAMPLES = { // CHANGED TO VAR TO ALLOW OVERRIDE
hello: `// ─── Hello World ─────────────────────────────
func main() {
    clear_screen();
    border_color(0);
    screen_color(6);
    print_at(10, 12, "HELLO, WORLD!");
    print_at(10, 14, "C64C V0.6");
    print_at(0, 22, "BYTE=");   print(42);
    print_at(0, 23, "SCORE=");  print(1234);
    wait(60);
}
`,
screen: `// ─── Fill Screen ──────────────────────────────
word SCREEN_RAM = $0400;
word COLOR_RAM  = $D800;

func main() {
    clear_screen();
    border_color(0);
    word i = 0;
    while (i < 1000) {
        poke(SCREEN_RAM + i, 160);
        poke(COLOR_RAM  + i, i % 16);
        i = i + 1;
    }
    wait(200);
}
`,
loop: `// ─── Color Loop ───────────────────────────────
func main() {
    clear_screen();
    print_at(12, 12, "COLOR LOOP");
    byte c = 0;
    while (1) {
        border_color(c);
        screen_color(c);
        wait(6);
        c = (c + 1) % 16;
    }
}
`,
border: `// ─── Border Animation ────────────────────────
word VIC_BORDER = $D020;
word VIC_BG     = $D021;

func main() {
    clear_screen();
    poke(VIC_BG, 0);
    print_at(11, 12, "BORDER EFFECT");
    byte c = 0;
    while (1) {
        poke(VIC_BORDER, c % 16);
        wait_frames(1);
        c = c + 1;
    }
}
`,
raster: `// ─── Raster Bars ──────────────────────────────
word VIC_BORDER = $D020;
word VIC_BG     = $D021;
word VIC_RASTER = $D012;
byte BAR_COLORS[8] = [2, 10, 7, 1, 7, 10, 2, 0];

func draw_bars() {
    byte i = 0;
    while (i < 8) {
        byte target = i * 25;
        while (peek(VIC_RASTER) != target) {}
        poke(VIC_BORDER, BAR_COLORS[i]);
        poke(VIC_BG,     BAR_COLORS[i]);
        i = i + 1;
    }
}

func main() {
    poke($D011, peek($D011) & %01111111);
    while (1) {
        draw_bars();
    }
}
`,
floatmath: `// ─── Float Math (KERNAL ROM) ──────────────────
// Chiama routines float del BASIC ROM via FAC1.
// Richiede $01=$37 (BASIC ROM visibile) — automatico.
// GIVAYF ($B391): Y=lo byte, A=hi byte (sign ext) -> FAC1
// FOUT   ($BDDD): FAC1 -> stringa ASCII stampabile
// Output atteso (gradi 0..90 step 15):
//   SIN(  0 DEG)=  0
//   SIN( 15 DEG)=  .258819
//   SIN( 30 DEG)=  .5
//   SIN( 45 DEG)=  .707107
//   SIN( 60 DEG)=  .866025
//   SIN( 75 DEG)=  .965926
//   SIN( 90 DEG)=  1
//   SQR(9)=  3
//   LOG(2)=  .693147
//   EXP(1)=  2.71828

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(0, 0, "FLOAT MATH/KERNAL ROM");
    print_at(0, 1, "SIN 0..90 DEG STEP 15");

    // ── sin(deg): angoli 0..90 step 15 gradi ──────────────
    // PI/180 = 0.017453293 (conversione gradi -> radianti)
    float deg2rad = 0.017453293;
    byte deg = 0;
    byte row = 3;
    while (deg < 91) {
        border_color(deg % 16);
        float rad = float(deg) * deg2rad;
        print_at(0, row, "SIN(");
        print(deg);        // stampa l'angolo in gradi
        print(" DEG)=");
        print(sin(rad));   // stampa sin(rad) con decimali
        deg = deg + 15;
        row = row + 1;
    }

    // ── Funzioni matematiche ───────────────────────────────
    border_color(5);
    byte x = 9;
    print_at(0, 12, "SQR(9)="); print(sqr(x));
    x = 2;
    print_at(0, 13, "LOG(2)="); print(log(x));
    x = 1;
    print_at(0, 14, "EXP(1)="); print(exp(x));
    x = 4;
    print_at(0, 15, "ABS(4)= "); print(abs(x));
}
`
,
sid: `// ─── SID Jingle ───────────────────────────────
// Melodia tramite SID chip ($D400-$D418)
// Frequenze PAL C64: scala Do-Re-Mi-Fa-Sol-La-Si-Do

word SID_V1FL = $D400;   // Voice 1 Freq Lo
word SID_V1FH = $D401;   // Voice 1 Freq Hi
word SID_V1CR = $D404;   // Control Reg (waveform + gate)
word SID_V1AD = $D405;   // Attack / Decay
word SID_V1SR = $D406;   // Sustain / Release
word SID_VOL  = $D418;   // Master Volume

// Frequenze PAL C64 (Hz × 2^24 / 985248)
// C4=4453 D4=4996 E4=5611 F4=5945 G4=6671 A4=7488 B4=8403 C5=8906
byte FREQ_LO[8] = [$65, $84, $EB, $79, $0F, $40, $D3, $CA];
byte FREQ_HI[8] = [$11, $13, $15, $17, $1A, $1D, $20, $22];
byte DURAT[8]   = [20, 20, 20, 20, 20, 20, 20, 40];

func play_note(byte idx) {
    poke(SID_V1FL, FREQ_LO[idx]);
    poke(SID_V1FH, FREQ_HI[idx]);
    poke(SID_V1CR, $21);      // sawtooth + gate ON
    wait(DURAT[idx]);
    poke(SID_V1CR, $20);      // gate OFF (release)
    wait(8);
}

func main() {
    clear_screen();
    border_color(6);
    screen_color(0);
    print_at(10, 11, "SID JINGLE");
    print_at(6,  13, "DO RE MI FA SOL LA SI DO");

    poke(SID_VOL,  $0F);   // volume massimo
    poke(SID_V1AD, $08);   // attack 2ms, decay 50ms
    poke(SID_V1SR, $F0);   // sustain max, release veloce

    byte rep = 0;
    while (rep < 2) {
        byte i = 0;
        while (i < 8) {
            border_color(i + 2);
            play_note(i);
            i = i + 1;
        }
        rep = rep + 1;
    }

    poke(SID_V1CR, $20);
    poke(SID_VOL, 0);
    border_color(6);
}
`,
sprite: `// ─── Sprite Bounce ────────────────────────────
// Sprite 0 rimbalza sullo schermo via VIC-II
// Dati @ $3400 = blocco VIC 208 (208 * 64)

word VIC_S0X  = $D000;   // Sprite 0 X (bit 7..0)
word VIC_S0Y  = $D001;   // Sprite 0 Y
word VIC_S0C  = $D027;   // Sprite 0 Color
word VIC_SPR  = $D015;   // Sprite Enable (bit0 = spr0)
word SPR0_PTR = $07F8;   // Puntatore dati sprite 0
word SPR_BASE = $3400;   // Blocco dati (64 byte)

func init_sprite() {
    // Azzera 64 byte del blocco sprite
    byte k = 0;
    while (k < 64) {
        poke(SPR_BASE + k, 0);
        k = k + 1;
    }
    // Pallina 8x8: ogni riga = 3 byte; byte[1] = pixel centrali
    poke(SPR_BASE +  1, $18);   // ..011000
    poke(SPR_BASE +  4, $3C);   // .0111100
    poke(SPR_BASE +  7, $7E);   // 01111110
    poke(SPR_BASE + 10, $FF);   // 11111111
    poke(SPR_BASE + 13, $FF);   // 11111111
    poke(SPR_BASE + 16, $7E);   // 01111110
    poke(SPR_BASE + 19, $3C);   // .0111100
    poke(SPR_BASE + 22, $18);   // ..011000
    poke(SPR0_PTR, 208);        // punta al blocco 208
    poke(VIC_S0C, 7);           // colore: giallo
    poke(VIC_SPR, 1);           // abilita sprite 0
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(13, 1, "SPRITE BOUNCE");

    init_sprite();

    byte x    = 100;
    byte y    = 100;
    byte dirx = 0;   // 0=destra  1=sinistra
    byte diry = 0;   // 0=giu     1=su

    while (1) {
        poke(VIC_S0X, x);
        poke(VIC_S0Y, y);
        wait_frames(1);

        if (x > 228) { dirx = 1; }
        if (x < 28)  { dirx = 0; }
        if (y > 224) { diry = 1; }
        if (y < 50)  { diry = 0; }

        if (dirx == 0) { x = x + 2; }
        if (dirx == 1) { x = x - 2; }
        if (diry == 0) { y = y + 1; }
        if (diry == 1) { y = y - 1; }

        border_color(x % 16);
    }
}
`,
charset: `// ─── Charset Map ──────────────────────────────
// Tutti i 256 caratteri PETSCII con 16 colori
// Cicla il colore del bordo in loop infinito

word SCREEN = $0400;
word COLOR  = $D800;

func main() {
    border_color(0);
    screen_color(0);

    // Riempi 1000 celle: char = sc & 255, colore = sc % 16
    word sc = 0;
    while (sc < 1000) {
        poke(SCREEN + sc, sc & 255);
        poke(COLOR  + sc, sc % 16);
        sc = sc + 1;
    }

    // Anima il bordo in loop
    byte c = 0;
    while (1) {
        border_color(c);
        wait(4);
        c = (c + 1) % 16;
    }
}
`,
floatarith: `// ─── Float Arithmetic con Variabili ──────────────────
// Dimostra aritmetica vera tra variabili float (5 byte CBM).
// Operatori: fadd fsub fmul fdiv fpow e operatori + - * / ^
// Routines KERNAL: FADD($B867) FSUB($B853) FMUL($BA28) FDIV($BB12) FPWR($BF78)
// Convenzione: FAC2 OP FAC1 → FAC1 · MOVFM($BBA2) / MOVMF($BBD4)

float pi   = 3.14159;
float e_   = 2.71828;
float half = 0.5;
float neg  = -1.5;
float zero = 0.0;

func main() {
    clear_screen();
    print_at(4,  0, "FLOAT ARITHMETIC");
    print_at(2,  1, "FAC1/FAC2 KERNAL ROM");

    // Somma: pi + half
    float sum_ = fadd(pi, half);
    print_at(0, 3, "PI+.5=");  print(sum_);

    // Differenza: pi - half
    float dif = fsub(pi, half);
    print_at(0, 4, "PI-.5=");  print(dif);

    // Prodotto: pi * e_
    float prod = fmul(pi, e_);
    print_at(0, 5, "PI*E =");  print(prod);

    // Divisione: pi / e_
    float quot = fdiv(pi, e_);
    print_at(0, 6, "PI/E =");  print(quot);

    // Valore assoluto di -1.5
    float a = abs(neg);
    print_at(0, 7, "ABS  =");  print(a);

    // Sin di pi (approx 0)
    float s = sin(pi);
    print_at(0, 8, "SIN  =");  print(s);

    // Radice di pi
    float r = sqr(pi);
    print_at(0, 9, "SQR  =");  print(r);

    // Loop: accumulo float
    print_at(0, 11, "LOOP +0.5:");
    float acc = zero;
    byte row = 12;
    while (row < 20) {
        print_at(3, row, "ACC=");
        print(acc);
        acc = fadd(acc, half);
        row = row + 1;
    }
}
`,

plasma: `// ─── Plasma Effect ────────────────────────────
// Effetto plasma classico C64 via border/BG color
// Usa sin() del KERNAL per modulare il colore.
// Richiede BASIC ROM ($01=$37) per float KERNAL.

word VIC_BORDER = $D020;
word VIC_BG     = $D021;

func main() {
    clear_screen();
    screen_color(0);
    print_at(14, 12, "PLASMA");

    byte t = 0;
    while (1) {
        byte a = t;
        byte b = t + 64;
        byte s1 = sin(a);     // sin(t)
        byte s2 = cos(b);     // cos(t+64)
        byte c1 = (s1 + 8) % 16;
        byte c2 = (s2 + 8) % 16;
        border_color(c1);
        screen_color(c2);
        wait(2);
        t = t + 3;
    }
}
`,
music: `// ─── Arpeggio SID ─────────────────────────────
// Arpeggio ciclico su 4 note con inviluppo ADSR
// Voice 1: triangle wave, Voice 2: sawtooth

word SID_V1FL = $D400;
word SID_V1FH = $D401;
word SID_V1CR = $D404;
word SID_V1AD = $D405;
word SID_V1SR = $D406;
word SID_V2FL = $D407;
word SID_V2FH = $D408;
word SID_V2CR = $D40B;
word SID_V2AD = $D40C;
word SID_V2SR = $D40D;
word SID_VOL  = $D418;

// Frequenze PAL: Am chord  A3 C4 E4 A4
byte LO1[4] = [$B2, $65, $AF, $B2];
byte HI1[4] = [$0B, $11, $15, $16];
// Quarta sopra per voice 2: D4 F4 A4 D5
byte LO2[4] = [$96, $96, $B2, $96];
byte HI2[4] = [$14, $17, $1A, $28];

func note_on(byte idx) {
    poke(SID_V1FL, LO1[idx]);
    poke(SID_V1FH, HI1[idx]);
    poke(SID_V2FL, LO2[idx]);
    poke(SID_V2FH, HI2[idx]);
    poke(SID_V1CR, $11);    // triangle + gate ON
    poke(SID_V2CR, $21);    // sawtooth + gate ON
}

func note_off() {
    poke(SID_V1CR, $10);    // gate OFF
    poke(SID_V2CR, $20);
}

func main() {
    clear_screen();
    border_color(6);
    screen_color(0);
    print_at(11, 11, "SID ARPEGGIO");
    print_at(7,  13, "AM CHORD - TRIANGLE+SAW");

    poke(SID_VOL,  $0F);
    poke(SID_V1AD, $23);
    poke(SID_V1SR, $90);
    poke(SID_V2AD, $13);
    poke(SID_V2SR, $A0);

    byte idx  = 0;
    byte tick = 0;
    while (1) {
        note_on(idx);
        border_color(idx * 4 + 1);
        wait(10);
        note_off();
        wait(4);
        idx = (idx + 1) % 4;
        tick = tick + 1;
        if (tick == 16) {
            idx = 0;
            tick = 0;
        }
    }
}
`,
starfield: `// ─── Starfield Scroller ───────────────────────
// 40 stelle che scorrono verso sinistra

word SCREEN = $0400;
word COLOR  = $D800;

byte STAR_X[40]   = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
byte STAR_Y[40]   = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14];
byte STAR_SPD[8]  = [1,1,1,2,2,2,3,3];
byte STAR_COL[8]  = [1,1,7,7,7,15,15,15];

func init_stars() {
    byte i = 0;
    while (i < 40) {
        STAR_X[i] = (i * 7 + 13) % 40;
        i = i + 1;
    }
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(12, 0, "* STARFIELD *");
    init_stars();
    while (1) {
        byte i = 0;
        while (i < 40) {
            byte x   = STAR_X[i];
            byte y   = STAR_Y[i];
            byte spd = STAR_SPD[i % 8];
            byte col = STAR_COL[i % 8];
            // indirizzo riga calcolato con addizioni word (evita overflow y*40)
            word sa  = $0400;
            word ca  = $D800;
            byte r   = 0;
            while (r < y) { sa = sa + 40; ca = ca + 40; r = r + 1; }
            poke(sa + x, 32);
            if (x < spd) { x = 39; } else { x = x - spd; }
            STAR_X[i] = x;
            poke(sa + x, $2A);
            poke(ca + x, col);
            i = i + 1;
        }
        wait(2);
    }
}
`,
sprite_mplex: `// ─── Sprite Multiplexer ───────────────────────
// 3 righe × 8 = 24 sprite virtuali con 8 HW
// Tecnica: raster polling → reposizionamento Y
// Sprite bitmap: pallina @ blocco VIC $3000 (192)

word VIC_SPE  = $D015;
word VIC_RAST = $D012;
word SPR_BASE = $3000;
word SPR_PTR0 = $07F8;

// 3 file Y di sprite
byte ROW_Y[3]   = [70, 130, 190];
// 8 colonne X (posizione iniziale)
byte COL_X[8]   = [30, 62, 94, 126, 158, 190, 218, 242];
// Direzione X per ogni colonna (1=destra 255=sinistra)
byte COL_DX[8]  = [1, 1, 2, 2, 255, 255, 254, 254];
// Colore per ogni riga
byte ROW_COL[3] = [10, 7, 13];

func init_spr() {
    byte k = 0;
    while (k < 64) { poke(SPR_BASE + k, 0); k = k + 1; }
    // Pallina rotonda
    poke(SPR_BASE + 1,  $18);
    poke(SPR_BASE + 4,  $3C);
    poke(SPR_BASE + 7,  $7E);
    poke(SPR_BASE + 10, $FF);
    poke(SPR_BASE + 13, $7E);
    poke(SPR_BASE + 16, $3C);
    poke(SPR_BASE + 19, $18);
    // Tutti e 8 puntano allo stesso blocco
    k = 0;
    while (k < 8) { poke(SPR_PTR0 + k, 192); k = k + 1; }
    poke(VIC_SPE, $FF);
}

func set_row(byte row) {
    byte y   = ROW_Y[row];
    byte col = ROW_COL[row];
    byte i = 0;
    while (i < 8) {
        poke($D001 + i + i, y);
        poke($D000 + i + i, COL_X[i]);
        poke($D027 + i, col);
        i = i + 1;
    }
}

func wait_raster(byte line) {
    while (peek(VIC_RAST) != line) {}
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(11, 0,  "SPRITE MULTIPLEXER");
    print_at(5,  24, "3 ROWS x 8 = 24 VIRTUAL SPRITES");
    init_spr();
    set_row(0);

    while (1) {
        // Aspetta raster prima di riga 0
        wait_raster(65);
        set_row(0);

        // Aspetta raster prima di riga 1
        wait_raster(125);
        set_row(1);

        // Aspetta raster prima di riga 2
        wait_raster(185);
        set_row(2);

        // Fine frame: aggiorna posizioni X
        wait_raster(240);
        byte i = 0;
        while (i < 8) {
            byte nx = COL_X[i] + COL_DX[i];
            if (nx > 244) { nx = 24; COL_DX[i] = 1; }
            if (nx < 24)  { nx = 24; COL_DX[i] = 1; }
            COL_X[i] = nx;
            i = i + 1;
        }
        // Anima colori riga per riga
        ROW_Y[0] = 70  + (ROW_Y[0] + 1) % 8;
    }
}
`,
sine_sprites: `// ─── Sine Wave Sprites ────────────────────────
// 8 sprite che seguono un'onda sinusoidale
// Tabella seno intera precalcolata (no float)
// 32 campioni, range Y 80-170

word VIC_SPE  = $D015;
word SPR_BASE = $3800;
word SPR_PTR0 = $07F8;

// Tabella seno: 32 campioni 0..360° → Y 80..170
byte SINTBL[32] = [
    125, 140, 153, 163, 170, 170, 163, 153,
    140, 125, 110,  97,  87,  80,  80,  87,
     97, 110, 125, 140, 153, 163, 170, 170,
    163, 153, 140, 125, 110,  97,  87,  80
];
// Fase iniziale sfasata di 4 step per sprite
byte PHASE[8]  = [0, 4, 8, 12, 16, 20, 24, 28];
// Colori arcobaleno
byte SCOL[8]   = [2, 8, 7, 5, 6, 3, 4, 14];
// X fisse distribuite sullo schermo
byte SPR_X[8]  = [32, 64, 96, 128, 160, 192, 224, 248];

func init_sine_spr() {
    byte k = 0;
    while (k < 64) { poke(SPR_BASE + k, 0); k = k + 1; }
    // Stella a 4 punte
    poke(SPR_BASE + 4,  $18);
    poke(SPR_BASE + 7,  $7E);
    poke(SPR_BASE + 10, $FF);
    poke(SPR_BASE + 13, $7E);
    poke(SPR_BASE + 16, $18);
    k = 0;
    while (k < 8) {
        poke(SPR_PTR0 + k, 224);
        poke($D027 + k, SCOL[k]);
        k = k + 1;
    }
    poke(VIC_SPE, $FF);
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(13, 0,  "SINE WAVE");
    print_at(8,  24, "8 SPRITES / SIN TABLE");
    init_sine_spr();

    byte t = 0;
    while (1) {
        byte i = 0;
        while (i < 8) {
            byte ph = (PHASE[i] + t) % 32;
            byte y  = SINTBL[ph];
            poke($D000 + i + i, SPR_X[i]);
            poke($D001 + i + i, y);
            // Cicla colori con offset temporale
            poke($D027 + i, SCOL[(i + t / 4) % 8]);
            i = i + 1;
        }
        border_color(t % 16);
        wait_frames(1);
        t = (t + 1) % 32;
    }
}
`,
pong: `// ─── PONG ─────────────────────────────────────
// Ball = sprite 0, Paddle = sprite 1 (Y doubled)
// Joystick porta 2 ($DC00): su/giù
// SID beep su rimbalzo/miss

word VIC_SPE  = $D015;
word VIC_SPYE = $D017;
word SPR_BALL = $3000;
word SPR_PDLE = $3040;
word SPR_PTR0 = $07F8;
word JOY2     = $DC00;
word SID_V1FL = $D400;
word SID_V1FH = $D401;
word SID_V1CR = $D404;
word SID_VOL  = $D418;

func beep(byte hi) {
    poke(SID_V1FL, 0); poke(SID_V1FH, hi);
    poke(SID_V1CR, $11); wait(3); poke(SID_V1CR, $10);
}

func init_pong() {
    // Pallina
    byte k = 0;
    while (k < 64) { poke(SPR_BALL + k, 0); k = k + 1; }
    poke(SPR_BALL + 4,  $3C);
    poke(SPR_BALL + 7,  $7E);
    poke(SPR_BALL + 10, $FF);
    poke(SPR_BALL + 13, $7E);
    poke(SPR_BALL + 16, $3C);

    // Paddle: azzera blocco poi barra verticale piena (3 byte per riga)
    k = 0;
    while (k < 64) { poke(SPR_PDLE + k, 0); k = k + 1; }
    k = 0;
    while (k < 21) {
        poke(SPR_PDLE + k * 3,     $FF);
        poke(SPR_PDLE + k * 3 + 1, $FF);
        poke(SPR_PDLE + k * 3 + 2, $FF);
        k = k + 1;
    }

    poke(SPR_PTR0,     192);  // ball  @ $3000
    poke(SPR_PTR0 + 1, 193);  // paddle @ $3040
    poke($D027, 7);            // ball: giallo
    poke($D028, 5);            // paddle: verde
    poke(VIC_SPYE, 2);        // Y-expand sprite 1 (paddle doppia altezza)
    poke(VIC_SPE, 3);         // abilita sprite 0 e 1
    poke(SID_VOL, $0F);
    poke($D002, 30);           // paddle X fissa
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(17, 0, "PONG");
    print_at(2,  1, "JOYSTICK PORTA 2 - SU/GIU");
    init_pong();

    byte bx  = 120;
    byte by  = 120;
    byte bdx = 2;
    byte bdy = 1;
    byte py  = 100;

    while (1) {
        // Leggi joystick
        byte joy = peek(JOY2);
        if ((joy & 1) == 0) { if (py < 210) { py = py + 3; } }
        if ((joy & 2) == 0) { if (py > 52)  { py = py - 3; } }

        // Muovi pallina
        bx = bx + bdx;
        by = by + bdy;

        // Rimbalzo su/giù (Y: 50..230)
        if (by < 50)  { by = 50;  bdy = 1;   beep($40); }
        if (by > 230) { by = 230; bdy = 255;  beep($40); }

        // Rimbalzo parete destra
        if (bx > 232) { bx = 232; bdx = 255; beep($20); }

        // Collisione paddle (sprite 1 è a X=30, alta 42px con Y-exp)
        if (bx < 50) {
            if (by >= py && by <= py + 42) {
                bdx = 2;
                beep($30);
            } else {
                // Mancato! Reset
                beep($08);
                bx = 120; by = 120;
                bdx = 2;  bdy = 1;
            }
        }

        // Aggiorna sprite
        poke($D000, bx);
        poke($D001, by);
        poke($D003, py);
        border_color((bx / 16) % 16);

        wait_frames(1);
    }
}
`,
irq_mplex: `// ─── IRQ Sprite Multiplexer ───────────────────
// Vero multiplexing via raster IRQ del VIC-II
// 3 righe × 8 sprite = 24 sprite virtuali
// Handler IRQ riposiziona gli 8 HW sprite prima
// del raster che li deve visualizzare.
// Sintassi: irq func name() { ... } → genera RTI

word VIC_SPE  = $D015;
word VIC_RAST = $D012;
word SPR_BASE = $3000;
word SPR_PTR0 = $07F8;

// Posizioni Y delle 3 righe raster
byte ROW_Y[3]    = [60, 130, 195];
// IRQ trigger: qualche riga prima di ogni gruppo
byte ROW_IRQ[3]  = [50, 120, 185];
// Posizioni X per le 8 colonne
byte COL_X[8]    = [24, 56, 88, 120, 152, 184, 216, 240];
// Velocità X per colonna (signed byte: >127 = negativo)
byte COL_DX[8]   = [1, 1, 2, 2, 255, 255, 254, 254];
// Colore per riga
byte ROW_COL[3]  = [10, 7, 2];
// Riga corrente servita dall'handler
byte IRQ_ROW     = 0;

// Handler IRQ raster unico — gestisce tutte e 3 le righe.
// Installato via set_irq_vector ($0314): KERNAL fa housekeeping
// una volta per IRQ, poi salta qui via JMP.
irq func raster_handler() {
    ack_raster_irq();
    byte y   = ROW_Y[IRQ_ROW];
    byte col = ROW_COL[IRQ_ROW];
    byte i   = 0;
    while (i < 8) {
        poke($D001 + i + i, y);
        poke($D000 + i + i, COL_X[i]);
        poke($D027 + i,     col);
        i = i + 1;
    }
    IRQ_ROW = (IRQ_ROW + 1) % 3;
    next_raster(ROW_IRQ[IRQ_ROW]);
}

func init_sprites() {
    byte k = 0;
    while (k < 64) { poke(SPR_BASE + k, 0); k = k + 1; }
    // Pallina
    poke(SPR_BASE +  1, $18);
    poke(SPR_BASE +  4, $3C);
    poke(SPR_BASE +  7, $7E);
    poke(SPR_BASE + 10, $FF);
    poke(SPR_BASE + 13, $FF);
    poke(SPR_BASE + 16, $7E);
    poke(SPR_BASE + 19, $3C);
    poke(SPR_BASE + 22, $18);
    k = 0;
    while (k < 8) { poke(SPR_PTR0 + k, 192); k = k + 1; }
    poke(VIC_SPE, $FF);
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(9,  1, "IRQ SPRITE MULTIPLEXER");
    print_at(5,  3, "3 ROWS x 8 = 24 VIRTUAL SPRITES");
    print_at(8,  5, "TRUE RASTER IRQ TECHNIQUE");

    init_sprites();
    IRQ_ROW = 0;

    // Installa handler e attiva IRQ raster alla prima riga trigger
    set_irq_vector(raster_handler);
    enable_raster_irq(ROW_IRQ[0]);

    // Main loop: anima le posizioni X fuori dall'IRQ
    while (1) {
        wait_frames(1);
        byte i = 0;
        while (i < 8) {
            byte nx  = COL_X[i] + COL_DX[i];
            byte spd = COL_DX[i];
            if (nx > 244) { COL_DX[i] = 255; nx = 244; }
            if (nx < 24)  { COL_DX[i] = 1;   nx = 24;  }
            COL_X[i] = nx;
            i = i + 1;
        }
        border_color(IRQ_ROW * 5);
    }
}
`,
// ────────────── FIXED-POINT EXAMPLES ──────────────────────────────────────
fpbasic: `// ─── Fixed-Point Q8.8 — Ciclo Colori ─────────────
// Tipo q8_8: 16 bit, 8 interi + 8 frazionari
//   1.0 = $0100 = 256     0.5 = $0080 = 128
//   VarDecl scala automaticamente:  q8_8 x = 1; → $0100
//   fp_int(x) → byte alto (parte intera 0-255)
//   fp_frac(x)→ byte basso (fraz. 0-255 = 0..0.996)
//   Somma q8_8 + q8_8 → 16-bit ADC diretto, carry incluso
//
// Demo: 2 contatori con velocita' sub-intere diverse.
// Velocita' in formato Q8.8 raw (hex = word grezzo, non scalato):
//   A = $0001 =  1/256 = 0.004 colori/frame (~256 frame/colore = ~4s)
//   B = $0003 =  3/256 = 0.012 colori/frame (~ 85 frame/colore = ~1.4s)

q8_8 cnt_a = 0;
q8_8 cnt_b = 0;

// Velocita' come costanti Q8.8 raw
q8_8 vel_a = 0;
q8_8 vel_b = 0;

func main() {
    clear_screen();
    screen_color(0);
    border_color(0);
    print_at(4, 10, "FIXED-POINT Q8.8 DEMO");
    print_at(3, 12, "BORDO:  1/256 = 0.004/FRAME");
    print_at(3, 13, "SFONDO: 3/256 = 0.012/FRAME");
    print_at(3, 15, "TIPO  Q8.8: 16 BIT, 8+8");
    print_at(3, 16, "INT  = FP.INT(X)  -> HI BYTE");
    print_at(3, 17, "FRAC = FP.FRAC(X) -> LO BYTE");

    // Velocita' in formato Q8.8 raw
    vel_a = $0001;   //  1/256 = 0.004 → 1 colore ogni 256 frame (~4s a 60fps)
    vel_b = $0003;   //  3/256 = 0.012 → 1 colore ogni  85 frame (~1.4s a 60fps)

    while (1) {
        cnt_a = cnt_a + vel_a;
        cnt_b = cnt_b + vel_b;

        // fp_int() estrae il byte alto = parte intera
        border_color(fp_int(cnt_a) % 16);
        screen_color(fp_int(cnt_b) % 16);

        wait_frames(1);
    }
}
`,

fpsmooth: `// ─── Smooth Sprite Q8.8 — Tipo Nativo ─────────────
// q8_8 : 16 bit  (hi=parte intera, lo=frazionaria)
// sq8_8: q8_8 con segno (velocita' direzionale)
//
// Posizione X/Y: tipo q8_8
//   fp_int(pos) → coordinata pixel da passare al VIC
// Velocita'  X/Y: valore Q8.8 raw
//   $0055 = 85/256 ≈ 0.33 px/frame
//   $0033 = 51/256 ≈ 0.20 px/frame
//
// L'addizione 16-bit include automaticamente il carry
// frazionario: sub-pixel si accumulano e overflow
// naturale propaga al byte intero. Stessa tecnica
// del 6510 ADC — ora espressa con tipi fp nativi!

word VIC_SPE  = $D015;
word SPR_BASE = $3800;
word SPR_PTR0 = $07F8;

q8_8 sx = 0;      // pos X in Q8.8
q8_8 sy = 0;      // pos Y in Q8.8
word vx  = 0;     // vel X raw Q8.8 ($0055 = 85/256 px/frame)
word vy  = 0;     // vel Y raw Q8.8 ($0033 = 51/256 px/frame)
byte dx  = 0;     // 0=destra  1=sinistra
byte dy  = 0;     // 0=giu'    1=su
byte col = 0;

func init_spr() {
    byte k = 0;
    while (k < 64) { poke(SPR_BASE + k, 0); k = k + 1; }
    poke(SPR_BASE +  4, $18);
    poke(SPR_BASE +  7, $7E);
    poke(SPR_BASE + 10, $FF);
    poke(SPR_BASE + 13, $FF);
    poke(SPR_BASE + 16, $7E);
    poke(SPR_BASE + 19, $18);
    poke(SPR_PTR0, 224);
    poke($D027, 7);
    poke(VIC_SPE, 1);
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(9, 0, "Q8.8 SMOOTH SPRITE");
    print_at(3, 1, "VX = $0055 = 85/256 PX/FRAME");
    print_at(3, 2, "VY = $0033 = 51/256 PX/FRAME");
    print_at(3, 3, "ADC 16-BIT: CARRY FRAZ AUTO");
    print_at(3, 4, "FP.INT(POS) = PIXEL VIC");
    init_spr();

    // Posizione iniziale in Q8.8 (120.0 e 130.0)
    sx = 120;
    sy = 130;
    // Velocita' raw Q8.8
    vx = $0055;   // 85/256 ≈ 0.33 px/frame
    vy = $0033;   // 51/256 ≈ 0.20 px/frame

    while (1) {
        // ─ Aggiorna posizione (16-bit ADC/SBC) ──────────
        if (dx == 0) {
            sx = sx + vx;
        } else {
            sx = sx - vx;
        }
        if (dy == 0) {
            sy = sy + vy;
        } else {
            sy = sy - vy;
        }

        // ─ Rimbalzo bordi (confronto sulla parte intera) ─
        if (fp_int(sx) > 230) { dx = 1; }
        if (fp_int(sx) < 28)  { dx = 0; }
        if (fp_int(sy) > 225) { dy = 1; }
        if (fp_int(sy) < 50)  { dy = 0; }

        // ─ Aggiorna sprite con coordinate intere ─────────
        poke($D000, fp_int(sx));
        poke($D001, fp_int(sy));
        col = (col + 1) % 15;
        poke($D027, col + 1);
        border_color(fp_int(sx) % 16);
        wait_frames(1);
    }
}
`,

fpgravity: `// ─── Fixed-Point SQ8.8: Fisica con Gravita' ──────
// Velocita' con segno: tipo sq8_8 (signed Q8.8)
//   vy > 0  → scende  (parte intera positiva)
//   vy < 0  → sale    (parte intera negativa)
//   vy = -vy → rimbalzo perfetto (negazione 16-bit)
//
// Gravita' = $0014 = 20/256 ≈ 0.078 px/frame^2
//   vy = vy + grav  →  sempre additivo, ogni frame
//   by = by + fp_int(vy) → muove di ±N pixel
//
// Il carry frazionario e' conservato in sq8_8:
//   le frazioni si accumulano, il pixel scatta quando
//   la parte intera cambia — fisicamente corretto!
//
// Rimbalzo: vy = -vy + damp  (anelastico: perde $0028/bounce ≈ 0.156 px/s)

word VIC_SPE  = $D015;
word SPR_BASE = $3C00;
word SPR_PTR0 = $07F8;

byte bx     = 120;
byte by     = 55;
sq8_8 vy    = 0;       // velocita' Y con segno in SQ8.8
sq8_8 grav  = $0014;   // gravita' = 20/256 px/frame^2 (raw)
byte bx_dir = 0;

func init_spr() {
    byte k = 0;
    while (k < 64) { poke(SPR_BASE + k, 0); k = k + 1; }
    poke(SPR_BASE +  1, $18);
    poke(SPR_BASE +  4, $3C);
    poke(SPR_BASE +  7, $7E);
    poke(SPR_BASE + 10, $FF);
    poke(SPR_BASE + 13, $7E);
    poke(SPR_BASE + 16, $3C);
    poke(SPR_BASE + 19, $18);
    poke(SPR_PTR0, 240);
    poke($D027, 7);
    poke(VIC_SPE, 1);
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(6, 0, "SQ8.8 GRAVITY DEMO");
    print_at(3, 1, "GRAV = $0014 = 20/256/FRAME^2");
    print_at(3, 2, "VY   = SQ8.8 (CON SEGNO)");
    print_at(3, 3, "CARRY FRAZ -> STEP INTERO AUTO");
    print_at(3, 4, "BOUNCE: VY = -VY (NEG 16-BIT)");
    init_spr();

    while (1) {
        // ─ Applica gravita' e muovi ───────────────────────
        // vy positiva = scende, vy negativa = sale
        // grav sempre sommata: accelera in caduta,
        // decelera in risalita, poi inverte naturalmente
        vy = vy + grav;
        by = by + fp_int(vy);

        // ─ Rimbalzo pavimento ─────────────────────────────
        if (by > 220) {
            by = 220;
            vy = -vy;              // complemento a due 16-bit
            vy = vy - (vy >> 2);  // coeff. restituzione 75%: |vy| *= 3/4
        }

        // ─ Rimbalzo soffitto ──────────────────────────────
        if (by < 50) {
            by = 50;
            vy = -vy;
            vy = vy - (vy >> 2);  // stesso coeff. restituzione
        }

        // ─ Moto orizzontale (1 px/frame) ──────────────────
        if (bx_dir == 0) { bx = bx + 1; } else { bx = bx - 1; }
        if (bx > 230) { bx_dir = 1; }
        if (bx < 28)  { bx_dir = 0; }

        poke($D000, bx);
        poke($D001, by);
        border_color(by % 16);
        wait_frames(1);
    }
}
`,



sidspr: `// ─── SID + Sprite ─────────────────────────────
// Sprite che rimbalza e suona una nota al rimbalzo

word VIC_S0X  = $D000;
word VIC_S0Y  = $D001;
word VIC_S0C  = $D027;
word VIC_SPR  = $D015;
word SPR0_PTR = $07F8;
word SPR_BASE = $3400;
word SID_V1FL = $D400;
word SID_V1FH = $D401;
word SID_V1CR = $D404;
word SID_V1AD = $D405;
word SID_V1SR = $D406;
word SID_VOL  = $D418;

// 8 note per gli 8 rimbalzi possibili (4 angoli x 2 assi)
byte HIT_LO[8] = [$65, $EB, $0F, $CA, $65, $EB, $0F, $CA];
byte HIT_HI[8] = [$11, $15, $1A, $22, $11, $15, $1A, $22];

func beep(byte idx) {
    poke(SID_V1FL, HIT_LO[idx]);
    poke(SID_V1FH, HIT_HI[idx]);
    poke(SID_V1CR, $81);      // noise + gate ON
    wait(4);
    poke(SID_V1CR, $80);      // gate OFF
}

func init_spr() {
    byte k = 0;
    while (k < 64) { poke(SPR_BASE + k, 0); k = k + 1; }
    poke(SPR_BASE +  1, $3C);
    poke(SPR_BASE +  4, $7E);
    poke(SPR_BASE +  7, $FF);
    poke(SPR_BASE + 10, $FF);
    poke(SPR_BASE + 13, $7E);
    poke(SPR_BASE + 16, $3C);
    poke(SPR0_PTR, 208);
    poke(VIC_SPR,  1);
    poke(SID_VOL,  $0F);
    poke(SID_V1AD, $00);
    poke(SID_V1SR, $F0);
}

func main() {
    clear_screen();
    border_color(0);
    screen_color(0);
    print_at(12, 12, "SID + SPRITE");

    init_spr();

    byte x    = 80;
    byte y    = 80;
    byte dirx = 0;
    byte diry = 0;
    byte note = 0;

    while (1) {
        poke(VIC_S0C, note + 1);
        poke(VIC_S0X, x);
        poke(VIC_S0Y, y);
        wait_frames(1);

        byte hit = 0;
        if (x > 228) { dirx = 1; hit = 1; }
        if (x < 28)  { dirx = 0; hit = 1; }
        if (y > 224) { diry = 1; hit = 1; }
        if (y < 50)  { diry = 0; hit = 1; }
        if (hit == 1) {
            border_color(note + 2);
            beep(note);
            note = (note + 1) % 8;
        }

        if (dirx == 0) { x = x + 2; }
        if (dirx == 1) { x = x - 2; }
        if (diry == 0) { y = y + 1; }
        if (diry == 1) { y = y - 1; }
    }
}
`
};


# ------------------------------------------------------------------------------
# QRCODE GENERATOR FROM SCRATCH (V1 - V40) + CUSTOM RENDER
# 
# PURPOSE: A fully independent QR Code generator. Zero external dependencies 
#          for data encoding, error correction, or matrix generation.
# 
# WHY:     To demonstrate total mastery over the ISO/IEC 18004 specification.
#          This is a ground-up implementation of the entire QR Code standard,
#          including all 40 versions, Level M (Medium) error correction,
#          and the complex Block Interleaving and masking processes.
#
# HOW:     Implements Galois Field GF(2^8) arithmetic, Reed-Solomon 
#          polynomial division, dynamic geometric scaling (up to 177x177 px), 
#          XOR masking, and format string calculation purely in Python.
#          Includes built-in Raster and Vector (SVG) renderers.
# ------------------------------------------------------------------------------

from PIL import Image, ImageDraw, ImageColor, ImageTk
import math
import random
import customtkinter as ctk
from tkinter import messagebox, filedialog

# UI Configuration
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 
APPLE_FONT = "SF Pro Display"


# 1. Qrcode_math using Galois Field GF(2^8) and Reed-Solomon encoding
# Pre-computed Galois Field tables
EXP_TABLE = [1] * 512
LOG_TABLE = [0] * 256
x = 1
for i in range(1, 255):
    x <<= 1
    if x & 0x100: x ^= 0x11D
    EXP_TABLE[i] = x
    LOG_TABLE[x] = i
for i in range(255, 512): EXP_TABLE[i] = EXP_TABLE[i - 255]

# ISO Alignment Patterns Center Coordinates
ALIGNMENTS = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42],
    9: [6, 26, 46], 10: [6, 28, 50], 11: [6, 30, 54], 12: [6, 32, 58], 13: [6, 34, 62], 14: [6, 26, 46, 66],
    15: [6, 26, 48, 70], 16: [6, 26, 50, 74], 17: [6, 30, 54, 78], 18: [6, 30, 56, 82], 19: [6, 30, 58, 86],
    20: [6, 34, 62, 90], 21: [6, 28, 50, 72, 94], 22: [6, 26, 50, 74, 98], 23: [6, 30, 54, 78, 102],
    24: [6, 28, 54, 80, 106], 25: [6, 32, 58, 84, 110], 26: [6, 30, 58, 86, 114], 27: [6, 34, 62, 90, 118],
    28: [6, 26, 50, 74, 98, 122], 29: [6, 30, 54, 78, 102, 126], 30: [6, 26, 52, 78, 104, 130],
    31: [6, 30, 56, 82, 108, 134], 32: [6, 34, 60, 86, 112, 138], 33: [6, 30, 58, 86, 114, 142],
    34: [6, 34, 62, 90, 118, 146], 35: [6, 30, 54, 78, 102, 126, 150], 36: [6, 24, 50, 76, 102, 128, 154],
    37: [6, 28, 54, 80, 106, 132, 158], 38: [6, 32, 58, 84, 110, 136, 162], 39: [6, 26, 54, 82, 110, 138, 166],
    40: [6, 30, 58, 86, 114, 142, 170]
}

# ISO Capacity Level M (Data, EC, G1_Blocks, G1_Data, G2_Blocks, G2_Data)
CAP_M = {
    1: (16, 10, 1, 16, 0, 0), 2: (28, 16, 1, 28, 0, 0), 3: (44, 26, 1, 44, 0, 0), 4: (64, 36, 2, 32, 0, 0),
    5: (86, 48, 2, 43, 0, 0), 6: (108, 64, 4, 27, 0, 0), 7: (130, 72, 4, 31, 0, 0), 8: (152, 88, 2, 38, 2, 39),
    9: (192, 110, 3, 36, 2, 37), 10: (224, 130, 4, 43, 1, 44), 11: (274, 150, 1, 50, 4, 51), 12: (322, 176, 6, 54, 2, 55),
    13: (368, 198, 8, 46, 1, 47), 14: (428, 216, 4, 50, 5, 51), 15: (460, 240, 5, 54, 5, 55), 16: (534, 280, 7, 43, 3, 44),
    17: (586, 308, 10, 45, 1, 46), 18: (644, 338, 9, 50, 4, 51), 19: (718, 364, 3, 54, 11, 55), 20: (792, 416, 3, 39, 13, 40),
    21: (858, 442, 17, 46, 0, 0), 22: (928, 476, 17, 50, 0, 0), 23: (1002, 504, 15, 54, 2, 55), 24: (1090, 560, 17, 43, 4, 44),
    25: (1170, 588, 11, 50, 11, 51), 26: (1272, 644, 11, 54, 12, 55), 27: (1366, 700, 7, 46, 18, 47), 28: (1464, 728, 22, 50, 4, 51),
    29: (1528, 784, 21, 54, 7, 55), 30: (1628, 812, 19, 53, 10, 54), 31: (1732, 868, 2, 54, 29, 55), 32: (1840, 924, 24, 54, 10, 55),
    33: (1952, 980, 28, 54, 10, 55), 34: (2068, 1036, 33, 54, 7, 55), 35: (2188, 1064, 16, 54, 26, 55), 36: (2302, 1120, 34, 54, 10, 55),
    37: (2430, 1204, 20, 54, 27, 55), 38: (2562, 1260, 17, 54, 34, 55), 39: (2698, 1316, 17, 54, 38, 55), 40: (2808, 1372, 19, 54, 38, 55)
}

# Pre-calculated Format (M-0) and Version Information strings (BCH Error Correction)
FMT_STR = "101010000010010"
V_INFO = { 7: "000111110010010100", 
           8: "001000010110111100", 
           9: "001001101010011001", 
          10: "001010010011010011", 
          11: "001011101111110110", 
          12: "001100011101100010", 
          13: "001101100001000111", 
          14: "001110011000001101", 
          15: "001111100100101000", 
          16: "010000101101111000", 
          17: "010001010001011101", 
          18: "010010101000010111", 
          19: "010011010100110010", 
          20: "010100100110100110", 
          21: "010101011010000011", 
          22: "010110100011001001", 
          23: "010111011111101100", 
          24: "011000111011000100", 
          25: "011001000111100001", 
          26: "011010111110101011", 
          27: "011011000010001110", 
          28: "011100110000011010", 
          29: "011101001100111111", 
          30: "011110110101110101", 
          31: "011111001001010000", 
          32: "100000100111010101", 
          33: "100001011011110000", 
          34: "100010100010111010", 
          35: "100011011110011111", 
          36: "100100101100001011", 
          37: "100101010000101110", 
          38: "100110101001100100", 
          39: "100111010101000001", 
          40: "101000110000110100"}

def poly_mul(p1, p2):
    """Galois Field polynomial multiplication."""
    res = [0] * (len(p1) + len(p2) - 1)
    for i, c1 in enumerate(p1):
        for j, c2 in enumerate(p2):
            if c1 and c2: res[i + j] ^= EXP_TABLE[LOG_TABLE[c1] + LOG_TABLE[c2]]
    return res

def poly_div(msg, gen):
    """Galois Field polynomial division to extract Parity Bytes."""
    msg_out = list(msg) + [0] * (len(gen) - 1)
    for i in range(len(msg)):
        coef = msg_out[i]
        if coef:
            for j in range(1, len(gen)):
                if gen[j]: msg_out[i + j] ^= EXP_TABLE[LOG_TABLE[coef] + LOG_TABLE[gen[j]]]
    return msg_out[len(msg):]

def universal_encode(text):
    """Analyzes text length, scales the version, encodes to bits, and computes RS blocks."""
    v = 1
    # Determine minimum required version (Byte Mode)
    for i in range(1, 41):
        len_bits = 8 if i < 10 else 16
        header_bits = 4 + len_bits
        data_bits = len(text) * 8
        if header_bits + data_bits <= CAP_M[i][0] * 8:
            v = i; break
    else: raise ValueError("Payload exceeds V40-M capacity.")

    cap = CAP_M[v]
    len_bits = 8 if v < 10 else 16
    bitstream = "0100" + format(len(text), f"0{len_bits}b")
    for char in text: bitstream += f"{ord(char):08b}"
    
    cap_bits = cap[0] * 8
    missing_bits = cap_bits - len(bitstream)
    if missing_bits > 0: bitstream += "0" * min(4, missing_bits)
    while len(bitstream) % 8 != 0: bitstream += "0"
    
    pads = ["11101100", "00010001"]
    pidx = 0
    while len(bitstream) < cap_bits: bitstream += pads[pidx % 2]; pidx += 1
    data_bytes = [int(bitstream[i:i+8], 2) for i in range(0, len(bitstream), 8)]

    # Complex Block Interleaving execution
    b1, d1, b2, d2 = cap[2], cap[3], cap[4], cap[5]
    ec_per_block = cap[1] // (b1 + b2)
    
    data_blocks = []
    idx = 0
    for _ in range(b1): data_blocks.append(data_bytes[idx : idx+d1]); idx += d1
    for _ in range(b2): data_blocks.append(data_bytes[idx : idx+d2]); idx += d2

    gen = [1]
    for i in range(ec_per_block): gen = poly_mul(gen, [1, EXP_TABLE[i]])
    
    ec_blocks = [poly_div(blk, gen) for blk in data_blocks]
    
    interleaved = []
    max_d = max(d1, d2) if b2 > 0 else d1
    for i in range(max_d):
        for b in range(b1 + b2):
            if i < len(data_blocks[b]): interleaved.append(data_blocks[b][i])
    for i in range(ec_per_block):
        for b in range(b1 + b2): interleaved.append(ec_blocks[b][i])
        
    return "".join([f"{b:08b}" for b in interleaved]), v

def build_skeleton(version):
    """Constructs the spatial matrix and reserves critical ISO structures."""
    dim = 21 + 4 * (version - 1)
    mat = [[None]*dim for _ in range(dim)]
    
    def draw_box(rs, cs, s):
        for r in range(s):
            for c in range(s):
                if r==0 or r==s-1 or c==0 or c==s-1 or (2<=r<=s-3 and 2<=c<=s-3): mat[rs+r][cs+c] = 1
                else: mat[rs+r][cs+c] = 0

    draw_box(0, 0, 7); draw_box(0, dim-7, 7); draw_box(dim-7, 0, 7)
    for i in range(8):
        if i<8: mat[7][i] = mat[i][7] = 0
        if i<8: mat[7][dim-8+i] = mat[i][dim-8] = 0
        if i<8: mat[dim-8][i] = mat[dim-8+i][7] = 0
    for i in range(8, dim-8): mat[6][i] = mat[i][6] = 1 if i%2==0 else 0
    mat[dim-8][8] = 1

    cents = ALIGNMENTS[version]
    for rc in cents:
        for cc in cents:
            if (rc<10 and cc<10) or (rc<10 and cc>dim-10) or (rc>dim-10 and cc<10): continue
            for r in range(-2, 3):
                for c in range(-2, 3):
                    mat[rc+r][cc+c] = 1 if (r==-2 or r==2 or c==-2 or c==2 or (r==0 and c==0)) else 0

    for i in range(9):
        if mat[8][i] is None: mat[8][i] = -1
        if mat[i][8] is None: mat[i][8] = -1
    for i in range(dim-8, dim):
        if mat[8][i] is None: mat[8][i] = -1
        if mat[i][8] is None: mat[i][8] = -1

    if version >= 7:
        for r in range(6):
            for c in range(3): mat[dim-11+c][r] = mat[r][dim-11+c] = -2
    return mat, dim

def inject_data(mat, bs, dim, v):
    """Serpentines the bitstream into the matrix, applying XOR Mask 0."""
    r, c, up, bi, L = dim-1, dim-1, True, 0, len(bs)
    while c > 0:
        if c == 6: c -= 1
        for _ in range(2):
            if mat[r][c] is None:
                bit = int(bs[bi]) if bi < L else 0
                if bi < L: bi += 1
                mat[r][c] = bit ^ 1 if ((r + c) % 2 == 0) else bit # XOR Mask 0 application
            c -= 1
        c += 2
        if up:
            r -= 1
            if r < 0: r = 0; up = False; c -= 2
        else:
            r += 1
            if r >= dim: r = dim-1; up = True; c -= 2

    # Stamp Format and Version blocks over reserved areas
    c1 = [(8,0),(8,1),(8,2),(8,3),(8,4),(8,5),(8,7),(8,8),(7,8),(5,8),(4,8),(3,8),(2,8),(1,8),(0,8)]
    c2 = [(dim-1,8),(dim-2,8),(dim-3,8),(dim-4,8),(dim-5,8),(dim-6,8),(dim-7,8),(8,dim-8),(8,dim-7),(8,dim-6),(8,dim-5),(8,dim-4),(8,dim-3),(8,dim-2),(8,dim-1)]
    for i, b in enumerate(FMT_STR):
        mat[c1[i][0]][c1[i][1]] = int(b); mat[c2[i][0]][c2[i][1]] = int(b)
        
    if v >= 7:
        v_str = V_INFO[v][::-1] 
        idx = 0
        for cc in range(3):
            for rr in range(6):
                mat[dim-11+cc][rr] = int(v_str[idx]); mat[rr][dim-11+cc] = int(v_str[idx])
                idx += 1
    return mat


# 2.(PILLOW)
def apply_raster_badge(img, bg):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    pad = int(img.size[0] * 0.2); sz = img.size[0] + pad*2
    b = Image.new('RGBA', (sz, sz), (0,0,0,0))
    ImageDraw.Draw(b).ellipse((0,0,sz,sz), fill=bg+(255,))
    l = Image.new('RGBA', (sz, sz), (0,0,0,0)); l.paste(img, (pad, pad))
    return Image.alpha_composite(b, l)

def apply_raster_camo(img, bs, fg, bg, is_circ=False):
    if img.mode != 'RGBA': img = img.convert('RGBA')
    mq = img.size[0] // bs
    md = math.ceil(mq * math.sqrt(2)); md += 1 if md%2 != mq%2 else 0
    sz = md * bs; r = sz // 2
    cv = Image.new('RGBA', (sz, sz), (0,0,0,0)); d = ImageDraw.Draw(cv)
    for row in range(md):
        for col in range(md):
            cx, cy = col*bs + bs/2, row*bs + bs/2
            if math.sqrt((cx-r)**2 + (cy-r)**2) <= r:
                c = fg+(255,) if random.random()>0.5 else bg+(255,)
                if is_circ: d.ellipse([col*bs, row*bs, col*bs+bs, row*bs+bs], fill=c)
                else: d.rectangle([col*bs, row*bs, col*bs+bs, row*bs+bs], fill=c)
    qm = Image.alpha_composite(Image.new("RGBA", img.size, bg+(255,)), img)
    off = (sz - img.size[0]) // 2
    lm = Image.new('RGBA', (sz, sz), (0,0,0,0)); lm.paste(qm, (off, off))
    cv = Image.alpha_composite(cv, lm)
    mk = Image.new('L', (sz, sz), 0); ImageDraw.Draw(mk).ellipse((0,0,sz,sz), fill=255)
    f = Image.new('RGBA', (sz, sz), (0,0,0,0)); f.paste(cv, (0,0), mk)
    return f

# 3.USER INTERFACE
class EngineAbsoluteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QR Studio PRO - Advanced QR Code Generator")
        self.geometry("950x650")
        self.resizable(False, False)
        
        self.data_var = ctk.StringVar(value="https://github.com")
        self.f_var, self.b_var = ctk.StringVar(value="#000000"), ctk.StringVar(value="#FFFFFF")
        self.fmt_var, self.shp_var, self.lay_var = ctk.StringVar(value="PNG"), ctk.StringVar(value="Cerchio"), ctk.StringVar(value="Camouflage Circolare")
        self.matrix, self.img_gen, self.svg_str, self.after_id = [], None, "", None
        
        self.create_ui()
        for v in [self.data_var, self.f_var, self.b_var, self.fmt_var, self.shp_var, self.lay_var]: v.trace_add("write", self.update_trig)
        self.render()

    def create_ui(self):
        L, R = ctk.CTkFrame(self, width=400, fg_color="transparent"), ctk.CTkFrame(self, fg_color=("gray90", "gray12"), corner_radius=15)
        L.pack(side="left", fill="y", padx=20, pady=20); R.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(L, text="QR Studio", font=ctk.CTkFont(family=APPLE_FONT, size=32, weight="bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(L, text="GF(2^8) Block Interleaving Active.", text_color="#10b981", font=ctk.CTkFont(family=APPLE_FONT, size=12, weight="bold")).pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(L, text="ISO Payload (Max ~2800 char)", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(5, 5))
        ctk.CTkEntry(L, textvariable=self.data_var, width=330, height=40, corner_radius=8).pack(anchor="w")

        ctk.CTkLabel(L, text="Colors", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(15, 5))
        cf = ctk.CTkFrame(L, fg_color="transparent"); cf.pack(anchor="w", fill="x")
        self.bf = ctk.CTkButton(cf, text="Pixel", width=160, height=35, fg_color=self.f_var.get(), command=lambda: self.pick_color(self.f_var, self.bf)); self.bf.pack(side="left", padx=(0, 10))
        self.bb = ctk.CTkButton(cf, text="Background", width=160, height=35, fg_color=self.b_var.get(), text_color="black", command=lambda: self.pick_color(self.b_var, self.bb)); self.bb.pack(side="left")

        ctk.CTkLabel(L, text="Export Format", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkOptionMenu(L, variable=self.fmt_var, values=["PNG", "JPG", "SVG"], width=330, height=35).pack(anchor="w")
        ctk.CTkLabel(L, text="Module Style", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkSegmentedButton(L, variable=self.shp_var, values=["Quadrato", "Cerchio"], width=330).pack(anchor="w")
        ctk.CTkLabel(L, text="External Layout", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkOptionMenu(L, variable=self.lay_var, values=["Standard", "Badge Circolare", "Camouflage Circolare"], width=330, height=35).pack(anchor="w")

        ctk.CTkLabel(R, text="Live Render", font=ctk.CTkFont(family=APPLE_FONT, size=20, weight="bold")).pack(pady=(20, 10))
        self.lbl_prev = ctk.CTkLabel(R, text=""); self.lbl_prev.pack(pady=10, expand=True)
        self.lbl_diag = ctk.CTkLabel(R, text="", text_color="#ef4444", font=ctk.CTkFont(family=APPLE_FONT, size=12, weight="bold")); self.lbl_diag.pack(pady=5)
        self.btn_s = ctk.CTkButton(R, text="Export", font=ctk.CTkFont(family=APPLE_FONT, size=16, weight="bold"), fg_color="#10b981", hover_color="#059669", height=50, corner_radius=25, command=self.save_export); self.btn_s.pack(fill="x", padx=40, pady=(10, 30))

    def pick_color(self, vt, bt):
        p = ctk.CTkToplevel(self); p.title("Color"); p.geometry("260x360"); p.attributes("-topmost", True); p.grab_set()
        ctk.CTkLabel(p, text="Palette", font=ctk.CTkFont(family=APPLE_FONT, size=16, weight="bold")).pack(pady=(15, 10))
        gf = ctk.CTkFrame(p, fg_color="transparent"); gf.pack(padx=20, pady=5)
        cols = ["#FF3B30", "#FF9500", "#FFCC00", "#34C759", "#5AC8FA", "#007AFF", "#5856D6", "#AF52DE", "#FF2D55", "#000000", "#FFFFFF", "#8E8E93", "#1C1C1E", "#3A3A3C", "#F2F2F7", "#059669"]
        def s(c): 
            vt.set(c); bt.configure(fg_color=c)
            try: bt.configure(text_color="white" if sum(a*b for a,b in zip(ImageColor.getrgb(c), [299,587,114]))/1000 < 128 else "black")
            except: pass
            p.destroy()
        for i, c in enumerate(cols):
            b = ctk.CTkButton(gf, text="", width=40, height=40, fg_color=c, corner_radius=8, command=lambda c=c: s(c)); b.grid(row=i//4, column=i%4, padx=5, pady=5)
            if c in ["#FFFFFF", "#F2F2F7"]: b.configure(border_width=1, border_color="#D1D1D6")
        v = ctk.StringVar(value=vt.get())
        ctk.CTkEntry(p, textvariable=v, width=150, justify="center").pack(pady=15)
        ctk.CTkButton(p, text="Apply", command=lambda: [s(v.get()) if v.get().startswith("#") else None]).pack()

    def update_trig(self, *a):
        if self.after_id: self.after_cancel(self.after_id)
        self.after_id = self.after(500, self.render) 

    def render(self):
        data = self.data_var.get().strip()
        if not data:
            self.lbl_diag.configure(text="Enter data."); self.lbl_prev.configure(image=""); self.btn_s.configure(state="disabled"); return
        try:
            fh, bh = self.f_var.get(), self.b_var.get()
            fr, br = ImageColor.getrgb(fh), ImageColor.getrgb(bh)
            if sum(a*b for a,b in zip(fr, [299,587,114])) == sum(a*b for a,b in zip(br, [299,587,114])): raise ValueError
        except: self.lbl_diag.configure(text="Invalid colors."); return
        
        try: bs, v = universal_encode(data)
        except ValueError as e: self.lbl_diag.configure(text=str(e)); return
        self.lbl_diag.configure(text=f"GF(2^8) Core OK. [V{v}-M] | Matrix: {21+4*(v-1)}x{21+4*(v-1)}", text_color="#10b981")
        
        mb, d = build_skeleton(v); self.matrix = inject_data(mb, bs, d, v)
        b_sz, bdr = min(15, 500//d), 3
        iw = ih = (d + 2*bdr) * b_sz
        isc, l, fmt = self.shp_var.get() == "Cerchio", self.lay_var.get(), self.fmt_var.get()

        if fmt == "SVG":
            se = []
            if l == "Camouflage Circolare":
                mq = d + 2*bdr; md = math.ceil(mq * math.sqrt(2)); md += 1 if md%2 != mq%2 else 0
                ts = md * b_sz; rad = ts / 2; op = ((md - mq) // 2) * b_sz
                se.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{ts}" height="{ts}"><defs><clipPath id="c"><circle cx="{rad}" cy="{rad}" r="{rad}"/></clipPath></defs><rect width="{ts}" height="{ts}" fill="{bh}" clip-path="url(#c)"/><g clip-path="url(#c)">')
                for r in range(md):
                    for c in range(md):
                        if (op//b_sz) <= r < (op//b_sz)+mq and (op//b_sz) <= c < (op//b_sz)+mq: continue
                        if math.sqrt(((c*b_sz+b_sz/2)-rad)**2 + ((r*b_sz+b_sz/2)-rad)**2) <= rad and random.random()>0.5:
                            se.append(f'<circle cx="{c*b_sz+b_sz/2}" cy="{r*b_sz+b_sz/2}" r="{b_sz/2}" fill="{fh}"/>' if isc else f'<rect x="{c*b_sz}" y="{r*b_sz}" width="{b_sz}" height="{b_sz}" fill="{fh}"/>')
                se.append(f'<rect x="{op}" y="{op}" width="{iw}" height="{ih}" fill="{bh}"/>')
                for r, row in enumerate(self.matrix):
                    for c, val in enumerate(row):
                        if val == 1:
                            x, y = (c+bdr)*b_sz+op, (r+bdr)*b_sz+op
                            se.append(f'<circle cx="{x+b_sz/2}" cy="{y+b_sz/2}" r="{b_sz/2}" fill="{fh}"/>' if isc else f'<rect x="{x}" y="{y}" width="{b_sz}" height="{b_sz}" fill="{fh}"/>')
                se.append('</g></svg>')
            else:
                pad = int(iw * 0.2) if l == "Badge Circolare" else 0
                ts = iw + pad*2
                se.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{ts}" height="{ts}">')
                if l == "Badge Circolare": se.append(f'<circle cx="{ts/2}" cy="{ts/2}" r="{ts/2}" fill="{bh}"/>')
                else: se.append(f'<rect width="{ts}" height="{ts}" fill="{bh}"/>')
                for r, row in enumerate(self.matrix):
                    for c, val in enumerate(row):
                        if val == 1:
                            x, y = (c+bdr)*b_sz+pad, (r+bdr)*b_sz+pad
                            se.append(f'<circle cx="{x+b_sz/2}" cy="{y+b_sz/2}" r="{b_sz/2}" fill="{fh}"/>' if isc else f'<rect x="{x}" y="{y}" width="{b_sz}" height="{b_sz}" fill="{fh}"/>')
                se.append('</svg>')
            self.svg_str = "".join(se)
        
        ib = Image.new("RGBA", (iw, ih), br+(255,))
        dw = ImageDraw.Draw(ib)
        for r, row in enumerate(self.matrix):
            for c, val in enumerate(row):
                if val == 1:
                    x, y = (c+bdr)*b_sz, (r+bdr)*b_sz
                    if isc: dw.ellipse([x, y, x+b_sz, y+b_sz], fill=fr+(255,))
                    else: dw.rectangle([x, y, x+b_sz, y+b_sz], fill=fr+(255,))
        if l == "Badge Circolare": self.img_gen = apply_raster_badge(ib, br)
        elif l == "Camouflage Circolare": self.img_gen = apply_raster_camo(ib, b_sz, fr, br, isc)
        else: self.img_gen = ib

        img_disp = self.img_gen.copy()
        c_img = ctk.CTkImage(light_image=img_disp, dark_image=img_disp, size=(380, 380))
        self.lbl_prev.configure(image=c_img); self.lbl_prev.image = c_img
        self.btn_s.configure(state="normal")

    def save_export(self):
        f = self.fmt_var.get()
        p = filedialog.asksaveasfilename(defaultextension=f".{f.lower()}", initialfile=f"qr_code.{f.lower()}")
        if p:
            if f == "SVG": open(p, "w", encoding="utf-8").write(self.svg_str)
            elif f == "JPG":
                bg = Image.new("RGB", self.img_gen.size, ImageColor.getrgb(self.b_var.get()))
                bg.paste(self.img_gen, (0,0), self.img_gen if self.img_gen.mode=='RGBA' else None); bg.save(p, "JPEG")
            else: self.img_gen.save(p, "PNG")
            messagebox.showinfo("Export", f"Generated: {p}")

if __name__ == "__main__":
    EngineAbsoluteApp().mainloop()
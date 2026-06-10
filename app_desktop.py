"""HandLingo v5 — Screenshot-matched UI"""
import os, sys, json, random, threading, math
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import torch, torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH     = os.path.join(BASE_DIR, "HandLingo.pth")
CLASS_NAMES_PATH = os.path.join(BASE_DIR, "class_names.json")
CONFIG_PATH    = os.path.join(BASE_DIR, "config.json")
ASL_DIR        = r"C:\Users\Lenovo\OneDrive\Masaüstü\asl_alphabet"

BG      = "#161514"
PANEL   = "#1c1b1a"
CARD_BG = "#222120"
CARD_HL = "#2c2b2a"
GREEN   = "#4caf50"
TEAL    = "#4db6ac"
COPPER  = "#d99d82"
PURPLE  = "#d99d82"
MAGENTA = "#d99d82"
ORANGE  = "#d99d82"
RED     = "#e53935"
WHITE   = "#ffffff"
GRAY    = "#a0a0a0"
GRAY2   = "#3c3a38"
GRAY3   = "#504e4c"
GOLD    = "#fbc02d"

THUMB   = 66
DROP_IMG = 140
DZ_W, DZ_H = 620, 260

class Model:
    def __init__(self):
        self.model = None; self.names = []; self.tf = None
        self.dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load()

    def _load(self):
        self.names = json.load(open(CLASS_NAMES_PATH)) if os.path.exists(CLASS_NAMES_PATH) else [chr(65+i) for i in range(26)]
        cfg = json.load(open(CONFIG_PATH)) if os.path.exists(CONFIG_PATH) else {}
        sz, nc = cfg.get("image_size", 224), cfg.get("num_classes", len(self.names))
        self.tf = transforms.Compose([transforms.Resize((sz,sz)), transforms.ToTensor(),
                                       transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
        if os.path.exists(MODEL_PATH):
            try:
                self.model = models.mobilenet_v2(weights=None)
                self.model.classifier[1] = nn.Linear(self.model.classifier[1].in_features, nc)
                self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.dev, weights_only=False))
                self.model.to(self.dev).eval()
                print(f"[OK] Model OK — {nc} sınıf, {self.dev}")
            except Exception as e:
                print(f"[ERR] {e}"); self.model = None

    def predict(self, path):
        if not self.model: return ("?", 0.0)
        try:
            img = Image.open(path).convert("RGB")
            t = self.tf(img).unsqueeze(0).to(self.dev)
            with torch.no_grad():
                p = torch.softmax(self.model(t), 1)
                c, i = torch.max(p, 1)
            i = i.item()
            return (self.names[i] if i < len(self.names) else "?", c.item())
        except: return ("?", 0.0)

def load_samples():
    samples = {}
    if not os.path.isdir(ASL_DIR): print(f"⚠ ASL bulunamadı: {ASL_DIR}"); return samples
    for d in sorted(os.listdir(ASL_DIR)):
        fp = os.path.join(ASL_DIR, d)
        if not os.path.isdir(fp): continue
        imgs = [f for f in os.listdir(fp) if f.lower().endswith((".jpg",".jpeg",".png"))]
        if imgs: samples[d] = os.path.join(fp, random.choice(imgs))
    print(f"[OK] {len(samples)} harf"); return samples

def hex2rgb(h): return (int(h[1:3],16), int(h[3:5],16), int(h[5:7],16))
def lighten(h, a=30): return f"#{min(255,max(0,int(h[1:3],16)+a)):02x}{min(255,max(0,int(h[3:5],16)+a)):02x}{min(255,max(0,int(h[5:7],16)+a)):02x}"

def make_thumb(path, size, radius, bg):
    img = Image.open(path).convert("RGB").resize((size,size), Image.LANCZOS)
    mask = Image.new("L",(size,size),0)
    ImageDraw.Draw(mask).rounded_rectangle([0,0,size-1,size-1], radius, fill=255)
    out = Image.new("RGB",(size,size), hex2rgb(bg))
    out.paste(img, mask=mask); return out

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HandLingo")
        self.root.geometry("1240x780")
        self.root.minsize(1000, 700)
        self.root.configure(bg=BG)
        try:
            self.root.update()
            from ctypes import windll, byref, c_int, sizeof
            windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(self.root.winfo_id()), 20, byref(c_int(2)), sizeof(c_int))
        except: pass

        self.sentence=[]; self.model=Model(); self.samples=load_samples()
        self.paths={}; self.dragging=False; self.drag_widget=None
        self.drag_letter=None; self._drop_photo=None; self._card_photos={}
        
        try:
            from PIL import ImageFont
            img = Image.new("RGBA", (64,64), (0,0,0,0))
            d = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("seguiemj.ttf", 40)
            except: font = None
            d.text((12, 5), "✋", font=font, fill=hex2rgb(COPPER))
            self.icon_photo = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, self.icon_photo)
        except: pass

        self._build(); self._fill_cards()

    def _build(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self._build_left()
        self._build_right()

    def _build_left(self):
        left = tk.Frame(self.root, bg=PANEL, width=260)
        left.grid(row=0, column=0, sticky="ns")
        left.grid_propagate(False)

        # Logo
        logo = tk.Frame(left, bg=PANEL)
        logo.pack(fill="x", padx=20, pady=(24,0))
        tk.Label(logo, text="✋", font=("Segoe UI",20), fg=COPPER, bg=PANEL).pack(side="left")
        lt = tk.Frame(logo, bg=PANEL)
        lt.pack(side="left", padx=(8,0))
        tk.Label(lt, text="HandLingo", font=("Segoe UI",12,"bold"), fg=WHITE, bg=PANEL).pack(anchor="w")
        tk.Label(lt, text="AI Destekli İşaret Dili Tercümanı", font=("Segoe UI",7), fg=GRAY, bg=PANEL).pack(anchor="w")

        tk.Frame(left, bg=GRAY2, height=1).pack(fill="x", padx=20, pady=(16,12))

        # Section header
        sh = tk.Frame(left, bg=PANEL)
        sh.pack(fill="x", padx=20)
        sh_top = tk.Frame(sh, bg=PANEL)
        sh_top.pack(anchor="w")
        tk.Label(sh_top, text="●", font=("Segoe UI",8), fg=COPPER, bg=PANEL).pack(side="left", pady=(2,0))
        tk.Label(sh_top, text="  İŞARET DİLİ", font=("Segoe UI",9,"bold"), fg=WHITE, bg=PANEL).pack(side="left")
        tk.Label(sh, text="Harfi sürükleyip sağa bırakın →", font=("Segoe UI",8), fg=GRAY, bg=PANEL).pack(anchor="w", pady=(4,0))

        # Search + filter
        sf = tk.Frame(left, bg=PANEL)
        sf.pack(fill="x", padx=16, pady=(12,8))
        se = tk.Frame(sf, bg=CARD_BG, highlightbackground=GRAY2, highlightthickness=1)
        se.pack(side="left", fill="x", expand=True)
        tk.Label(se, text="🔍", font=("Segoe UI",9), bg=CARD_BG, fg=GRAY).pack(side="left", padx=(8,0))
        tk.Label(se, text="Harf ara...", font=("Segoe UI",8), fg=GRAY, bg=CARD_BG).pack(side="left", padx=4, pady=6)
        fb = tk.Frame(sf, bg=CARD_BG, highlightbackground=GRAY2, highlightthickness=1)
        fb.pack(side="left", padx=(8,0))
        tk.Label(fb, text="▼ Tümü", font=("Segoe UI",8), fg=GRAY, bg=CARD_BG, padx=10, pady=6).pack()

        # Tabs at bottom
        tabs = tk.Frame(left, bg=PANEL)
        tabs.pack(fill="x", side="bottom")
        tk.Frame(tabs, bg=GRAY2, height=1).pack(fill="x")
        tb = tk.Frame(tabs, bg=PANEL)
        tb.pack(fill="x")
        tk.Label(tb, text="㗊 Tümü", font=("Segoe UI",9), fg=WHITE, bg=PANEL, pady=14).pack(side="left", expand=True)
        for ico in ["🤚", "⭐", "🕒"]:
            tk.Label(tb, text=ico, font=("Segoe UI",11), fg=GRAY, bg=PANEL, pady=14).pack(side="left", expand=True)

        # Card grid
        cont = tk.Frame(left, bg=PANEL)
        cont.pack(fill="both", expand=True, padx=10, pady=(0,0))
        self.canvas = tk.Canvas(cont, bg=PANEL, highlightthickness=0, bd=0)
        self.card_frame = tk.Frame(self.canvas, bg=PANEL)
        self.card_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0), window=self.card_frame, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

    def _build_right(self):
        right = tk.Frame(self.root, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self._build_topbar(right)
        self._build_dropzone(right)
        self._build_text_card(right)
        self._build_feature_cards(right)

    def _build_topbar(self, p):
        top = tk.Frame(p, bg=BG)
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(24,0))

        lb = tk.Frame(top, bg=BG)
        lb.pack(side="left")
        
        # Simulated gradient title
        tt = tk.Frame(lb, bg=BG)
        tt.pack(anchor="w")
        tk.Label(tt, text="Hand", font=("Segoe UI",24,"bold"), fg=COPPER, bg=BG, bd=0, padx=0).pack(side="left")
        tk.Label(tt, text="Lingo", font=("Segoe UI",24,"bold"), fg=COPPER, bg=BG, bd=0, padx=0).pack(side="left")
        
        tk.Label(lb, text="AI Destekli İşaret Dili Tercümanı", font=("Segoe UI",9), fg=GRAY, bg=BG).pack(anchor="w", pady=(2,0))

        rb = tk.Frame(top, bg=BG)
        rb.pack(side="right")
        fg_ = TEAL if self.model.model else COPPER
        txt = "  ● Model Hazır ⌄ " if self.model.model else "  ● Model Yok ⌄ "
        f_badge = tk.Frame(rb, bg=fg_)
        f_badge.pack(side="left")
        tk.Label(f_badge, text=txt, font=("Segoe UI",8,"bold"), fg=fg_, bg=CARD_BG, pady=5).pack(padx=1, pady=1, ipady=1)
        
        set_btn = tk.Frame(rb, bg=CARD_BG, highlightbackground=GRAY2, highlightthickness=1)
        set_btn.pack(side="left", padx=(12,0))
        tk.Label(set_btn, text="⚙", font=("Segoe UI",12), fg=GRAY, bg=CARD_BG, padx=8, pady=3).pack()

    def _build_dropzone(self, p):
        center = tk.Frame(p, bg=BG)
        center.grid(row=1, column=0, sticky="nsew", padx=32, pady=16)
        center.columnconfigure(0, weight=1)
        center.rowconfigure(0, weight=1)

        self.dz_cv = tk.Canvas(center, bg=CARD_BG, highlightthickness=1, highlightbackground=GRAY2, bd=0)
        self.dz_cv.place(relx=0.5, rely=0.5, anchor="center", width=DZ_W, height=DZ_H)
        
        # Waves
        for i in range(10):
            yo = i * 6
            self.dz_cv.create_line(0, 100+yo, 150, 80+yo, 300, 180+yo, smooth=True, fill="#3c2a20", width=1)
            self.dz_cv.create_line(DZ_W, 100+yo, DZ_W-150, 80+yo, DZ_W-300, 180+yo, smooth=True, fill="#203535", width=1)

        # Center Dashed Circle & Icon
        cx, cy = DZ_W//2, DZ_H//2 - 20
        self.dz_cv.create_oval(cx-44, cy-44, cx+44, cy+44, outline=GRAY3, dash=(6,4), width=2)
        self._ph_ids = [
            self.dz_cv.create_text(cx, cy, text="✋", font=("Segoe UI",38), fill=COPPER),
            self.dz_cv.create_text(cx, cy+70, text="Harfi buraya bırakın.", font=("Segoe UI",16,"bold"), fill=COPPER),
            self.dz_cv.create_text(cx, cy+94, text="veya panelden sürükleyin", font=("Segoe UI",10), fill=GRAY),
        ]
        
        self.dz = self.dz_cv
        self.pred = tk.Frame(self.dz_cv, bg=CARD_BG)
        self._pred_win = self.dz_cv.create_window(cx, cy+10, window=self.pred, anchor="center", state="hidden")

        self.pred_img  = tk.Label(self.pred, bg=CARD_BG)
        self.pred_img.pack(pady=(10,6))
        rr = tk.Frame(self.pred, bg=CARD_BG); rr.pack()
        self.pred_lbl  = tk.Label(rr, text="", font=("Segoe UI",48,"bold"), fg=TEAL, bg=CARD_BG)
        self.pred_lbl.pack(side="left", padx=(0,12))
        ic = tk.Frame(rr, bg=CARD_BG); ic.pack(side="left", anchor="center")
        self.pred_name = tk.Label(ic, text="", font=("Segoe UI",12,"bold"), fg=COPPER, bg=CARD_BG, anchor="w")
        self.pred_name.pack(anchor="w")
        self.pred_conf = tk.Label(ic, text="", font=("Segoe UI",9), fg=GRAY, bg=CARD_BG, anchor="w")
        self.pred_conf.pack(anchor="w", pady=(2,6))
        bt = tk.Frame(ic, bg=GRAY2, height=5, width=130); bt.pack(anchor="w"); bt.pack_propagate(False)
        self.bar_fill = tk.Frame(bt, bg=TEAL, height=5)
        self.bar_fill.place(x=0, y=0, relheight=1, relwidth=0)

    def _build_text_card(self, p):
        card = tk.Frame(p, bg=CARD_BG, highlightbackground=GRAY2, highlightthickness=1)
        card.grid(row=2, column=0, sticky="ew", padx=32, pady=(0,16))

        hdr = tk.Frame(card, bg=CARD_BG)
        hdr.pack(fill="x", padx=20, pady=(16,0))
        tk.Label(hdr, text="✦", font=("Segoe UI",12), fg=TEAL, bg=CARD_BG).pack(side="left")
        tk.Label(hdr, text=" ÇEVİRİLEN METİN", font=("Segoe UI",9,"bold"), fg=WHITE, bg=CARD_BG).pack(side="left")

        vb = tk.Frame(hdr, bg=GRAY2, highlightbackground=GRAY3, highlightthickness=1)
        vb.pack(side="right")
        tk.Label(vb, text="🔊", font=("Segoe UI",10), fg=GRAY, bg=GRAY2, padx=6, pady=2).pack()

        self.wc = tk.Canvas(hdr, bg=CARD_BG, width=160, height=24, highlightthickness=0)
        self.wc.pack(side="right", padx=(0,16))
        self.wave_lines = []
        heights = [4,8,12,16,10,20,24,16,10,14,18,12,8,10,6,14,20,12,8,4]
        for i, h in enumerate(heights):
            x = i*7 + 6; cy = 12
            c = TEAL if i<8 else (COPPER if i<14 else GRAY)
            line = self.wc.create_line(x, cy-h//2, x, cy+h//2, fill=c, width=3, capstyle="round")
            self.wave_lines.append(line)

        tk.Frame(card, bg=GRAY2, height=1).pack(fill="x", padx=20, pady=(12,0))

        # Bottom part: Text Area + Buttons
        bot = tk.Frame(card, bg=CARD_BG)
        bot.pack(fill="x", padx=20, pady=(12,16))
        
        self.sent_lbl = tk.Label(bot, text="Buraya oluşan metin gelecek...",
                                  font=("Segoe UI",12), fg=GRAY, bg=CARD_BG, anchor="w", wraplength=450)
        self.sent_lbl.pack(side="left", fill="x", expand=True)

        br = tk.Frame(bot, bg=CARD_BG)
        br.pack(side="right")
        for txt, cmd, hc, fgc in [
            ("🔊 Sesli Oku", self._speak, TEAL, TEAL),
            ("🗑 Sil",       self._del,   GRAY3, WHITE),
            ("— Boşluk",    self._space,  GRAY3, WHITE),
            ("🗑 Temizle",  self._clear,  COPPER, COPPER),
        ]:
            bf = tk.Frame(br, bg=hc)
            bf.pack(side="left", padx=(8,0))
            b = tk.Button(bf, text=txt, font=("Segoe UI",9,"bold"),
                          fg=fgc, bg=CARD_BG, bd=0, padx=11, pady=5,
                          activebackground=CARD_HL, activeforeground=WHITE,
                          cursor="hand2", command=cmd)
            b.pack(padx=1, pady=1)
            b.bind("<Enter>", lambda e,b=b: b.config(bg=CARD_HL))
            b.bind("<Leave>", lambda e,b=b: b.config(bg=CARD_BG))

    def _build_feature_cards(self, p):
        bot_container = tk.Frame(p, bg=BG)
        bot_container.grid(row=3, column=0, sticky="ew", padx=32, pady=(0, 20))
        
        row = tk.Frame(bot_container, bg=BG)
        row.pack(fill="x")
        row.columnconfigure((0,1,2), weight=1)
        feats = [
            ("⚡", "Hızlı & Doğru", "Anlık tercüme.", COPPER),
            ("🛡", "Güvenli & Gizli", "Veriler yerel kalır.", COPPER),
            ("👆", "Kolay Kullanım", "Basit işaretlerle çalışır.", COPPER),
        ]
        for col, (ico, title, desc, c) in enumerate(feats):
            fc = tk.Frame(row, bg=CARD_BG, highlightbackground=GRAY2, highlightthickness=1)
            fc.grid(row=0, column=col, sticky="ew", padx=(0 if col==0 else 16, 0))
            r = tk.Frame(fc, bg=CARD_BG)
            r.pack(fill="x", padx=20, pady=(16,16))
            tk.Label(r, text=ico, font=("Segoe UI",18), bg=CARD_BG, fg=c).pack(side="left")
            tf = tk.Frame(r, bg=CARD_BG)
            tf.pack(side="left", padx=(12,0))
            tk.Label(tf, text=title, font=("Segoe UI",10,"bold"), fg=WHITE, bg=CARD_BG).pack(anchor="w")
            tk.Label(tf, text=desc, font=("Segoe UI",8), fg=GRAY, bg=CARD_BG, justify="left").pack(anchor="w", pady=(2,0))

        # Footer: Proje Hakkında
        footer = tk.Frame(bot_container, bg=CARD_BG, highlightbackground=GRAY2, highlightthickness=1)
        footer.pack(fill="x", pady=(16, 0))
        
        fh = tk.Frame(footer, bg=CARD_BG)
        fh.pack(anchor="w", padx=20, pady=(12, 0))
        tk.Label(fh, text="ℹ", font=("Segoe UI", 12), fg=COPPER, bg=CARD_BG).pack(side="left")
        tk.Label(fh, text="  PROJE HAKKINDA", font=("Segoe UI", 9, "bold"), fg=WHITE, bg=CARD_BG).pack(side="left")
        
        ab_txt = ("HandLingo, işitme engelli bireylerin iletişimini kolaylaştırmak için geliştirilmiş yapay zeka destekli işaret dili tercüman sistemidir.\n\n"
                  "Kullanıcının seçtiği el görselleri üzerinden harfleri anında tanır ve metne çevirir.\n\n"
                  "MobileNetV2 mimarisi ile eğitilmiş derin öğrenme modeli kullanmaktadır.")
        tk.Label(footer, text=ab_txt, font=("Segoe UI", 8), fg=GRAY, bg=CARD_BG, justify="left", wraplength=1000).pack(anchor="w", padx=46, pady=(4, 16))

    def _fill_cards(self):
        r=c=0
        for letter in sorted(self.samples.keys()):
            self._card(self.card_frame, letter, self.samples[letter], r, c)
            c+=1
            if c>=3: c=0; r+=1

    def _card(self, parent, letter, path, row, col):
        if not hasattr(self, 'selected_letter'): self.selected_letter = 'D'
        is_sel = (letter == getattr(self, 'selected_letter', 'D'))
        bc = COPPER if is_sel else GRAY2
        tc = COPPER if is_sel else WHITE
        
        f = tk.Frame(parent, bg=CARD_BG, highlightbackground=bc,
                     highlightthickness=1, cursor="hand2")
        f.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        parent.columnconfigure(col, weight=1, minsize=76)
        try:
            photo = ImageTk.PhotoImage(make_thumb(path, THUMB, 8, CARD_BG))
            self._card_photos[letter] = photo
            self.paths[letter] = path
            il = tk.Label(f, image=photo, bg=CARD_BG)
            il.pack(padx=4, pady=(8,2))
        except:
            il = tk.Label(f, text="?", font=("Segoe UI",18), fg=GRAY, bg=CARD_BG)
            il.pack(padx=4, pady=(8,2))
        ll = tk.Label(f, text=letter, font=("Segoe UI",9,"bold"), fg=tc, bg=CARD_BG)
        ll.pack(pady=(0,6))
        
        if not hasattr(self, 'card_widgets'): self.card_widgets = {}
        self.card_widgets[letter] = {'frame': f, 'label': ll}
        
        def on_enter(e, l=letter):
            if getattr(self, 'selected_letter', None) != l:
                self.card_widgets[l]['frame'].config(highlightbackground=GRAY, bg=CARD_HL)
        def on_leave(e, l=letter):
            if getattr(self, 'selected_letter', None) != l:
                self.card_widgets[l]['frame'].config(highlightbackground=GRAY2, bg=CARD_BG)

        for w in [f,il,ll]:
            w.bind("<ButtonPress-1>",  lambda e,l=letter: self._ds(e,l))
            w.bind("<B1-Motion>",       self._dm)
            w.bind("<ButtonRelease-1>", self._de)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def _ds(self, e, letter):
        self.selected_letter = letter
        if hasattr(self, 'card_widgets'):
            for l, w in self.card_widgets.items():
                if l == letter:
                    w['frame'].config(highlightbackground=COPPER, bg=CARD_BG)
                    w['label'].config(fg=COPPER)
                else:
                    w['frame'].config(highlightbackground=GRAY2, bg=CARD_BG)
                    w['label'].config(fg=WHITE)

        self.dragging=True; self.drag_letter=letter
        if letter in self._card_photos:
            self.drag_widget = tk.Label(self.root, image=self._card_photos[letter], bg=COPPER, bd=2, relief="flat")
        else:
            self.drag_widget = tk.Label(self.root, text=letter, font=("Segoe UI",18,"bold"), fg="#000", bg=COPPER, padx=8, pady=4)
        x=e.x_root-self.root.winfo_rootx()-THUMB//2
        y=e.y_root-self.root.winfo_rooty()-THUMB//2
        self.drag_widget.place(x=x,y=y); self.drag_widget.lift()
        self.dz_cv.config(highlightbackground=COPPER)

    def _dm(self, e):
        if self.drag_widget and self.dragging:
            x=e.x_root-self.root.winfo_rootx()-THUMB//2
            y=e.y_root-self.root.winfo_rooty()-THUMB//2
            self.drag_widget.place(x=x,y=y)

    def _de(self, e):
        if not self.dragging: return
        self.dragging=False; self.dz_cv.config(highlightbackground=GRAY2)
        if self.drag_widget: self.drag_widget.destroy(); self.drag_widget=None
        if e.x_root > self.root.winfo_rootx()+260:
            self._on_drop(self.drag_letter)
        self.drag_letter=None

    def _on_drop(self, letter):
        if not letter or letter not in self.paths: return
        path=self.paths[letter]
        for pid in self._ph_ids: self.dz_cv.itemconfigure(pid, state="hidden")
        self.dz_cv.itemconfigure(self._pred_win, state="normal")
        try:
            thumb=make_thumb(path, DROP_IMG, 12, CARD_BG)
            self._drop_photo=ImageTk.PhotoImage(thumb)
            self.pred_img.configure(image=self._drop_photo)
        except: pass
        self.pred_lbl.configure(text="⏳", fg=COPPER)
        self.pred_name.configure(text="Analiz ediliyor...", fg=COPPER)
        self.pred_conf.configure(text="Tahmin yürütülüyor...", fg=GRAY)
        self.bar_fill.configure(bg=TEAL)
        self.bar_fill.place(relwidth=0)
        self.root.update()
        def run():
            res,conf=self.model.predict(path)
            self.root.after(0, lambda: self._show(res,conf))
        threading.Thread(target=run, daemon=True).start()

    def _show(self, res, conf):
        display=res
        if res=="Space": display="␣"; self.sentence.append(" ")
        elif res=="Del":
            display="⌫"
            if self.sentence: self.sentence.pop()
        else: self.sentence.append(res)
        clr = TEAL if conf>.8 else (COPPER if conf>.5 else RED)
        self.pred_lbl.configure(text=display, fg=clr)
        self.pred_name.configure(text=f"Tahmin: {res}", fg=WHITE)
        self.pred_conf.configure(text=f"Güven: %{conf*100:.1f}", fg=GRAY)
        self.bar_fill.configure(bg=clr); self.bar_fill.place(relwidth=conf)
        self._upd()

    def _upd(self):
        t="".join(self.sentence) if self.sentence else ""
        self.sent_lbl.configure(
            text=t if t else "Buraya oluşan metin gelecek...",
            fg=WHITE if t else GRAY)

    def _animate_waves(self):
        if getattr(self, 'is_speaking', False):
            for i, line in enumerate(self.wave_lines):
                h = random.randint(4, 24)
                x = i*7 + 6; cy = 12
                self.wc.coords(line, x, cy-h//2, x, cy+h//2)
            self.root.after(100, self._animate_waves)
        else:
            heights = [4,8,12,16,10,20,24,16,10,14,18,12,8,10,6,14,20,12,8,4]
            for i, line in enumerate(self.wave_lines):
                h = heights[i]
                x = i*7 + 6; cy = 12
                self.wc.coords(line, x, cy-h//2, x, cy+h//2)

    def _speak(self):
        t="".join(self.sentence)
        if not t.strip() or getattr(self, 'is_speaking', False): return
        self.is_speaking = True
        self._animate_waves()
        def run():
            try:
                import pyttsx3; e=pyttsx3.init(); e.setProperty("rate",140)
                for v in e.getProperty("voices"):
                    if "turk" in v.name.lower() or "tr" in v.id.lower():
                        e.setProperty("voice",v.id); break
                e.say(t); e.runAndWait()
            except ImportError:
                if sys.platform=="win32":
                    os.system(f'powershell -Command "Add-Type -AssemblyName System.Speech;$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;$s.Speak(\'{t}\')"')
            self.is_speaking = False
        threading.Thread(target=run,daemon=True).start()

    def _del(self):
        if self.sentence: self.sentence.pop(); self._upd()

    def _space(self):
        self.sentence.append(" "); self._upd()

    def _clear(self):
        self.sentence.clear(); self._upd()
        self.dz_cv.itemconfigure(self._pred_win, state="hidden")
        for pid in self._ph_ids: self.dz_cv.itemconfigure(pid, state="normal")

    def run(self): self.root.mainloop()

if __name__ == "__main__":
    print("="*45); print("  HandLingo v5 — Pixel Perfect"); print("="*45)
    App().run()



# ------------------------------------------------------------------------------
# QR CODE GENERATOR USING STANDARD LIBRARY + CUSTOM RENDER
# 
# PURPOSE: Generates high-fidelity, customizable QR codes.
# 
# WHY:     Standard libraries are excellent for complex mathematical encoding 
#          but severely lack advanced graphical customization (like camouflage 
#          patterns or perfect SVG vector shapes). 
# 
# HOW:     This script delegates the heavy lifting of ISO data encoding and 
#          error correction to the 'qrcode' library. It then extracts the 
#          raw binary matrix and feeds it into two proprietary rendering 
#          engines (Raster via Pillow, Vector via XML) for pixel-perfect, 
#          infinitely scalable outputs.
# ------------------------------------------------------------------------------

import qrcode
from PIL import Image, ImageDraw, ImageColor, ImageTk
import math
import random
import customtkinter as ctk
from tkinter import messagebox, filedialog

# UI Configuration
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 
APPLE_FONT = "SF Pro Display"

# 1. (PILLOW)
def apply_circular_badge(qr_img, bg_color_rgb):
    """Wraps the QR code in a circular badge with a solid background."""
    if qr_img.mode != 'RGBA':
        qr_img = qr_img.convert('RGBA')
        
    qr_size = qr_img.size[0]
    padding = int(qr_size * 0.2)
    badge_size = qr_size + (padding * 2)
    
    badge = Image.new('RGBA', (badge_size, badge_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    
    bg_color_full = bg_color_rgb + (255,)
    draw.ellipse((0, 0, badge_size, badge_size), fill=bg_color_full)
    
    qr_layer = Image.new('RGBA', (badge_size, badge_size), (0, 0, 0, 0))
    qr_layer.paste(qr_img, (padding, padding))
    
    return Image.alpha_composite(badge, qr_layer)

def apply_circular_camouflage(qr_img, box_size, fg_rgb, bg_rgb, is_circle=False):
    """Generates a camouflage pattern around the QR matrix to create a seamless circle."""
    if qr_img.mode != 'RGBA':
        qr_img = qr_img.convert('RGBA')
        
    qr_size = qr_img.size[0]
    qr_modules = qr_size // box_size
    
    diag_modules = math.ceil(qr_modules * math.sqrt(2))
    if diag_modules % 2 != qr_modules % 2:
        diag_modules += 1
        
    canvas_size = diag_modules * box_size
    center = radius = canvas_size // 2

    canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    for row in range(diag_modules):
        for col in range(diag_modules):
            cx = col * box_size + (box_size / 2)
            cy = row * box_size + (box_size / 2)
            distance = math.sqrt((cx - center)**2 + (cy - center)**2)
            
            if distance <= radius:
                is_filled = random.random() > 0.5
                pixel_color = fg_rgb + (255,) if is_filled else bg_rgb + (255,)
                
                x0, y0 = col * box_size, row * box_size
                x1, y1 = x0 + box_size, y0 + box_size
                
                if is_circle:
                    draw.ellipse([x0, y0, x1, y1], fill=pixel_color)
                else:
                    draw.rectangle([x0, y0, x1, y1], fill=pixel_color)

    qr_overlay = Image.alpha_composite(Image.new("RGBA", qr_img.size, bg_rgb + (255,)), qr_img)
    offset = (canvas_size - qr_size) // 2
    temp_layer = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    temp_layer.paste(qr_overlay, (offset, offset))

    canvas = Image.alpha_composite(canvas, temp_layer)

    mask = Image.new('L', (canvas_size, canvas_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, canvas_size, canvas_size), fill=255)
    
    final_img = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    final_img.paste(canvas, (0, 0), mask)

    return final_img

def generate_raster_asset(matrix, fg_rgb, bg_rgb, is_circle, layout, box_size=10, border=3):
    """Core function to generate pixel-based assets."""
    mat_rows, mat_cols = len(matrix), len(matrix[0])
    img_w, img_h = (mat_cols + 2 * border) * box_size, (mat_rows + 2 * border) * box_size
    
    img_base = Image.new("RGBA", (img_w, img_h), bg_rgb + (255,))
    draw = ImageDraw.Draw(img_base)
    
    for r_idx, row in enumerate(matrix):
        for c_idx, val in enumerate(row):
            if val == 1:
                x0, y0 = (c_idx + border) * box_size, (r_idx + border) * box_size
                if is_circle: 
                    draw.ellipse([x0, y0, x0 + box_size, y0 + box_size], fill=fg_rgb + (255,))
                else: 
                    draw.rectangle([x0, y0, x0 + box_size, y0 + box_size], fill=fg_rgb + (255,))

    if layout == "Badge Circolare": 
        return apply_circular_badge(img_base, bg_rgb)
    elif layout == "Camouflage Circolare": 
        return apply_circular_camouflage(img_base, box_size, fg_rgb, bg_rgb, is_circle)
        
    return img_base


# 2. VECTOR RENDER (SVG)
def generate_svg_asset(matrix, fg_hex, bg_hex, is_circle, layout, box_size=10, border=3):
    """Core function to generate native, infinitely scalable XML Vector assets."""
    mat_rows, mat_cols = len(matrix), len(matrix[0])
    img_w, img_h = (mat_cols + 2 * border) * box_size, (mat_rows + 2 * border) * box_size
    svg_elements = []

    if layout == "Camouflage Circolare":
        qr_modules = max(mat_cols, mat_rows) + 2 * border
        diag_modules = math.ceil(qr_modules * math.sqrt(2))
        if diag_modules % 2 != qr_modules % 2: 
            diag_modules += 1

        tot_size = diag_modules * box_size
        center = radius = tot_size / 2
        offset_pixels = ((diag_modules - qr_modules) // 2) * box_size

        svg_elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{tot_size}" height="{tot_size}" viewBox="0 0 {tot_size} {tot_size}">')
        svg_elements.append(f'<defs><clipPath id="circleClip"><circle cx="{center}" cy="{center}" r="{radius}"/></clipPath></defs>')
        svg_elements.append(f'<rect width="{tot_size}" height="{tot_size}" fill="{bg_hex}" clip-path="url(#circleClip)"/>')
        svg_elements.append('<g clip-path="url(#circleClip)">')

        # Fake camouflage modules
        start_m, end_m = (diag_modules - qr_modules) // 2, ((diag_modules - qr_modules) // 2) + qr_modules
        for r in range(diag_modules):
            for c in range(diag_modules):
                if start_m <= r < end_m and start_m <= c < end_m: continue 
                cx, cy = c * box_size + (box_size / 2), r * box_size + (box_size / 2)
                if math.sqrt((cx - center)**2 + (cy - center)**2) <= radius and random.random() > 0.5:
                    if is_circle: svg_elements.append(f'<circle cx="{cx}" cy="{cy}" r="{box_size/2}" fill="{fg_hex}"/>')
                    else: svg_elements.append(f'<rect x="{c*box_size}" y="{r*box_size}" width="{box_size}" height="{box_size}" fill="{fg_hex}"/>')

        # Inner solid wall for true data protection
        svg_elements.append(f'<rect x="{offset_pixels}" y="{offset_pixels}" width="{img_w}" height="{img_h}" fill="{bg_hex}"/>')
        
        # True QR modules
        for r_idx, row in enumerate(matrix):
            for c_idx, val in enumerate(row):
                if val == 1:
                    x, y = (c_idx + border) * box_size + offset_pixels, (r_idx + border) * box_size + offset_pixels
                    if is_circle: svg_elements.append(f'<circle cx="{x+box_size/2}" cy="{y+box_size/2}" r="{box_size/2}" fill="{fg_hex}"/>')
                    else: svg_elements.append(f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" fill="{fg_hex}"/>')
        svg_elements.append('</g></svg>')

    else:
        if layout == "Badge Circolare":
            pad = int(img_w * 0.2)
            tot_size = img_w + (pad * 2)
            svg_elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{tot_size}" height="{tot_size}" viewBox="0 0 {tot_size} {tot_size}">')
            svg_elements.append(f'<circle cx="{tot_size/2}" cy="{tot_size/2}" r="{tot_size/2}" fill="{bg_hex}"/>')
            offset_x, offset_y = pad, pad
        else:
            svg_elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{img_w}" height="{img_h}" viewBox="0 0 {img_w} {img_h}">')
            svg_elements.append(f'<rect width="{img_w}" height="{img_h}" fill="{bg_hex}"/>')
            offset_x, offset_y = 0, 0

        # True QR modules
        for r_idx, row in enumerate(matrix):
            for c_idx, val in enumerate(row):
                if val == 1:
                    x, y = (c_idx + border) * box_size + offset_x, (r_idx + border) * box_size + offset_y
                    if is_circle: svg_elements.append(f'<circle cx="{x+box_size/2}" cy="{y+box_size/2}" r="{box_size/2}" fill="{fg_hex}"/>')
                    else: svg_elements.append(f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" fill="{fg_hex}"/>')
        svg_elements.append('</svg>')

    return "\n".join(svg_elements)

# 3.USER INTERFACE
class QRStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("QR Studio PRO - Advanced QR Code Generator")
        self.geometry("950x650") 
        self.resizable(False, False)
        
        # --- UI Variables ---
        self.data_var = ctk.StringVar(value="https://github.com")
        self.fg_var = ctk.StringVar(value="#000000")
        self.bg_var = ctk.StringVar(value="#FFFFFF")
        self.format_var = ctk.StringVar(value="PNG")
        self.shape_var = ctk.StringVar(value="Quadrato")
        self.layout_var = ctk.StringVar(value="Standard")

        self.generated_img = None 
        self.svg_output_str = "" 
        self.after_id = None 

        self.create_interface()
        
        # --- Triggers for Live Update ---
        self.data_var.trace_add("write", self.on_change)
        self.fg_var.trace_add("write", self.on_change)
        self.bg_var.trace_add("write", self.on_change)
        self.shape_var.trace_add("write", self.on_change)
        self.layout_var.trace_add("write", self.on_change)
        self.format_var.trace_add("write", self.on_change)

        self.render_preview()

    def create_interface(self):
        left_panel = ctk.CTkFrame(self, width=400, fg_color="transparent")
        left_panel.pack(side="left", fill="y", padx=20, pady=20)
        
        right_panel = ctk.CTkFrame(self, fg_color=("gray90", "gray12"), corner_radius=15)
        right_panel.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(left_panel, text="QR Studio", font=ctk.CTkFont(family=APPLE_FONT, size=32, weight="bold"))
        header.pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(left_panel, text="URL or Text", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(5, 5))
        ctk.CTkEntry(left_panel, textvariable=self.data_var, width=350, height=40, corner_radius=8, font=ctk.CTkFont(family=APPLE_FONT)).pack(anchor="w")

        ctk.CTkLabel(left_panel, text="Colors", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(20, 5))
        color_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        color_frame.pack(anchor="w", fill="x")

        self.btn_fg = ctk.CTkButton(color_frame, text="Pixel", width=160, height=35, fg_color=self.fg_var.get(), text_color="white", command=lambda: self.open_color_picker(self.fg_var, self.btn_fg))
        self.btn_fg.pack(side="left", padx=(0, 10))

        self.btn_bg = ctk.CTkButton(color_frame, text="Background", width=160, height=35, fg_color=self.bg_var.get(), text_color="black", command=lambda: self.open_color_picker(self.bg_var, self.btn_bg))
        self.btn_bg.pack(side="left")

        ctk.CTkLabel(left_panel, text="Export Format", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkOptionMenu(left_panel, variable=self.format_var, values=["PNG", "JPG", "SVG"], width=330, height=35, corner_radius=8, font=ctk.CTkFont(family=APPLE_FONT)).pack(anchor="w")

        ctk.CTkLabel(left_panel, text="Module Style", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkSegmentedButton(left_panel, variable=self.shape_var, values=["Quadrato", "Cerchio"], width=330, font=ctk.CTkFont(family=APPLE_FONT)).pack(anchor="w")

        ctk.CTkLabel(left_panel, text="External Layout", font=ctk.CTkFont(family=APPLE_FONT, weight="bold")).pack(anchor="w", pady=(20, 5))
        ctk.CTkOptionMenu(left_panel, variable=self.layout_var, values=["Standard", "Badge Circolare", "Camouflage Circolare"], width=330, height=35, corner_radius=8, font=ctk.CTkFont(family=APPLE_FONT)).pack(anchor="w")

        ctk.CTkLabel(right_panel, text="Live Preview", font=ctk.CTkFont(family=APPLE_FONT, size=20, weight="bold")).pack(pady=(20, 10))
        
        self.lbl_preview = ctk.CTkLabel(right_panel, text="")
        self.lbl_preview.pack(pady=10, expand=True)

        self.lbl_diagnostic = ctk.CTkLabel(right_panel, text="", text_color="#ef4444", font=ctk.CTkFont(family=APPLE_FONT, size=12, weight="bold"))
        self.lbl_diagnostic.pack(pady=5)

        self.btn_save = ctk.CTkButton(right_panel, text="Export Asset", font=ctk.CTkFont(family=APPLE_FONT, size=16, weight="bold"), fg_color="#10b981", hover_color="#059669", height=50, corner_radius=25, command=self.save_file)
        self.btn_save.pack(fill="x", padx=40, pady=(10, 30))

    def open_color_picker(self, var_target, btn_target):
        """Custom OS-independent minimal color picker."""
        picker = ctk.CTkToplevel(self)
        picker.title("Choose Color")
        picker.geometry("260x360")
        picker.resizable(False, False)
        picker.attributes("-topmost", True)
        picker.grab_set() 
        
        ctk.CTkLabel(picker, text="Quick Palette", font=ctk.CTkFont(family=APPLE_FONT, size=16, weight="bold")).pack(pady=(15, 10))
        
        grid_frame = ctk.CTkFrame(picker, fg_color="transparent")
        grid_frame.pack(padx=20, pady=5)
        
        palette_colors = [
            "#FF3B30", "#FF9500", "#FFCC00", "#34C759", 
            "#5AC8FA", "#007AFF", "#5856D6", "#AF52DE", 
            "#FF2D55", "#000000", "#FFFFFF", "#8E8E93", 
            "#1C1C1E", "#3A3A3C", "#F2F2F7", "#059669"
        ]
        
        def set_color(c):
            var_target.set(c)
            btn_target.configure(fg_color=c)
            try:
                rgb = ImageColor.getrgb(c)
                luminance = (rgb[0]*299 + rgb[1]*587 + rgb[2]*114) / 1000
                btn_target.configure(text_color="white" if luminance < 128 else "black")
            except: pass
            picker.destroy()
            
        row, col = 0, 0
        for c in palette_colors:
            btn = ctk.CTkButton(grid_frame, text="", width=40, height=40, fg_color=c, corner_radius=8, command=lambda color=c: set_color(color))
            if c in ["#FFFFFF", "#F2F2F7"]:
                btn.configure(border_width=1, border_color="#D1D1D6", hover_color="#E5E5EA")
            else:
                btn.configure(hover_color=c) 
            btn.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col > 3:
                col = 0
                row += 1
                
        ctk.CTkLabel(picker, text="Or paste HEX code:", font=ctk.CTkFont(family=APPLE_FONT, size=13, weight="bold")).pack(pady=(15, 5))
        
        hex_var = ctk.StringVar(value=var_target.get())
        entry = ctk.CTkEntry(picker, textvariable=hex_var, width=150, justify="center", font=ctk.CTkFont(family=APPLE_FONT, weight="bold"))
        entry.pack(pady=5)
        
        
        def confirm_hex(event=None):
            val = hex_var.get().strip().upper()
            if not val.startswith("#"): val = "#" + val
            try:
                ImageColor.getrgb(val) 
                set_color(val)
            except ValueError:
                messagebox.showerror("Error", "Invalid HEX code.", parent=picker)
        entry.bind("<Return>", confirm_hex)        
        ctk.CTkButton(picker, text="Apply HEX", fg_color="#007AFF", hover_color="#005ecb", font=ctk.CTkFont(family=APPLE_FONT, weight="bold"), command=confirm_hex).pack(pady=(10, 10))

    def on_change(self, *args):
        """Debouncer logic to prevent render overload while typing."""
        if self.after_id:
            self.after_cancel(self.after_id)
        self.after_id = self.after(300, self.render_preview)

    def render_preview(self):
        data_str = self.data_var.get().strip()
        self.lbl_diagnostic.configure(text="")
        
        if not data_str:
            self.lbl_diagnostic.configure(text="Enter data to generate the code.")
            self.lbl_preview.configure(image="")
            self.btn_save.configure(state="disabled")
            return

        try:
            fg_hex = self.fg_var.get()
            bg_hex = self.bg_var.get()
            fg_rgb = ImageColor.getrgb(fg_hex)
            bg_rgb = ImageColor.getrgb(bg_hex)
            
            if fg_rgb == (0, 0, 0): fg_rgb = (1, 1, 1)
            if bg_rgb == (0, 0, 0): bg_rgb = (1, 1, 1)
            
            lum_fg = (fg_rgb[0] * 299 + fg_rgb[1] * 587 + fg_rgb[2] * 114) / 1000
            lum_bg = (bg_rgb[0] * 299 + bg_rgb[1] * 587 + bg_rgb[2] * 114) / 1000
            contrast = abs(lum_fg - lum_bg)
            
            if contrast == 0:
                self.lbl_diagnostic.configure(text="ERROR: Identical colors. Choose a visible contrast.")
                self.lbl_preview.configure(image="")
                self.btn_save.configure(state="disabled")
                return
            elif contrast < 80:
                self.lbl_diagnostic.configure(text="WARNING: Low contrast. Scanners might fail.", text_color="#f59e0b")
            else:
                self.lbl_diagnostic.configure(text="Matrix valid.", text_color="#10b981")
                
        except Exception:
            self.lbl_diagnostic.configure(text="Color decoding error.")
            return

        # DATA ENCODING via QRCODE LIBRARY
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=1, border=0)
        qr.add_data(data_str)
        qr.make(fit=True)
        raw_matrix = [[1 if cell else 0 for cell in row] for row in qr.get_matrix()]

        box_sz = 10
        is_circ = (self.shape_var.get() == "Cerchio")
        lay = self.layout_var.get()
        fmt = self.format_var.get()

        # ROUTING TO SPECIFIC ENGINES
        if fmt == "SVG":
            self.svg_output_str = generate_svg_asset(raw_matrix, fg_hex, bg_hex, is_circ, lay, box_sz, 3)
            # Raster fallback required for Tkinter UI preview
            self.generated_img = generate_raster_asset(raw_matrix, fg_rgb, bg_rgb, is_circ, lay, box_sz, 3)
        else:
            self.generated_img = generate_raster_asset(raw_matrix, fg_rgb, bg_rgb, is_circ, lay, box_sz, 3)

        # UPDATE UI
        img_disp = self.generated_img.copy()
        c_img = ctk.CTkImage(light_image=img_disp, dark_image=img_disp, size=(380, 380))
        self.lbl_preview.configure(image=c_img)
        self.lbl_preview.image = c_img
        self.btn_save.configure(state="normal")

    def save_file(self):
        fmt = self.format_var.get()
        ext = f".{fmt.lower()}"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=ext,
            initialfile=f"qr_code{ext}",
            title="Export Asset",
            filetypes=[(f"{fmt} files", f"*{ext}")]
        )
        
        if filepath:
            if fmt == "SVG":
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self.svg_output_str)
            elif fmt == "JPG":
                flat_bg = Image.new("RGB", self.generated_img.size, ImageColor.getrgb(self.bg_var.get()))
                flat_bg.paste(self.generated_img, (0, 0), self.generated_img if self.generated_img.mode == 'RGBA' else None)
                flat_bg.save(filepath, "JPEG", quality=100)
            else:
                self.generated_img.save(filepath, "PNG")
                
            messagebox.showinfo("Saved", f"Export completed successfully:\n{filepath}")

if __name__ == "__main__":
    app = QRStudioApp()
    app.mainloop()
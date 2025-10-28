import threading, random, os, traceback
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .models import SetSpec, CardSet, COLORS
from .generation.distribution import plan_types
from .generation.cardgen import generate_card
from .generation.templates import load_packages
from .llm.ollama_client import name_art_flavor
from .exporters.json_exporter import export_json
from .exporters.csv_exporter import export_csv
from .exporters.mse_exporter import export_mse

APP_TITLE = "Phyrexian Engine"
PKG_DIR = os.path.join(os.path.dirname(__file__), "packages")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x760")
        self._build_ui()

        # initial population of package list
        self.refresh_package_list()

        self.card_set = None

    def _build_ui(self):
        top = ttk.Frame(self, padding=8); top.pack(fill='x')

        # Name / Code / Total
        ttk.Label(top, text="Set Name").grid(row=0, column=0, sticky='w')
        self.ent_name = ttk.Entry(top, width=28); self.ent_name.insert(0, "New Set")
        self.ent_name.grid(row=0, column=1, sticky='w', padx=6)

        ttk.Label(top, text="Code").grid(row=0, column=2, sticky='w')
        self.ent_code = ttk.Entry(top, width=10); self.ent_code.insert(0, "NEW")
        self.ent_code.grid(row=0, column=3, sticky='w', padx=6)

        ttk.Label(top, text="# Cards").grid(row=0, column=4, sticky='w')
        self.ent_total = ttk.Entry(top, width=7); self.ent_total.insert(0, "120")
        self.ent_total.grid(row=0, column=5, sticky='w', padx=6)

        # Colors toggles
        COLORS_LIST = COLORS
        self.color_vars = {c: tk.BooleanVar(value=c in ['W','U','B','R','G']) for c in COLORS_LIST}
        colf = ttk.Frame(self, padding=8); colf.pack(fill='x')
        ttk.Label(colf, text="Colors").grid(row=0, column=0, sticky='w')
        for i,c in enumerate(COLORS_LIST):
            ttk.Checkbutton(colf, text=c, variable=self.color_vars[c]).grid(row=0, column=i+1, padx=2)
        self.include_artifacts = tk.BooleanVar(value=True); ttk.Checkbutton(colf, text="Artifacts", variable=self.include_artifacts).grid(row=0, column=len(COLORS_LIST)+2, padx=6)
        self.include_lands = tk.BooleanVar(value=True); ttk.Checkbutton(colf, text="Lands", variable=self.include_lands).grid(row=0, column=len(COLORS_LIST)+3, padx=6)

        # Description
        ttk.Label(top, text="Set Theme / Description").grid(row=2, column=0, sticky='nw', pady=(8,0))
        self.txt_desc = tk.Text(top, width=80, height=4)
        self.txt_desc.insert('1.0', "Describe your set's themes and flavor. Packages below add effects & subtypes.")
        self.txt_desc.grid(row=2, column=1, columnspan=5, sticky='we', pady=(8,0))

        # LLM settings
        llm = ttk.Frame(self, padding=8); llm.pack(fill='x')
        ttk.Label(llm, text="Ollama model").grid(row=0, column=0, sticky='w')
        self.ent_model = ttk.Entry(llm, width=18); self.ent_model.insert(0, "gemma3:4b")
        self.ent_model.grid(row=0, column=1, sticky='w', padx=6)
        ttk.Label(llm, text="Endpoint").grid(row=0, column=2, sticky='w')
        self.ent_host = ttk.Entry(llm, width=28); self.ent_host.insert(0, "http://localhost:11434")
        self.ent_host.grid(row=0, column=3, sticky='w', padx=6)
        self.chk_use_llm = tk.BooleanVar(value=True)
        ttk.Checkbutton(llm, text="Use LLM for name/art/flavor", variable=self.chk_use_llm).grid(row=0, column=4, padx=8)

        # Packages
        pkgf = ttk.Labelframe(self, text="Packages (.json in packages/)", padding=8); pkgf.pack(fill='both', expand=False)

        # Button bar: Select/Deselect all packages
        bar = ttk.Frame(pkgf)
        bar.pack(side='top', fill='x', pady=(0,6))
        ttk.Button(bar, text="Select All", command=self._select_all_packages).pack(side='left')
        ttk.Button(bar, text="Deselect All", command=self._deselect_all_packages).pack(side='left', padx=6)

        self.lb = tk.Listbox(pkgf, selectmode='multiple', height=6, exportselection=False)

        self.lb.pack(side='left', fill='both', expand=True)
        ttk.Scrollbar(pkgf, orient='vertical', command=self.lb.yview).pack(side='right', fill='y')

        # Controls / progress / export (top row)
        btnf = ttk.Frame(self, padding=8); btnf.pack(fill='x')
        self.btn_gen = ttk.Button(btnf, text="Generate", command=self.on_generate); self.btn_gen.pack(side='left')
        ttk.Button(btnf, text="Export JSON", command=self.on_export_json).pack(side='left', padx=(12,0))
        ttk.Button(btnf, text="Export CSV", command=self.on_export_csv).pack(side='left', padx=6)
        ttk.Button(btnf, text="Export MSE (.mse-set)", command=self.on_export_mse).pack(side='left')
        self.prog = ttk.Progressbar(btnf, length=260, mode='determinate'); self.prog.pack(side='left', padx=12)
        self.lbl = ttk.Label(btnf, text="Idle."); self.lbl.pack(side='left')

        # Table of generated cards
        table = ttk.Frame(self, padding=8); table.pack(fill='both', expand=True)
        cols = ["#", "Name", "TypeLine", "MV", "Cost", "Rarity", "P/T", "Rules"]
        self.tree = ttk.Treeview(table, columns=cols, show='headings', height=18)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("#", width=40, anchor='center'); self.tree.column("Name", width=220)
        self.tree.column("TypeLine", width=220); self.tree.column("MV", width=40, anchor='center')
        self.tree.column("Cost", width=60, anchor='center'); self.tree.column("Rarity", width=70, anchor='center')
        self.tree.column("P/T", width=60, anchor='center'); self.tree.column("Rules", width=520)
        self.tree.pack(side='left', fill='both', expand=True)
        ttk.Scrollbar(table, orient='vertical', command=self.tree.yview).pack(side='right', fill='y')

    # --- data helpers ---
    def refresh_package_list(self):
        self.lb.delete(0, 'end')
        try:
            files = [f for f in os.listdir(PKG_DIR) if f.lower().endswith('.json')]
        except FileNotFoundError:
            files = []
        files = sorted(files)
        if not files:
            self.lb.insert('end', "<no packages found> (put .json files in the folder above)")
            self.lb.configure(state='disabled')
        else:
            self.lb.configure(state='normal')
            for f in files:
                self.lb.insert('end', f)

    def _gather_spec(self) -> SetSpec:
        name = self.ent_name.get().strip() or "New Set"
        code = self.ent_code.get().strip().upper()[:5] or "NEW"
        try:
            total = int(self.ent_total.get().strip())
        except Exception:
            total = 120
        colors = [c for c,v in self.color_vars.items() if v.get()]
        desc = self.txt_desc.get('1.0', 'end').strip()
        sel = [self.lb.get(i) for i in self.lb.curselection() if self.lb.get(i).endswith('.json')]
        selected_packages = [os.path.splitext(s)[0] for s in sel]
        spec = SetSpec(
            name=name,
            code=code,
            total_cards=total,
            colors=colors,
            include_artifacts=self.include_artifacts.get(),
            include_lands=self.include_lands.get(),
            description=desc,
            selected_packages=selected_packages
        )
        return spec

    # --- thread-safe UI helpers ---
    def _insert_row(self, idx, card):
        pt = f"{card.power}/{card.toughness}" if (getattr(card, 'power', None) is not None and getattr(card, 'toughness', None) is not None) else ""
        self.tree.insert('', 'end', values=(idx, getattr(card,'name',"") or "", card.typeline(), getattr(card,'mana_value',""), getattr(card,'mana_cost',""), getattr(card,'rarity',""), pt, getattr(card,'rules_text',"")))

    def _set_progress(self, val, text=None):
        self.prog.config(value=val)
        if text is not None:
            self.lbl.config(text=text)

    def _finish(self):
        self.btn_gen.config(state='normal')
        self.lbl.config(text="Done.")

    # --- handlers ---
    def on_generate(self):
        spec = self._gather_spec()
        if not spec.selected_packages:
            if not messagebox.askyesno("No packages selected", "Proceed with no packages? (Only minimal defaults will be used)"):
                return
        self.btn_gen.config(state='disabled'); self.prog.config(value=0, maximum=spec.total_cards)
        self.lbl.config(text="Generating..."); self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._worker, args=(spec,), daemon=True).start()

    def _worker(self, spec: SetSpec):
        try:
            random.seed(None)
            effects, subtypes_pool, string_pools, monster_keywords = load_packages(PKG_DIR, spec.selected_packages)
            types = plan_types(spec)
            cards = []
            for i, ctype in enumerate(types, start=1):
                # schedule progress update on main thread
                self.after(0, self._set_progress, i, f"Generating {i}/{len(types)}...")

                
                # Determine color identity for this card with proper distribution.
                if ctype == 'Land':
                    # Lands are colorless identity for cost purposes (no cost anyway)
                    colors = []
                else:
                    # Artifacts / Equipment: 80% chance to be colorless
                    if ctype in ('Artifact', 'Equipment') and spec.include_artifacts and random.random() < 0.80:
                        colors = []
                    else:
                        # 15% chance to be multicolor (only if at least 2 colors available)
                        can_multicolor = len(spec.colors) >= 2
                        if can_multicolor and random.random() < 0.15:
                            pick_n = min(2, len(spec.colors))
                            colors = random.sample(spec.colors, k=pick_n)
                        else:
                            # Otherwise pick ONE mono color or colorless with equal weight
                            # Build options = each allowed color + 'colorless'
                            opts = list(spec.colors) + ['colorless']
                            choice = random.choice(opts) if opts else 'colorless'
                            if choice == 'colorless':
                                colors = []
                            else:
                                colors = [choice]


                card = generate_card(f"C{i}", colors, ctype, spec, effects, subtypes_pool, string_pools, monster_keywords)
                if self.chk_use_llm.get():
                    pt = f"{card.power}/{card.toughness}" if (getattr(card,'power',None) is not None and getattr(card,'toughness',None) is not None) else None
                    subline = " ".join(card.subtypes) if getattr(card,'subtypes',None) else ""
                    res = name_art_flavor(spec.description, card.rules_text, subline, pt, model=self.ent_model.get().strip(), host=self.ent_host.get().strip())
                    card.name = res.get('name'); card.art_description = res.get('art'); card.flavor_text = res.get('flavor')
                else:
                    card.name = f"{ctype} {i}"
                    card.art_description = "A scene matching the card's color and effect."
                cards.append(card)

                # schedule row insert on main thread
                self.after(0, self._insert_row, i, card)

            # install the CardSet and finish on the main thread
            def _finalize():
                self.card_set = CardSet(spec=spec, cards=cards)
                self._finish()
            self.after(0, _finalize)

        except Exception as e:
            # surface exceptions in UI (main thread)
            def _show_err():
                tb = traceback.format_exc()
                self.lbl.config(text="Error occurred. See console.")
                messagebox.showerror("Generation Error", tb)
                self.btn_gen.config(state='normal')
            self.after(0, _show_err)

    def on_export_json(self):
        if not self.card_set or not self.card_set.cards:
            messagebox.showwarning("No data", "Generate cards first."); return
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")], title="Export to JSON")
        if not p: return
        export_json(self.card_set, p); messagebox.showinfo("Export", f"Saved to {p}")

    def on_export_csv(self):
        if not self.card_set or not self.card_set.cards:
            messagebox.showwarning("No data", "Generate cards first."); return
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="Export to CSV")
        if not p: return
        export_csv(self.card_set, p); messagebox.showinfo("Export", f"Saved to {p}")

    def on_export_mse(self):
        if not self.card_set or not self.card_set.cards:
            messagebox.showwarning("No data", "Generate cards first."); return
        p = filedialog.asksaveasfilename(defaultextension=".mse-set", filetypes=[("Magic Set Editor","*.mse-set")], title="Export to Magic Set Editor (.mse-set)")
        if not p: return
        export_mse(self.card_set, p); messagebox.showinfo("Export", f"Saved to {p}\nOpen in MSE (M15).")

    # --- Package selection helpers ---
    def _select_all_packages(self):
        """Select all items in the package listbox."""
        try:
            self.lb.selection_set(0, 'end')
        except Exception:
            pass

    def _deselect_all_packages(self):
        """Clear all selections in the package listbox."""
        try:
            self.lb.selection_clear(0, 'end')
        except Exception:
            pass


def main():
    app = App(); app.mainloop()

if __name__ == '__main__':
    main()

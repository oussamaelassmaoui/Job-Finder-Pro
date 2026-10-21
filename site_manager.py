"""
Job Finder Pro — Persistent Site Manager
Compatible with CustomTkinter + the existing Job_Finder.py.

What it provides:
- Add/edit/remove websites from the GUI
- Enable/disable sites with checkboxes
- Persistent storage in sites.json (survives app restarts)
- Built-in starter list of job sites
- Exports enabled sites as dictionaries for the search engine

Integration:
    from site_manager import SiteManager, load_sites, save_sites

    # In your JobFinderApp.__init__:
    self.sites = load_sites()
    # Add a button:
    ctk.CTkButton(parent, text="🌐 Gérer les sites",
                  command=self.open_site_manager).pack()

    # Add this method to JobFinderApp:
    def open_site_manager(self):
        SiteManager(self, on_change=self.refresh_site_checkboxes)

    # Use load_sites() to read enabled sites before searching.
"""
from __future__ import annotations

import json
import os
import re
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SITES_FILE = os.path.join(APP_DIR, "sites.json")

DEFAULT_SITES = [
    {"name": "Indeed", "domain": "indeed.com", "enabled": True, "country": "International", "notes": "Offres d'emploi"},
    {"name": "LinkedIn Jobs", "domain": "linkedin.com/jobs", "enabled": True, "country": "International", "notes": "Offres LinkedIn"},
    {"name": "Glassdoor", "domain": "glassdoor.com", "enabled": True, "country": "International", "notes": "Emploi et avis"},
    {"name": "Bayt", "domain": "bayt.com", "enabled": True, "country": "MENA", "notes": "Moyen-Orient et Afrique du Nord"},
    {"name": "ReKrute", "domain": "rekrute.com", "enabled": True, "country": "Maroc", "notes": "Emploi au Maroc"},
    {"name": "Emploi.ma", "domain": "emploi.ma", "enabled": True, "country": "Maroc", "notes": "Emploi au Maroc"},
    {"name": "MarocAnnonces", "domain": "marocannonces.com", "enabled": True, "country": "Maroc", "notes": "Annonces et emploi"},
    {"name": "ANAPEC", "domain": "anapec.org", "enabled": True, "country": "Maroc", "notes": "Agence nationale"},
    {"name": "Welcome to the Jungle", "domain": "welcometothejungle.com", "enabled": True, "country": "Europe", "notes": "Emploi et entreprises"},
    {"name": "Jooble", "domain": "jooble.org", "enabled": True, "country": "International", "notes": "Moteur d'offres"},
    {"name": "Talent.com", "domain": "talent.com", "enabled": True, "country": "International", "notes": "Moteur d'offres"},
    {"name": "Adzuna", "domain": "adzuna.com", "enabled": True, "country": "International", "notes": "Moteur d'offres"},
    {"name": "Careerjet", "domain": "careerjet.com", "enabled": True, "country": "International", "notes": "Moteur d'offres"},
    {"name": "Monster", "domain": "monster.com", "enabled": True, "country": "International", "notes": "Offres d'emploi"},
    {"name": "ZipRecruiter", "domain": "ziprecruiter.com", "enabled": True, "country": "International", "notes": "Offres d'emploi"},
    {"name": "SimplyHired", "domain": "simplyhired.com", "enabled": True, "country": "International", "notes": "Offres d'emploi"},
    {"name": "CareerBuilder", "domain": "careerbuilder.com", "enabled": True, "country": "International", "notes": "Offres d'emploi"},
    {"name": "France Travail", "domain": "francetravail.fr", "enabled": True, "country": "France", "notes": "Service public français"},
    {"name": "Apec", "domain": "apec.fr", "enabled": True, "country": "France", "notes": "Cadres"},
    {"name": "HelloWork", "domain": "hellowork.com", "enabled": True, "country": "France", "notes": "Emploi en France"},
    {"name": "EURES", "domain": "europa.eu/eures", "enabled": True, "country": "Europe", "notes": "Mobilité professionnelle européenne"},
    {"name": "XING Jobs", "domain": "xing.com/jobs", "enabled": True, "country": "Germany", "notes": "Emploi germanophone"},
    {"name": "Keejob", "domain": "keejob.com", "enabled": True, "country": "Tunisie", "notes": "Emploi en Tunisie"},
    {"name": "Tanitjobs", "domain": "tanitjobs.com", "enabled": True, "country": "Tunisie", "notes": "Emploi en Tunisie"},
    {"name": "Novojob", "domain": "novojob.com", "enabled": True, "country": "Afrique du Nord", "notes": "Emploi régional"},
    {"name": "Jobijoba", "domain": "jobijoba.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "Optioncarriere", "domain": "optioncarriere.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "StepStone", "domain": "stepstone.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "EURES", "domain": "eures.europa.eu", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "JobTeaser", "domain": "jobteaser.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "EuroJobs", "domain": "eurojobs.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "JobisJob", "domain": "jobisjob.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "GrabJobs", "domain": "grabjobs.co", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "JobRapido", "domain": "jobrapido.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "CareerBliss", "domain": "careerbliss.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "Lensa", "domain": "lensa.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
    {"name": "FlexJobs", "domain": "flexjobs.com", "enabled": True, "country": "International", "notes": "Source intégrée"},
]

def _normalize_domain(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"^https?://", "", value, flags=re.I)
    value = value.split("#", 1)[0].split("?", 1)[0].strip().strip("/")
    value = re.sub(r"^www\.", "", value, flags=re.I)
    return value.lower()

def _validate_site(name: str, domain: str) -> tuple[bool, str]:
    if not name.strip():
        return False, "Le nom du site est obligatoire."
    domain = _normalize_domain(domain)
    if not domain or "." not in domain:
        return False, "Entre un domaine valide, par exemple jobs.example.com."
    if any(ch.isspace() for ch in domain):
        return False, "Le domaine ne doit pas contenir d'espaces."
    if not re.fullmatch(r"[a-z0-9.-]+(?:/[a-z0-9._/-]+)?", domain):
        return False, "Domaine ou chemin invalide. Exemple : exemple.com/jobs"
    return True, ""

def load_sites() -> list[dict]:
    """Load saved sites; create sites.json with starter sites on first run."""
    if not os.path.exists(SITES_FILE):
        save_sites(DEFAULT_SITES)
        return [dict(s) for s in DEFAULT_SITES]
    try:
        with open(SITES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Le fichier doit contenir une liste de sites.")
        cleaned = []
        seen = set()
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            domain = _normalize_domain(str(item.get("domain", "")))
            ok, _ = _validate_site(name, domain)
            key = domain.lower()
            if ok and key not in seen:
                seen.add(key)
                cleaned.append({
                    "name": name,
                    "domain": domain,
                    "enabled": bool(item.get("enabled", True)),
                    "country": str(item.get("country", "International")),
                    "notes": str(item.get("notes", "")),
                })
        return cleaned
    except (OSError, json.JSONDecodeError, ValueError):
        # Preserve the user's broken file rather than silently overwriting it.
        return [dict(s) for s in DEFAULT_SITES]

def save_sites(sites: list[dict]) -> None:
    """Persist all sites to sites.json."""
    temp_path = SITES_FILE + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(sites, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, SITES_FILE)

def enabled_sites() -> list[dict]:
    return [dict(s) for s in load_sites() if s.get("enabled", True)]

class SiteManager(ctk.CTkToplevel):
    """A site-management window. on_change receives the updated list."""
    def __init__(self, master, on_change=None):
        super().__init__(master)
        self.title("Job Finder Pro — Gestion des sites")
        self.geometry("1050x720")
        self.minsize(800, 560)
        self.configure(fg_color="#0b1220")
        self.on_change = on_change
        self.sites = load_sites()
        self.row_vars = []
        self.delete_vars = []
        self._build_ui()
        self.transient(master)
        self.grab_set()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="#111c2e", corner_radius=14)
        header.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(header, text="🌐 Gestionnaire de sites",
                     font=ctk.CTkFont(size=23, weight="bold"),
                     text_color="#eaf2ff").pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(header,
                     text="Ajoute tes sites une seule fois. Ils restent enregistrés dans sites.json.",
                     text_color="#a9bad2").pack(anchor="w", padx=18, pady=(0, 14))

        form = ctk.CTkFrame(self, fg_color="#111c2e", corner_radius=14)
        form.pack(fill="x", padx=16, pady=8)
        self.name_entry = ctk.CTkEntry(form, placeholder_text="Nom du site — ex. MonJob",
                                       width=220, height=38)
        self.name_entry.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="ew")
        self.domain_entry = ctk.CTkEntry(form, placeholder_text="Domaine — ex. jobs.example.com",
                                         height=38)
        self.domain_entry.grid(row=0, column=1, padx=6, pady=12, sticky="ew")
        self.country_entry = ctk.CTkEntry(form, placeholder_text="Pays (optionnel)", width=150, height=38)
        self.country_entry.grid(row=0, column=2, padx=6, pady=12, sticky="ew")
        ctk.CTkButton(form, text="＋ Ajouter le site", width=145, height=38,
                      command=self.add_site, fg_color="#1677ff",
                      hover_color="#0f5fcf").grid(row=0, column=3, padx=(6, 12), pady=12)
        form.grid_columnconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=16, pady=(2, 8))
        ctk.CTkButton(toolbar, text="Tout activer", width=120,
                      command=lambda: self.set_all(True)).pack(side="left", padx=(0, 8))
        ctk.CTkButton(toolbar, text="Tout désactiver", width=130,
                      command=lambda: self.set_all(False),
                      fg_color="#334155", hover_color="#475569").pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text="Supprimer sélection", width=155,
                      command=self.delete_selected, fg_color="#b91c1c",
                      hover_color="#991b1b").pack(side="left", padx=4)
        self.count_label = ctk.CTkLabel(toolbar, text="", text_color="#a9bad2")
        self.count_label.pack(side="right", padx=8)

        list_shell = ctk.CTkFrame(self, fg_color="#111c2e", corner_radius=12)
        list_shell.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.scroll = ctk.CTkScrollableFrame(list_shell, fg_color="#111c2e",
                                             corner_radius=10, label_text="")
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self._render_rows()

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(footer,
                     text="Astuce : ajoute le domaine ou un chemin, sans obligation d'écrire https://",
                     text_color="#94a3b8").pack(side="left")
        ctk.CTkButton(footer, text="✓ Enregistrer et fermer", width=190, height=40,
                      command=self.save_and_close, fg_color="#15803d",
                      hover_color="#166534").pack(side="right")

    def _render_rows(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.row_vars = []
        self.delete_vars = []
        header = ctk.CTkFrame(self.scroll, fg_color="#1b2a40", corner_radius=8)
        header.pack(fill="x", pady=(0, 5))
        for text, width in [("Suppr.", 55), ("Actif", 55), ("Site", 210), ("Domaine / chemin", 300), ("Pays", 130), ("Notes", 220)]:
            ctk.CTkLabel(header, text=text, width=width, anchor="w",
                         font=ctk.CTkFont(weight="bold"), text_color="#dbeafe").pack(side="left", padx=5, pady=9)
        for index, site in enumerate(self.sites):
            row = ctk.CTkFrame(self.scroll,
                               fg_color=("#172338" if index % 2 == 0 else "#111c2e"),
                               corner_radius=7)
            row.pack(fill="x", pady=2)
            delete_var = tk.BooleanVar(value=False)
            ctk.CTkCheckBox(row, text="", variable=delete_var, width=40,
                            checkbox_width=17, checkbox_height=17).pack(side="left", padx=(10, 0), pady=8)
            self.delete_vars.append(delete_var)
            enabled_var = tk.BooleanVar(value=site.get("enabled", True))
            ctk.CTkCheckBox(row, text="", variable=enabled_var, width=40,
                            checkbox_width=19, checkbox_height=19,
                            command=lambda i=index, v=enabled_var: self.set_enabled(i, v.get())).pack(side="left", padx=(8, 0), pady=8)
            self.row_vars.append(enabled_var)
            ctk.CTkLabel(row, text=site["name"], width=210, anchor="w",
                         text_color="#f1f5f9").pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text=site["domain"], width=300, anchor="w",
                         text_color="#93c5fd").pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text=site.get("country", "International"), width=130,
                         anchor="w", text_color="#cbd5e1").pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(row, text=site.get("notes", ""), width=220, anchor="w",
                         text_color="#94a3b8").pack(side="left", padx=5, pady=8)
        self.count_label.configure(text=f"{len(self.sites)} sites • {sum(1 for s in self.sites if s.get('enabled'))} actifs")

    def set_enabled(self, index, value):
        self.sites[index]["enabled"] = bool(value)
        self._save_silently()
        self.count_label.configure(text=f"{len(self.sites)} sites • {sum(1 for s in self.sites if s.get('enabled'))} actifs")

    def set_all(self, value):
        for site in self.sites:
            site["enabled"] = value
        self._save_silently()
        self._render_rows()

    def add_site(self):
        name = self.name_entry.get().strip()
        domain = _normalize_domain(self.domain_entry.get())
        country = self.country_entry.get().strip() or "International"
        ok, error = _validate_site(name, domain)
        if not ok:
            messagebox.showwarning("Données invalides", error, parent=self)
            return
        if any(s["domain"].lower() == domain.lower() for s in self.sites):
            messagebox.showwarning("Site déjà présent", "Ce domaine existe déjà dans la liste.", parent=self)
            return
        self.sites.append({"name": name, "domain": domain, "enabled": True,
                           "country": country, "notes": "Site ajouté par l'utilisateur"})
        self.name_entry.delete(0, "end")
        self.domain_entry.delete(0, "end")
        self.country_entry.delete(0, "end")
        self._save_silently()
        self._render_rows()

    def delete_selected(self):
        # Selection means checked rows; avoid accidental deletion by confirming.
        selected = [i for i, var in enumerate(self.delete_vars) if var.get()]
        if not selected:
            messagebox.showinfo("Aucune sélection", "Coche les sites à supprimer.", parent=self)
            return
        if not messagebox.askyesno("Confirmer", f"Supprimer {len(selected)} site(s) coché(s) ?\nCette action est définitive.", parent=self):
            return
        self.sites = [s for i, s in enumerate(self.sites) if i not in set(selected)]
        self._save_silently()
        self._render_rows()

    def _save_silently(self):
        try:
            save_sites(self.sites)
        except OSError as exc:
            messagebox.showerror("Erreur d'enregistrement", str(exc), parent=self)

    def save_and_close(self):
        self._save_silently()
        if callable(self.on_change):
            self.on_change(self.sites)
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("Job Finder Pro — Démo du gestionnaire")
    root.geometry("450x220")
    ctk.CTkLabel(root, text="Gestionnaire de sites Job Finder",
                 font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(30, 8))
    ctk.CTkLabel(root, text="Ouvre le gestionnaire pour ajouter et gérer les sites.").pack(pady=5)
    ctk.CTkButton(root, text="🌐 Gérer les sites",
                  command=lambda: SiteManager(root)).pack(pady=18)
    root.mainloop()

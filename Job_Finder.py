# ================================================================
# JOB FINDER PRO v3.2
# Multi-Source Job Search
# Full Scrollable GUI
# CustomTkinter + DDGS + Pandas + OpenPyXL
# ================================================================

import re
import time
import threading
import webbrowser
from datetime import datetime
from urllib.parse import urlparse

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import customtkinter as ctk
import pandas as pd

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

from site_manager import SiteManager, load_sites


# ================================================================
# CONFIGURATION
# ================================================================

APP_NAME = "Job Finder Pro"
APP_VERSION = "3.2"


def _openrouter_settings_path():
    """User-local settings file used to remember the API key between runs."""
    import os
    from pathlib import Path
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "JobFinderPro"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


def _load_openrouter_key():
    """Read saved key; environment variable takes precedence."""
    import json, os
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(json.loads(_openrouter_settings_path().read_text(encoding="utf-8")).get("openrouter_api_key", "")).strip()
    except (OSError, ValueError, AttributeError):
        return ""


def _save_openrouter_key(key):
    """Save key locally so the user only needs to enter it once."""
    import json
    path = _openrouter_settings_path()
    path.write_text(json.dumps({"openrouter_api_key": key}, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        import os
        os.chmod(path, 0o600)
    except OSError:
        pass

# Search engines.
# Startpage intentionally excluded because of previous
# connection refused errors.
SEARCH_BACKENDS = "bing,google,brave,duckduckgo,mojeek,yahoo"

MAX_RESULTS_PER_QUERY = 8

QUERY_VARIANTS = [
    '"{keyword}" "{city}" "{country}" site:{domain}',
    '"{keyword} job" "{city}" "{country}" site:{domain}',
    '"{keyword} emploi" "{city}" "{country}" site:{domain}',
    '"{keyword} recrutement" "{city}" "{country}" site:{domain}',
]


# ================================================================
# JOB SOURCES
# ================================================================

JOB_SOURCES = {
    "Indeed": "indeed.com",
    "LinkedIn Jobs": "linkedin.com/jobs",
    "Glassdoor": "glassdoor.com",
    "Bayt": "bayt.com",
    "ReKrute": "rekrute.com",
    "Jobijoba": "jobijoba.com",
    "Welcome to the Jungle": "welcometothejungle.com",
    "Monster": "monster.com",
    "Jooble": "jooble.org",
    "CareerBuilder": "careerbuilder.com",
    "ZipRecruiter": "ziprecruiter.com",
    "SimplyHired": "simplyhired.com",
    "Talent.com": "talent.com",
    "Adzuna": "adzuna.com",
    "Careerjet": "careerjet.com",
    "Optioncarriere": "optioncarriere.com",
    "Emploi.ma": "emploi.ma",
    "MarocAnnonces": "marocannonces.com",
    "Novojob": "novojob.com",
    "Tanitjobs": "tanitjobs.com",
    "Keejob": "keejob.com",
    "ANAPEC": "anapec.org",
    "France Travail": "francetravail.fr",
    "Apec": "apec.fr",
    "HelloWork": "hellowork.com",
    "StepStone": "stepstone.com",
    "EURES": "eures.europa.eu",
    "XING Jobs": "xing.com/jobs",
    "JobTeaser": "jobteaser.com",
    "EuroJobs": "eurojobs.com",
    "JobisJob": "jobisjob.com",
    "GrabJobs": "grabjobs.co",
    "JobRapido": "jobrapido.com",
    "CareerBliss": "careerbliss.com",
    "Lensa": "lensa.com",
    "FlexJobs": "flexjobs.com",
}

# La liste persistante est gérée dans sites.json.
# Les sites ajoutés depuis la fenêtre de gestion seront utilisés
# directement par le moteur de recherche générique.
SAVED_SITES = load_sites()
JOB_SOURCES.clear()
JOB_SOURCES.update({
    site["name"]: site["domain"]
    for site in SAVED_SITES
})
SITE_ENABLED = {
    site["name"]: bool(site.get("enabled", True))
    for site in SAVED_SITES
}


# ================================================================
# COUNTRIES / CITIES
# ================================================================

COUNTRY_CITIES = {

    "All": [
        "All"
    ],

    "Maroc": [
        "All",
        "Casablanca",
        "Rabat",
        "Fès",
        "Marrakech",
        "Agadir",
        "Tanger",
        "Meknès",
        "Oujda",
        "Kenitra",
        "Tétouan",
        "El Jadida",
        "Safi",
        "Béni Mellal",
        "Nador",
        "Mohammedia",
        "Settat",
        "Khouribga",
        "Essaouira",
        "Ouarzazate",
    ],

    "France": [
        "All",
        "Paris",
        "Lyon",
        "Marseille",
        "Toulouse",
        "Bordeaux",
        "Lille",
        "Nantes",
        "Nice",
        "Strasbourg",
        "Montpellier",
        "Rennes",
        "Grenoble",
        "Dijon",
        "Rouen",
        "Reims",
    ],

    "Belgique": [
        "All",
        "Bruxelles",
        "Anvers",
        "Gand",
        "Liège",
        "Charleroi",
        "Namur",
        "Louvain",
    ],

    "Canada": [
        "All",
        "Montréal",
        "Toronto",
        "Vancouver",
        "Ottawa",
        "Calgary",
        "Québec",
        "Edmonton",
    ],

    "Suisse": [
        "All",
        "Genève",
        "Lausanne",
        "Zurich",
        "Berne",
        "Bâle",
        "Lugano",
    ],

    "Allemagne": [
        "All",
        "Berlin",
        "Munich",
        "Hamburg",
        "Frankfurt",
        "Cologne",
        "Stuttgart",
        "Düsseldorf",
    ],

    "Espagne": [
        "All",
        "Madrid",
        "Barcelona",
        "Valencia",
        "Seville",
        "Bilbao",
        "Malaga",
    ],

    "Italie": [
        "All",
        "Rome",
        "Milan",
        "Naples",
        "Turin",
        "Bologna",
        "Florence",
    ],

    "Portugal": [
        "All",
        "Lisbon",
        "Porto",
        "Braga",
        "Coimbra",
        "Faro",
    ],

    "Netherlands": [
        "All",
        "Amsterdam",
        "Rotterdam",
        "The Hague",
        "Utrecht",
        "Eindhoven",
    ],

    "United Kingdom": [
        "All",
        "London",
        "Manchester",
        "Birmingham",
        "Liverpool",
        "Leeds",
        "Bristol",
        "Edinburgh",
    ],

    "United States": [
        "All",
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Miami",
        "San Francisco",
        "Boston",
        "Seattle",
        "Washington",
    ],
}


# ================================================================
# HELPERS
# ================================================================

def clean_text(value):

    if value is None:
        return ""

    value = str(value)

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def normalize_url(url):

    if not url:
        return ""

    try:

        parsed = urlparse(
            url.strip()
        )

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/")

        return f"{scheme}://{netloc}{path}"

    except Exception:

        return url.lower().rstrip("/")


def make_safe_filename(value):

    value = str(
        value or "search"
    )

    value = re.sub(
        r'[<>:"/\\|?*]',
        "",
        value
    )

    value = value.replace(
        " ",
        "_"
    )

    value = re.sub(
        r"_+",
        "_",
        value
    )

    return value[:100]


def detect_source(url):

    url = url.lower()

    for source, domain in JOB_SOURCES.items():

        if domain.lower() in url:
            return source

    return "Other"


def extract_company(title, body):

    text = clean_text(body)

    patterns = [
        r"(?:at|chez|@)\s+([A-Z][A-Za-z0-9&.\- ]{2,60})",
        r"(?:company|entreprise)\s*[:\-]\s*([A-Za-z0-9&.\- ]{2,60})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            company = clean_text(
                match.group(1)
            )

            if len(company) > 2:
                return company

    return ""


def extract_location(
    text,
    country,
    city
):

    text = clean_text(text)

    if city != "All":

        if city.lower() in text.lower():
            return city

    if country != "All":

        if country.lower() in text.lower():
            return country

    return ""


def guess_published_date(text):

    text = clean_text(text)

    patterns = [

        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",

        r"\b\d+\s+(?:day|days|week|weeks|month|months)\s+ago\b",

        r"\bil y a\s+\d+\s+(?:jour|jours|semaine|semaines|mois)\b",

        r"\b\d+\s+(?:j|jours)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(0)

    return ""


# ================================================================
# SEARCH ENGINE
# ================================================================

class JobSearchEngine:

    def __init__(
        self,
        logger=None,
        stop_event=None
    ):

        self.logger = logger
        self.stop_event = stop_event

    def log(self, message):

        if self.logger:
            self.logger(message)

    def search(
        self,
        query,
        max_results=8
    ):

        if DDGS is None:

            raise RuntimeError(
                "Le module 'ddgs' n'est pas installé."
            )

        # --------------------------------------------------------
        # PRIMARY SEARCH
        # --------------------------------------------------------

        try:

            self.log(
                f"      ⚡ Recherche multi-backend"
            )

            with DDGS(
                timeout=10
            ) as ddgs:

                results = ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    timelimit=None,
                    max_results=max_results,
                    backend=SEARCH_BACKENDS
                )

                if results:
                    return list(results)

        except TypeError:

            self.log(
                "      ⚠️ Backend personnalisé "
                "non supporté par cette version."
            )

        except Exception as exc:

            self.log(
                "      ⚠️ Recherche échouée : "
                f"{type(exc).__name__}: {exc}"
            )

        # --------------------------------------------------------
        # FALLBACK
        # --------------------------------------------------------

        try:

            self.log(
                "      🔄 Fallback DDGS..."
            )

            with DDGS(
                timeout=10
            ) as ddgs:

                results = ddgs.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    timelimit=None,
                    max_results=max_results,
                    backend="auto"
                )

                return list(
                    results or []
                )

        except Exception as exc:

            self.log(
                "      ❌ Fallback échoué : "
                f"{type(exc).__name__}: {exc}"
            )

            return []


# ================================================================
# APPLICATION
# ================================================================

class JobFinderApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            f"{APP_NAME} v{APP_VERSION}"
        )

        self.geometry(
            "1500x950"
        )

        self.minsize(
            1100,
            700
        )

        ctk.set_appearance_mode(
            "dark"
        )

        ctk.set_default_color_theme(
            "blue"
        )

        self.stop_event = threading.Event()

        self.search_thread = None

        self.results = []

        self.result_urls = set()

        self.source_vars = {}

        self.setup_style()

        self.build_ui()

    # ============================================================
    # STYLE
    # ============================================================

    def setup_style(self):

        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except Exception:
            pass

        style.configure(
            "Treeview",
            rowheight=38,
            font=(
                "Segoe UI",
                10
            )
        )

        style.configure(
            "Treeview.Heading",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        )

    # ============================================================
    # BUILD UI
    # ============================================================

    def build_ui(self):

        # ========================================================
        # GLOBAL SCROLL AREA
        # ========================================================

        # Canvas principal
        self.main_canvas = tk.Canvas(
            self,
            bg="#1a1a1a",
            highlightthickness=0
        )

        self.main_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar principale
        self.main_scrollbar = ctk.CTkScrollbar(
            self,
            orientation="vertical",
            command=self.main_canvas.yview
        )

        self.main_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.main_canvas.configure(
            yscrollcommand=self.main_scrollbar.set
        )

        # Frame global
        self.main_content = ctk.CTkFrame(
            self.main_canvas,
            fg_color="transparent"
        )

        self.main_window = (
            self.main_canvas.create_window(
                (0, 0),
                window=self.main_content,
                anchor="nw"
            )
        )

        # Mise à jour de la zone scrollable
        self.main_content.bind(
            "<Configure>",
            self.update_main_scroll
        )

        # Largeur du contenu
        self.main_canvas.bind(
            "<Configure>",
            self.resize_main_content
        )

        # Mouse wheel globale
        self.main_canvas.bind(
            "<Enter>",
            self.enable_main_mousewheel
        )

        self.main_canvas.bind(
            "<Leave>",
            self.disable_main_mousewheel
        )

        # ========================================================
        # HEADER
        # ========================================================

        header = ctk.CTkFrame(
            self.main_content,
            corner_radius=0,
            height=85
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

        title = ctk.CTkLabel(
            header,
            text="🔎 JOB FINDER PRO",
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        title.pack(
            side="left",
            padx=25
        )

        subtitle = ctk.CTkLabel(
            header,
            text=(
                "Multi-source Job Search "
                "• 30+ plateformes"
            ),
            font=ctk.CTkFont(
                size=13
            )
        )

        subtitle.pack(
            side="left",
            padx=5
        )

        # ========================================================
        # SEARCH PANEL
        # ========================================================

        search_frame = ctk.CTkFrame(
            self.main_content,
            corner_radius=15
        )

        search_frame.pack(
            fill="x",
            padx=18,
            pady=15
        )

        # Domain
        ctk.CTkLabel(
            search_frame,
            text="💼 Domaine / Métier",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            padx=12,
            pady=(15, 5),
            sticky="w"
        )

        self.keyword_entry = ctk.CTkEntry(
            search_frame,
            width=300,
            height=42,
            placeholder_text=(
                "ex: développement web"
            )
        )

        self.keyword_entry.grid(
            row=1,
            column=0,
            padx=12,
            pady=(0, 15)
        )

        # Country
        ctk.CTkLabel(
            search_frame,
            text="🌍 Pays",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).grid(
            row=0,
            column=1,
            padx=12,
            pady=(15, 5),
            sticky="w"
        )

        self.country_combo = ctk.CTkComboBox(
            search_frame,
            width=230,
            height=42,
            values=list(
                COUNTRY_CITIES.keys()
            ),
            command=self.on_country_change
        )

        self.country_combo.set(
            "Maroc"
        )

        self.country_combo.grid(
            row=1,
            column=1,
            padx=12,
            pady=(0, 15)
        )

        # City
        ctk.CTkLabel(
            search_frame,
            text="📍 Ville",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).grid(
            row=0,
            column=2,
            padx=12,
            pady=(15, 5),
            sticky="w"
        )

        self.city_combo = ctk.CTkComboBox(
            search_frame,
            width=230,
            height=42,
            values=COUNTRY_CITIES["Maroc"]
        )

        self.city_combo.set(
            "All"
        )

        self.city_combo.grid(
            row=1,
            column=2,
            padx=12,
            pady=(0, 15)
        )

        # Search button
        self.search_button = ctk.CTkButton(
            search_frame,
            text="🚀 RECHERCHER",
            width=190,
            height=44,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            command=self.start_search
        )

        self.search_button.grid(
            row=1,
            column=3,
            padx=15,
            pady=(0, 15)
        )

        # Stop button
        self.stop_button = ctk.CTkButton(
            search_frame,
            text="⛔ STOP",
            width=120,
            height=44,
            fg_color="#B42318",
            hover_color="#D92D20",
            command=self.stop_search,
            state="disabled"
        )

        self.stop_button.grid(
            row=1,
            column=4,
            padx=10,
            pady=(0, 15)
        )

        # ========================================================
        # SOURCES
        # ========================================================

        source_outer = ctk.CTkFrame(
            self.main_content,
            corner_radius=15
        )

        source_outer.pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        source_header = ctk.CTkFrame(
            source_outer,
            fg_color="transparent"
        )

        source_header.pack(
            fill="x",
            padx=10,
            pady=(10, 5)
        )

        ctk.CTkLabel(
            source_header,
            text="🌐 Sources de recrutement",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        ).pack(
            side="left",
            padx=5
        )

        self.select_all_button = ctk.CTkButton(
            source_header,
            text="☑ Tout sélectionner",
            width=150,
            height=30,
            command=self.select_all_sources
        )

        self.select_all_button.pack(
            side="right",
            padx=5
        )

        self.clear_sources_button = ctk.CTkButton(
            source_header,
            text="☐ Tout désélectionner",
            width=160,
            height=30,
            command=self.clear_all_sources
        )

        self.clear_sources_button.pack(
            side="right",
            padx=5
        )

        self.manage_sources_button = ctk.CTkButton(
            source_header,
            text="⚙ Gérer les sites",
            width=135,
            height=30,
            fg_color="#1677ff",
            hover_color="#0f5fcf",
            command=self.open_site_manager
        )
        self.manage_sources_button.pack(
            side="right",
            padx=5
        )

        # ========================================================
        # SOURCE SCROLL AREA
        # ========================================================

        source_scroll_container = ctk.CTkFrame(
            source_outer,
            fg_color="transparent",
            height=170
        )

        source_scroll_container.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        source_scroll_container.pack_propagate(
            False
        )

        source_canvas = tk.Canvas(
            source_scroll_container,
            bg="#2b2b2b",
            highlightthickness=0
        )
        self.source_canvas = source_canvas

        source_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        source_scrollbar_y = ctk.CTkScrollbar(
            source_scroll_container,
            orientation="vertical",
            command=source_canvas.yview
        )

        source_scrollbar_y.pack(
            side="right",
            fill="y"
        )

        source_scrollbar_x = ctk.CTkScrollbar(
            source_scroll_container,
            orientation="horizontal",
            command=source_canvas.xview
        )

        source_scrollbar_x.pack(
            side="bottom",
            fill="x"
        )

        source_canvas.configure(
            yscrollcommand=source_scrollbar_y.set,
            xscrollcommand=source_scrollbar_x.set
        )

        source_inner = ctk.CTkFrame(
            source_canvas,
            fg_color="transparent"
        )
        self.source_inner = source_inner

        source_window = source_canvas.create_window(
            (0, 0),
            window=source_inner,
            anchor="nw"
        )

        def update_sources_scroll(
            event=None
        ):

            source_canvas.configure(
                scrollregion=source_canvas.bbox(
                    "all"
                )
            )

        source_inner.bind(
            "<Configure>",
            update_sources_scroll
        )

        def resize_source_width(
            event
        ):

            source_canvas.itemconfigure(
                source_window,
                width=event.width
            )

        source_canvas.bind(
            "<Configure>",
            resize_source_width
        )

        def source_mousewheel(
            event
        ):

            source_canvas.yview_scroll(
                int(
                    -1 *
                    (event.delta / 120)
                ),
                "units"
            )

        source_canvas.bind(
            "<Enter>",
            lambda e:
            source_canvas.bind_all(
                "<MouseWheel>",
                source_mousewheel
            )
        )

        source_canvas.bind(
            "<Leave>",
            lambda e:
            source_canvas.unbind_all(
                "<MouseWheel>"
            )
        )

        # Source checkboxes (liste persistante dans sites.json)
        self.refresh_source_checkboxes()

        # ========================================================
        # STATUS
        # ========================================================

        status_frame = ctk.CTkFrame(
            self.main_content,
            corner_radius=15
        )

        status_frame.pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="🟢 Prêt",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        self.status_label.pack(
            side="left",
            padx=15,
            pady=10
        )

        self.count_label = ctk.CTkLabel(
            status_frame,
            text="Résultats : 0",
            font=ctk.CTkFont(
                size=13
            )
        )

        self.count_label.pack(
            side="right",
            padx=15,
            pady=10
        )

        self.progress = ctk.CTkProgressBar(
            status_frame,
            width=400
        )

        self.progress.pack(
            side="right",
            padx=10,
            pady=10
        )

        self.progress.set(
            0
        )

        # ========================================================
        # RESULTS
        # ========================================================

        results_outer = ctk.CTkFrame(
            self.main_content,
            corner_radius=15
        )

        results_outer.pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        results_title = ctk.CTkLabel(
            results_outer,
            text="📋 Résultats des offres",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        results_title.pack(
            anchor="w",
            padx=15,
            pady=(10, 5)
        )

        results_frame = ctk.CTkFrame(
            results_outer,
            fg_color="transparent",
            height=360
        )

        results_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        results_frame.pack_propagate(
            False
        )

        columns = (
            "title",
            "company",
            "location",
            "country",
            "source",
            "published",
            "url",
            "description"
        )

        self.tree = ttk.Treeview(
            results_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "title": "Poste",
            "company": "Entreprise",
            "location": "Ville / Localisation",
            "country": "Pays",
            "source": "Source",
            "published": "Publié",
            "url": "URL",
            "description": "Description"
        }

        widths = {
            "title": 280,
            "company": 190,
            "location": 170,
            "country": 120,
            "source": 160,
            "published": 120,
            "url": 450,
            "description": 550
        }

        for col in columns:

            self.tree.heading(
                col,
                text=headings[col]
            )

            self.tree.column(
                col,
                width=widths[col],
                minwidth=100,
                anchor="w"
            )

        tree_y = ttk.Scrollbar(
            results_frame,
            orient="vertical",
            command=self.tree.yview
        )

        tree_x = ttk.Scrollbar(
            results_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=tree_y.set,
            xscrollcommand=tree_x.set
        )

        self.tree.pack(
            side="top",
            fill="both",
            expand=True
        )

        tree_y.pack(
            side="right",
            fill="y"
        )

        tree_x.pack(
            side="bottom",
            fill="x"
        )

        self.tree.bind(
            "<Double-1>",
            self.open_selected_url
        )

        # ========================================================
        # LOG
        # ========================================================

        log_outer = ctk.CTkFrame(
            self.main_content,
            corner_radius=15
        )

        log_outer.pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        log_title = ctk.CTkLabel(
            log_outer,
            text="📝 Logs / Progression",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        log_title.pack(
            anchor="w",
            padx=15,
            pady=(10, 5)
        )

        self.log_text = ctk.CTkTextbox(
            log_outer,
            height=230,
            font=(
                "Consolas",
                10
            )
        )

        self.log_text.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        # ========================================================
        # BOTTOM BUTTONS
        # ========================================================

        bottom = ctk.CTkFrame(
            self.main_content,
            corner_radius=15
        )

        bottom.pack(
            fill="x",
            padx=18,
            pady=(0, 20)
        )

        bottom_label = ctk.CTkLabel(
            bottom,
            text="💾 Export / Gestion",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        bottom_label.pack(
            side="left",
            padx=15
        )

        clear_button = ctk.CTkButton(
            bottom,
            text="🗑 Effacer",
            width=140,
            height=42,
            command=self.clear_results
        )

        clear_button.pack(
            side="right",
            padx=5,
            pady=10
        )

        self.export_csv_button = ctk.CTkButton(
            bottom,
            text="📄 Export CSV",
            width=160,
            height=42,
            command=self.export_csv
        )

        self.export_csv_button.pack(
            side="right",
            padx=5,
            pady=10
        )

        self.export_excel_button = ctk.CTkButton(
            bottom,
            text="📗 Export Excel",
            width=180,
            height=42,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            fg_color="#16803C",
            hover_color="#1E9B4B",
            command=self.export_excel
        )

        self.export_excel_button.pack(
            side="right",
            padx=8,
            pady=10
        )

        self.ai_career_button = ctk.CTkButton(
            bottom,
            text="✨ CV + Lettre IA",
            width=190,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6D28D9",
            hover_color="#5B21B6",
            command=self.start_ai_career_assistant
        )
        self.ai_career_button.pack(
            side="right",
            padx=8,
            pady=10
        )

    # ============================================================
    # AI CAREER ASSISTANT
    # ============================================================

    def start_ai_career_assistant(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Aucune offre sélectionnée",
                "Sélectionnez une offre dans le tableau avant de lancer l'analyse IA."
            )
            return

        values = self.tree.item(selected[0], "values")
        if not values or len(values) < 8:
            messagebox.showerror("Erreur", "Impossible de lire l'offre sélectionnée.")
            return

        job = {
            "Poste": values[0], "Entreprise": values[1],
            "Localisation": values[2], "Pays": values[3],
            "Source": values[4], "Publié": values[5],
            "URL": values[6], "Description": values[7],
        }

        cv_path = filedialog.askopenfilename(
            title="Choisir votre CV original (PDF)",
            filetypes=[("Fichiers PDF", "*.pdf")]
        )
        if not cv_path:
            return

        if not messagebox.askyesno(
            "Données et confidentialité",
            "Pour analyser cette candidature, le texte extrait de votre CV et les informations de l'offre seront envoyés au fournisseur de l'API IA. "
            "Ne continuez que si vous acceptez ce traitement.\n\nLe CV original ne sera pas modifié. Continuer ?"
        ):
            return

        api_key = _load_openrouter_key()
        if not api_key:
            api_key = simpledialog.askstring(
                "Clé API OpenRouter",
                "Collez votre clé API OpenRouter. Elle sera mémorisée localement sur cet ordinateur pour éviter de la ressaisir.",
                show="*", parent=self
            ) or ""
            api_key = api_key.strip()
            if api_key:
                try:
                    _save_openrouter_key(api_key)
                except OSError as exc:
                    messagebox.showwarning(
                        "Clé non mémorisée",
                        f"La clé sera utilisée pour cette analyse, mais n'a pas pu être enregistrée : {exc}"
                    )
        if not api_key:
            messagebox.showinfo("Clé API requise", "Ajoutez une clé OpenRouter valide pour lancer l'analyse.")
            return

        output_dir = filedialog.askdirectory(
            title="Choisir le dossier de sortie des PDF (Annuler = dossier par défaut)"
        ) or None

        self.ai_career_button.configure(state="disabled", text="⏳ Analyse IA...")
        self.log("🤖 Analyse IA lancée pour : " + str(job.get("Poste", "")))

        def worker():
            try:
                from ai_career_assistant import generate_documents
                result = generate_documents(cv_path=cv_path, job=job, api_key=api_key, output_dir=output_dir)
                self.after(0, lambda r=result: self._ai_career_finished(r))
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                self.after(0, lambda m=message: self._ai_career_failed(m))

        threading.Thread(target=worker, daemon=True).start()

    def _ai_career_finished(self, result):
        self.ai_career_button.configure(state="normal", text="✨ CV + Lettre IA")
        self.log(f"✅ Analyse IA terminée — compatibilité indicative : {result.get('match_score', '?')}/100")
        self.log("📄 CV : " + result.get("cv_pdf", ""))
        self.log("📄 Lettre : " + result.get("letter_pdf", ""))
        self.log("📄 Rapport : " + result.get("report_pdf", ""))
        messagebox.showinfo(
            "Documents générés",
            "Les 3 fichiers PDF ont été créés :\n\n"
            f"CV adapté : {result.get('cv_pdf', '')}\n\n"
            f"Lettre : {result.get('letter_pdf', '')}\n\n"
            f"Analyse : {result.get('report_pdf', '')}\n\n"
            f"Compatibilité indicative : {result.get('match_score', '?')}/100\n\n"
            "Relisez les trois documents avant de postuler."
        )

    def _ai_career_failed(self, message):
        self.ai_career_button.configure(state="normal", text="✨ CV + Lettre IA")
        self.log("❌ Erreur assistant IA : " + message)
        messagebox.showerror("Échec de l'analyse IA", message)

        # ========================================================
        # FOOTER
        # ========================================================

        footer = ctk.CTkLabel(
            self.main_content,
            text=(
                f"{APP_NAME} v{APP_VERSION} "
                "• Multi-source search"
            ),
            font=ctk.CTkFont(
                size=11
            )
        )

        footer.pack(
            pady=(0, 25)
        )

    # ============================================================
    # MAIN GLOBAL SCROLL
    # ============================================================

    def update_main_scroll(
        self,
        event=None
    ):

        self.main_canvas.configure(
            scrollregion=self.main_canvas.bbox(
                "all"
            )
        )

    def resize_main_content(
        self,
        event
    ):

        self.main_canvas.itemconfigure(
            self.main_window,
            width=event.width
        )

    def enable_main_mousewheel(
        self,
        event=None
    ):

        self.main_canvas.bind_all(
            "<MouseWheel>",
            self.main_mousewheel
        )

    def disable_main_mousewheel(
        self,
        event=None
    ):

        self.main_canvas.unbind_all(
            "<MouseWheel>"
        )

    def main_mousewheel(
        self,
        event
    ):

        self.main_canvas.yview_scroll(
            int(
                -1 *
                (event.delta / 120)
            ),
            "units"
        )

    # ============================================================
    # COUNTRY
    # ============================================================

    def on_country_change(
        self,
        country
    ):

        cities = COUNTRY_CITIES.get(
            country,
            ["All"]
        )

        self.city_combo.configure(
            values=cities
        )

        self.city_combo.set(
            "All"
        )

    # ============================================================
    # GESTION PERSISTANTE DES SITES
    # ============================================================

    def refresh_source_checkboxes(self):
        """Reconstruit la liste des sources selon sites.json."""
        if not hasattr(self, "source_inner"):
            return

        previous_values = {
            name: var.get()
            for name, var in self.source_vars.items()
        }

        for widget in self.source_inner.winfo_children():
            widget.destroy()

        self.source_vars.clear()
        columns = 4

        for index, source in enumerate(JOB_SOURCES.keys()):
            default_value = SITE_ENABLED.get(source, True)
            value = previous_values.get(source, default_value)
            var = tk.BooleanVar(value=value)
            self.source_vars[source] = var

            checkbox = ctk.CTkCheckBox(
                self.source_inner,
                text=source,
                variable=var,
                width=190
            )
            checkbox.grid(
                row=index // columns,
                column=index % columns,
                padx=12,
                pady=7,
                sticky="w"
            )

        self.source_inner.update_idletasks()
        self.source_canvas.configure(
            scrollregion=self.source_canvas.bbox("all")
        )

    def open_site_manager(self):
        """Ouvre la fenêtre d'ajout et de gestion des sites."""
        SiteManager(self, on_change=self.on_sites_changed)

    def on_sites_changed(self, sites):
        """Recharge les sites enregistrés après fermeture du gestionnaire."""
        global JOB_SOURCES, SITE_ENABLED

        JOB_SOURCES.clear()
        SITE_ENABLED.clear()

        for site in sites:
            name = str(site.get("name", "")).strip()
            domain = str(site.get("domain", "")).strip()
            if not name or not domain:
                continue
            JOB_SOURCES[name] = domain
            SITE_ENABLED[name] = bool(site.get("enabled", True))

        self.refresh_source_checkboxes()
        self.log(
            f"🌐 Liste des sites mise à jour : {len(JOB_SOURCES)} sites, "
            f"{sum(SITE_ENABLED.values())} activés."
        )

    # ============================================================
    # SOURCE BUTTONS
    # ============================================================

    def select_all_sources(
        self
    ):

        for var in self.source_vars.values():
            var.set(True)

    def clear_all_sources(
        self
    ):

        for var in self.source_vars.values():
            var.set(False)

    def get_selected_sources(
        self
    ):

        return [
            source
            for source, var
            in self.source_vars.items()
            if var.get()
        ]

    # ============================================================
    # LOG
    # ============================================================

    def log(
        self,
        message
    ):

        def write():

            self.log_text.insert(
                "end",
                message + "\n"
            )

            self.log_text.see(
                "end"
            )

        self.after(
            0,
            write
        )

    # ============================================================
    # STATUS
    # ============================================================

    def set_status(
        self,
        text
    ):

        self.after(
            0,
            lambda:
            self.status_label.configure(
                text=text
            )
        )

    def set_progress(
        self,
        value
    ):

        self.after(
            0,
            lambda:
            self.progress.set(
                value
            )
        )

    def update_count(
        self
    ):

        self.after(
            0,
            lambda:
            self.count_label.configure(
                text=(
                    f"Résultats : "
                    f"{len(self.results)}"
                )
            )
        )

    # ============================================================
    # START SEARCH
    # ============================================================

    def start_search(
        self
    ):

        if (
            self.search_thread
            and
            self.search_thread.is_alive()
        ):

            messagebox.showwarning(
                "Recherche en cours",
                "Une recherche est déjà en cours."
            )

            return

        keyword = clean_text(
            self.keyword_entry.get()
        )

        country = clean_text(
            self.country_combo.get()
        )

        city = clean_text(
            self.city_combo.get()
        )

        if not keyword:

            messagebox.showwarning(
                "Domaine manquant",
                "Veuillez entrer un domaine ou un métier."
            )

            return

        sources = (
            self.get_selected_sources()
        )

        if not sources:

            messagebox.showwarning(
                "Sources manquantes",
                "Sélectionnez au moins une source."
            )

            return

        # Reset results
        self.results = []

        self.result_urls = set()

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )

        self.log_text.delete(
            "1.0",
            "end"
        )

        self.stop_event.clear()

        self.search_button.configure(
            state="disabled"
        )

        self.stop_button.configure(
            state="normal"
        )

        self.progress.set(
            0
        )

        self.set_status(
            "🔎 Recherche en cours..."
        )

        self.log(
            "=" * 80
        )

        self.log(
            f"🚀 Recherche : {keyword}"
        )

        self.log(
            f"🌍 Pays : {country}"
        )

        self.log(
            f"📍 Ville : {city}"
        )

        self.log(
            f"🌐 Sources sélectionnées : "
            f"{len(sources)}"
        )

        self.log(
            f"⚡ Search backends : "
            f"{SEARCH_BACKENDS}"
        )

        self.log(
            "=" * 80
        )

        # Automatically scroll to logs
        self.after(
            100,
            self.scroll_to_logs
        )

        self.search_thread = threading.Thread(
            target=self.run_search,
            args=(
                keyword,
                country,
                city,
                sources
            ),
            daemon=True
        )

        self.search_thread.start()

    # ============================================================
    # SCROLL TO LOGS
    # ============================================================

    def scroll_to_logs(
        self
    ):

        self.main_canvas.update_idletasks()

        self.main_canvas.yview_moveto(
            0.65
        )

    # ============================================================
    # SEARCH WORKER
    # ============================================================

    def run_search(
        self,
        keyword,
        country,
        city,
        sources
    ):

        engine = JobSearchEngine(
            logger=self.log,
            stop_event=self.stop_event
        )

        total_sources = len(
            sources
        )

        completed_sources = 0

        for source in sources:

            if self.stop_event.is_set():
                break

            domain = JOB_SOURCES[
                source
            ]

            self.log("")
            self.log(
                f"🌐 SOURCE : {source}"
            )

            self.log(
                f"🔗 Domaine : {domain}"
            )

            source_results = 0

            for variant in QUERY_VARIANTS:

                if self.stop_event.is_set():
                    break

                query_city = (
                    city
                    if city != "All"
                    else ""
                )

                query_country = (
                    country
                    if country != "All"
                    else ""
                )

                query = variant.format(
                    keyword=keyword,
                    city=query_city,
                    country=query_country,
                    domain=domain
                )

                query = re.sub(
                    r"\s+",
                    " ",
                    query
                )

                self.log(
                    f"🔎 {query}"
                )

                try:

                    raw_results = (
                        engine.search(
                            query,
                            MAX_RESULTS_PER_QUERY
                        )
                    )

                    self.log(
                        f"      📊 "
                        f"{len(raw_results)} "
                        f"résultat(s)"
                    )

                    for raw in raw_results:

                        if self.stop_event.is_set():
                            break

                        result = (
                            self.parse_result(
                                raw,
                                source,
                                country,
                                city
                            )
                        )

                        if not result:
                            continue

                        if self.add_result(
                            result
                        ):

                            source_results += 1

                except Exception as exc:

                    self.log(
                        "      ❌ Erreur : "
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )

                time.sleep(
                    0.2
                )

            completed_sources += 1

            progress = (
                completed_sources
                /
                total_sources
            )

            self.set_progress(
                progress
            )

            self.set_status(
                f"🔎 {source} — "
                f"{len(self.results)} résultat(s)"
            )

            self.log(
                f"      ✅ "
                f"{source_results} "
                f"nouveau(x) résultat(s)"
            )

        self.after(
            0,
            self.search_finished
        )

    # ============================================================
    # PARSE RESULT
    # ============================================================

    def parse_result(
        self,
        raw,
        source,
        country,
        city
    ):

        if not isinstance(
            raw,
            dict
        ):
            return None

        title = clean_text(
            raw.get(
                "title",
                ""
            )
        )

        url = clean_text(
            raw.get(
                "href"
            )
            or raw.get(
                "url"
            )
            or ""
        )

        body = clean_text(
            raw.get(
                "body",
                ""
            )
        )

        if not title or not url:
            return None

        if not url.startswith(
            (
                "http://",
                "https://"
            )
        ):
            return None

        expected_domain = (
            JOB_SOURCES.get(
                source,
                ""
            )
        )

        if expected_domain:

            if (
                expected_domain.lower()
                not in
                url.lower()
            ):

                detected = detect_source(
                    url
                )

                if detected != source:
                    return None

        combined = (
            f"{title} {body}"
        )

        company = extract_company(
            title,
            body
        )

        location = extract_location(
            combined,
            country,
            city
        )

        published = guess_published_date(
            combined
        )

        return {
            "Poste": title,
            "Entreprise": company,
            "Localisation": location,
            "Pays": (
                country
                if country != "All"
                else ""
            ),
            "Source": source,
            "Publié": published,
            "URL": url,
            "Description": body,
        }

    # ============================================================
    # ADD RESULT
    # ============================================================

    def add_result(
        self,
        result
    ):

        url = normalize_url(
            result["URL"]
        )

        if not url:
            return False

        if url in self.result_urls:
            return False

        self.result_urls.add(
            url
        )

        self.results.append(
            result
        )

        self.after(
            0,
            lambda r=result:
            self.insert_tree_result(r)
        )

        self.update_count()

        return True

    # ============================================================
    # INSERT RESULT
    # ============================================================

    def insert_tree_result(
        self,
        result
    ):

        self.tree.insert(
            "",
            "end",
            values=(
                result["Poste"],
                result["Entreprise"],
                result["Localisation"],
                result["Pays"],
                result["Source"],
                result["Publié"],
                result["URL"],
                result["Description"],
            )
        )

    # ============================================================
    # SEARCH FINISHED
    # ============================================================

    def search_finished(
        self
    ):

        stopped = (
            self.stop_event.is_set()
        )

        self.search_button.configure(
            state="normal"
        )

        self.stop_button.configure(
            state="disabled"
        )

        self.progress.set(
            0 if stopped else 1
        )

        if stopped:

            self.set_status(
                f"⛔ Arrêté — "
                f"{len(self.results)} résultat(s)"
            )

            self.log("")
            self.log(
                "⛔ Recherche arrêtée."
            )

        else:

            self.set_status(
                f"✅ Terminé — "
                f"{len(self.results)} résultat(s)"
            )

            self.log("")
            self.log(
                "=" * 80
            )

            self.log(
                f"✅ Terminé : "
                f"{len(self.results)} résultat(s)"
            )

            self.log(
                "=" * 80
            )

        self.update_count()

        # Show logs after search
        self.after(
            100,
            self.scroll_to_logs
        )

    # ============================================================
    # STOP
    # ============================================================

    def stop_search(
        self
    ):

        if (
            self.search_thread
            and
            self.search_thread.is_alive()
        ):

            self.stop_event.set()

            self.set_status(
                "⛔ Arrêt demandé..."
            )

            self.log(
                "⛔ Arrêt demandé..."
            )

    # ============================================================
    # CLEAR
    # ============================================================

    def clear_results(
        self
    ):

        self.results = []

        self.result_urls = set()

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )

        self.count_label.configure(
            text="Résultats : 0"
        )

        self.status_label.configure(
            text="🟢 Prêt"
        )

        self.progress.set(
            0
        )

        self.log_text.delete(
            "1.0",
            "end"
        )

    # ============================================================
    # OPEN URL
    # ============================================================

    def open_selected_url(
        self,
        event=None
    ):

        selection = (
            self.tree.selection()
        )

        if not selection:
            return

        item = self.tree.item(
            selection[0]
        )

        values = item.get(
            "values",
            []
        )

        if len(values) > 6:

            url = values[6]

            if url:
                webbrowser.open(
                    url
                )

    # ============================================================
    # EXPORT CSV
    # ============================================================

    def export_csv(
        self
    ):

        if not self.results:

            messagebox.showwarning(
                "Export",
                "Aucun résultat à exporter."
            )

            return

        domain = clean_text(
            self.keyword_entry.get()
        )

        city = clean_text(
            self.city_combo.get()
        )

        filename = (
            "Job_Finder_"
            f"{make_safe_filename(domain)}_"
            f"{make_safe_filename(city)}.csv"
        )

        path = filedialog.asksaveasfilename(
            title="Exporter CSV",
            initialfile=filename,
            defaultextension=".csv",
            filetypes=[
                (
                    "CSV files",
                    "*.csv"
                ),
                (
                    "All files",
                    "*.*"
                )
            ]
        )

        if not path:
            return

        try:

            df = pd.DataFrame(
                self.results
            )

            df.to_csv(
                path,
                index=False,
                encoding="utf-8-sig"
            )

            self.log(
                f"📄 CSV exporté : {path}"
            )

            messagebox.showinfo(
                "Export terminé",
                (
                    "CSV exporté avec succès.\n\n"
                    f"{path}"
                )
            )

        except Exception as exc:

            messagebox.showerror(
                "Erreur CSV",
                str(exc)
            )

    # ============================================================
    # EXPORT EXCEL
    # ============================================================

    def export_excel(
        self
    ):

        if not self.results:

            messagebox.showwarning(
                "Export Excel",
                "Aucun résultat à exporter."
            )

            return

        domain = clean_text(
            self.keyword_entry.get()
        )

        country = clean_text(
            self.country_combo.get()
        )

        city = clean_text(
            self.city_combo.get()
        )

        filename = (
            "Job_Finder_"
            f"{make_safe_filename(domain)}_"
            f"{make_safe_filename(city)}.xlsx"
        )

        path = filedialog.asksaveasfilename(
            title="Exporter Excel",
            initialfile=filename,
            defaultextension=".xlsx",
            filetypes=[
                (
                    "Excel files",
                    "*.xlsx"
                ),
                (
                    "All files",
                    "*.*"
                )
            ]
        )

        if not path:
            return

        try:

            df = pd.DataFrame(
                self.results
            )

            with pd.ExcelWriter(
                path,
                engine="openpyxl"
            ) as writer:

                # ------------------------------------------------
                # RESULTS
                # ------------------------------------------------

                df.to_excel(
                    writer,
                    sheet_name="Job Results",
                    index=False
                )

                worksheet = writer.sheets[
                    "Job Results"
                ]

                worksheet.freeze_panes = (
                    "A2"
                )

                worksheet.auto_filter.ref = (
                    worksheet.dimensions
                )

                widths = {
                    "A": 42,
                    "B": 28,
                    "C": 25,
                    "D": 20,
                    "E": 25,
                    "F": 20,
                    "G": 65,
                    "H": 90
                }

                for column, width in widths.items():

                    worksheet.column_dimensions[
                        column
                    ].width = width

                for row in worksheet.iter_rows():

                    for cell in row:

                        cell.alignment = (
                            cell.alignment.copy(
                                wrap_text=True,
                                vertical="top"
                            )
                        )

                for cell in worksheet[1]:

                    cell.font = (
                        cell.font.copy(
                            bold=True
                        )
                    )

                # ------------------------------------------------
                # SEARCH INFO
                # ------------------------------------------------

                info = pd.DataFrame(
                    [
                        {
                            "Information": "Domaine",
                            "Valeur": domain
                        },
                        {
                            "Information": "Pays",
                            "Valeur": country
                        },
                        {
                            "Information": "Ville",
                            "Valeur": city
                        },
                        {
                            "Information":
                                "Nombre de résultats",
                            "Valeur":
                                len(self.results)
                        },
                        {
                            "Information":
                                "Date de recherche",
                            "Valeur":
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                        },
                        {
                            "Information":
                                "Nombre de sources",
                            "Valeur":
                                len(
                                    self.get_selected_sources()
                                )
                        }
                    ]
                )

                info.to_excel(
                    writer,
                    sheet_name="Search Info",
                    index=False
                )

                info_sheet = writer.sheets[
                    "Search Info"
                ]

                info_sheet.column_dimensions[
                    "A"
                ].width = 30

                info_sheet.column_dimensions[
                    "B"
                ].width = 60

            self.log(
                f"📗 Excel exporté : {path}"
            )

            messagebox.showinfo(
                "Export terminé",
                (
                    "Excel exporté avec succès.\n\n"
                    f"{path}"
                )
            )

        except Exception as exc:

            self.log(
                f"❌ Erreur Excel : {exc}"
            )

            messagebox.showerror(
                "Erreur Excel",
                str(exc)
            )


# ================================================================
# MAIN
# ================================================================

def main():

    if DDGS is None:

        root = tk.Tk()

        root.withdraw()

        messagebox.showerror(
            "Module manquant",
            (
                "Le module 'ddgs' n'est pas installé.\n\n"
                "Exécutez :\n\n"
                "python -m pip install -U ddgs"
            )
        )

        root.destroy()

        return

    app = JobFinderApp()

    app.mainloop()


# ================================================================
# RUN
# ================================================================

if __name__ == "__main__":
    main()
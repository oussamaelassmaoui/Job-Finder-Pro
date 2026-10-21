"""AI career assistant for Job Finder Pro.
Generates a tailored CV, motivation letter and job-match report as PDF files.
Requires OPENROUTER_API_KEY or an API key supplied at runtime by the GUI.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


def extract_pdf_text(pdf_path: str) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("La bibliothèque PyMuPDF manque. Installez les dépendances du projet.") from exc

    chunks = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            chunks.append(page.get_text("text"))
    text = "\n".join(chunks).strip()
    if len(text) < 80:
        raise ValueError(
            "Le PDF contient très peu de texte. S'il s'agit d'un scan, il faut d'abord appliquer un OCR."
        )
    return text[:28000]


def _build_pdf(path: Path, title: str, story: list) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="DocTitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=colors.HexColor("#163A5F"), alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="SectionCustom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor("#163A5F"), spaceBefore=10, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, alignment=TA_LEFT, spaceAfter=4))
    styles.add(ParagraphStyle(name="SmallCustom", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=8, leading=10, textColor=colors.HexColor("#555555"), spaceAfter=5))

    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=1.6*cm, bottomMargin=1.6*cm, title=title, author="Job Finder Pro")
    doc.build(story)


def _p(text: str, style="BodyCustom"):
    text = str(text or "").strip().replace("\n", "<br/>\n")
    return __import__("reportlab.platypus", fromlist=["Paragraph"]).Paragraph(escape(text).replace("&lt;br/&gt;", "<br/>"), style)


def _bullet(text: str):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    # HTML escaping prevents model text from being interpreted as markup.
    return Paragraph("• " + escape(str(text)), getSampleStyleSheet()["BodyText"])


def _safe_filename(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", text or "Job")
    return value.strip("_")[:60] or "Job"


def generate_documents(cv_path: str, job: dict, api_key: str | None = None, output_dir: str | None = None, model: str = "openrouter/free") -> dict:
    """Analyze a job against the real CV and create three PDF files."""
    key = (api_key or os.environ.get("OPENROUTER_API_KEY", "")).strip()
    if not key:
        raise ValueError("Clé API OpenRouter absente. Saisissez-la dans la fenêtre ou définissez OPENROUTER_API_KEY.")
    cv_text = extract_pdf_text(cv_path)
    job_text = "\n".join(f"{k}: {v}" for k, v in job.items() if v)
    prompt = f"""
Tu es un conseiller en recrutement francophone. Analyse le CV réel ci-dessous et l'offre d'emploi.
Réponds uniquement en JSON valide. Rédige en français professionnel.
RÈGLES STRICTES :
- N'invente jamais d'expérience, diplôme, certification, compétence, langue, employeur, date ou résultat.
- Ne transforme pas une compétence souhaitée en compétence acquise si elle n'apparaît pas dans le CV.
- Tu peux reformuler, réorganiser et mettre en valeur les informations déjà présentes.
- Si une information manque, omets-la ou indique-la dans gaps; ne la fabrique pas.
- Pour le CV, garde les noms d'employeurs, dates, diplômes et faits identifiables fidèles au CV source.
- Ne promets pas un recrutement et ne prétends pas connaître les critères internes de l'entreprise.
- Le score est une estimation indicative de compatibilité, pas une probabilité d'embauche.

Retourne ces clés JSON :
{{
 "job_title": "titre du poste",
 "company": "entreprise ou chaîne vide",
 "match_score": 0,
 "match_summary": "résumé court et nuancé",
 "strengths": ["élément réel du CV correspondant à l'offre"],
 "gaps": ["exigence absente ou non démontrée dans le CV"],
 "keywords_to_emphasize": ["mot-clé pertinent et véridique"],
 "cv": {{
   "full_name": "nom seulement s'il est présent",
   "contact": "coordonnées seulement si présentes, sans inventer",
   "headline": "titre professionnel",
   "summary": "résumé professionnel personnalisé",
   "skills": ["compétences présentes dans le CV"],
   "experience": [{{"role":"poste", "company":"employeur", "dates":"dates", "bullets":["réalisation ou responsabilité issue du CV source"]}}],
   "education": [{{"degree":"diplôme", "institution":"établissement", "dates":"dates"}}],
   "languages": ["langues et niveaux uniquement si indiqués"],
   "projects": [{{"name":"nom du projet présent dans le CV", "description":"description fidèle au CV source"}}],
   "certifications": ["certifications présentes dans le CV"]
 }},
 "motivation_letter": "lettre de motivation complète, personnalisée et prête à relire, sans coordonnées ni faits inventés",
 "disclaimer": "éléments à vérifier avant candidature"
}}

OFFRE D'EMPLOI :
{job_text[:10000]}

TEXTE DU CV ORIGINAL :
{cv_text}
"""
    # OpenRouter expose une API compatible avec le format Chat Completions.
    import requests
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu aides à préparer des candidatures exactes, honnêtes et adaptées. Respecte strictement les faits source. Réponds uniquement en JSON valide, sans markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 12000,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openrouter.ai/",
        "X-Title": "Job Finder Pro",
    }
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=(15, 180))
    except requests.RequestException as exc:
        raise RuntimeError(f"Connexion à OpenRouter impossible : {exc}") from exc
    if response.status_code >= 400:
        try:
            error_obj = response.json().get("error", {})
            detail = error_obj.get("message") or response.text
        except (ValueError, AttributeError):
            detail = response.text
        if response.status_code in (401, 403):
            hint = "Vérifiez votre clé API OpenRouter sur https://openrouter.ai/keys."
        elif response.status_code == 402:
            hint = "Le modèle demandé peut nécessiter des crédits. Essayez openrouter/free et vérifiez les limites de votre compte."
        elif response.status_code == 429:
            hint = "Limite de requêtes atteinte. Attendez un peu ou essayez plus tard; les modèles gratuits ont des quotas."
        elif response.status_code >= 500:
            hint = "Le fournisseur ou le modèle est temporairement indisponible. Réessayez dans quelques minutes."
        else:
            hint = "Vérifiez le modèle configuré et réessayez."
        raise RuntimeError(f"Erreur OpenRouter HTTP {response.status_code}: {detail}. {hint}")
    try:
        body = response.json()
        raw = body["choices"][0]["message"]["content"]
        if isinstance(raw, list):
            raw = "\n".join(str(part.get("text", "")) for part in raw if isinstance(part, dict))
        raw = str(raw or "").strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"\s*```$", "", raw)
        if not raw:
            raise ValueError("contenu vide")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenRouter n'a pas renvoyé de réponse exploitable. Réessayez ou changez de modèle.") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("La réponse IA n'a pas pu être lue comme JSON. Réessayez.") from exc

    out_dir = Path(output_dir) if output_dir else Path(cv_path).resolve().parent / "JobFinder_AI_Applications"
    out_dir.mkdir(parents=True, exist_ok=True)
    job_name = _safe_filename(data.get("job_title") or job.get("Poste") or "Candidature")
    company = _safe_filename(data.get("company") or job.get("Entreprise") or "Entreprise")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{stamp}_{job_name}_{company}"

    from reportlab.platypus import Paragraph, Spacer, HRFlowable, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="AIHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#163A5F"), spaceBefore=9, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle(name="AIBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=4))
    styles.add(ParagraphStyle(name="AITitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#163A5F"), alignment=TA_CENTER, spaceAfter=7))
    def para(t, style="AIBody"):
        return Paragraph(escape(str(t or "")).replace("\n", "<br/>"), styles[style])
    def heading(t):
        return Paragraph(escape(t), styles["AIHeading"])
    def bullets(items):
        return [para("• " + str(x)) for x in (items or []) if str(x).strip()]

    # Tailored CV PDF — compact, structured, one-page-oriented layout.
    # The PDF source is text-extracted above; do not fabricate a portrait/photo.
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    cv = data.get("cv") or {}
    navy = colors.HexColor("#163A5F")
    blue = colors.HexColor("#315B86")
    styles_cv = getSampleStyleSheet()
    styles_cv.add(ParagraphStyle(name="CVNameCompact", parent=styles_cv["Title"], fontName="Helvetica-Bold", fontSize=20, leading=23, alignment=TA_CENTER, textColor=navy, spaceAfter=1))
    styles_cv.add(ParagraphStyle(name="CVHeadlineCompact", parent=styles_cv["Normal"], fontName="Helvetica-Bold", fontSize=9.5, leading=11, alignment=TA_CENTER, textColor=blue, spaceAfter=2))
    styles_cv.add(ParagraphStyle(name="CVContactCompact", parent=styles_cv["Normal"], fontSize=8, leading=9.5, alignment=TA_CENTER, spaceAfter=7))
    styles_cv.add(ParagraphStyle(name="CVSectionCompact", parent=styles_cv["Normal"], fontName="Helvetica-Bold", fontSize=9.2, leading=11, textColor=navy, spaceBefore=7, spaceAfter=3, keepWithNext=True))
    styles_cv.add(ParagraphStyle(name="CVBodyCompact", parent=styles_cv["BodyText"], fontName="Helvetica", fontSize=8.35, leading=10.6, spaceAfter=2.4, alignment=TA_LEFT))
    styles_cv.add(ParagraphStyle(name="CVRoleCompact", parent=styles_cv["BodyText"], fontName="Helvetica-Bold", fontSize=8.8, leading=10.4, textColor=navy, spaceBefore=4, spaceAfter=1.2, keepWithNext=True))
    styles_cv.add(ParagraphStyle(name="CVMetaCompact", parent=styles_cv["BodyText"], fontName="Helvetica-Oblique", fontSize=7.8, leading=9.2, textColor=blue, spaceAfter=1.2))

    def cp(value, style="CVBodyCompact"):
        return Paragraph(escape(str(value or "")).replace("\n", "<br/>").replace("&lt;br/&gt;", "<br/>"), styles_cv[style])
    def csection(title):
        return [cp(title.upper(), "CVSectionCompact"), HRFlowable(width="100%", thickness=0.5, color=blue, spaceAfter=1.5)]
    def cbullets(items):
        return [cp("• " + str(item)) for item in (items or []) if str(item).strip()]

    # Add the portrait extracted from the original CV PDF, without changing
    # the remaining CV content or layout. If no embedded image is available,
    # keep the existing text-only header.
    header_text = [cp(cv.get("full_name") or "CV professionnel", "CVNameCompact")]
    if cv.get("headline"): header_text.append(cp(cv["headline"], "CVHeadlineCompact"))
    if cv.get("contact"): header_text.append(cp(cv["contact"], "CVContactCompact"))

    portrait = None
    try:
        import fitz
        from reportlab.platypus import Image as RLImage, Table as RLTable, TableStyle as RLTableStyle
        with fitz.open(cv_path) as original_doc:
            for original_page in original_doc:
                images = original_page.get_images(full=True)
                if images:
                    extracted = original_doc.extract_image(images[0][0])
                    portrait_path = out_dir / f"{prefix}_portrait.{extracted.get('ext', 'png')}"
                    portrait_path.write_bytes(extracted["image"])
                    portrait = RLImage(str(portrait_path), width=2.35*cm, height=2.65*cm, kind="proportional")
                    break
    except Exception:
        portrait = None

    if portrait is not None:
        header = RLTable([[portrait, header_text]], colWidths=[2.7*cm, 14.0*cm], hAlign="LEFT")
        header.setStyle(RLTableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story_cv = [header]
    else:
        story_cv = header_text
    story_cv.append(HRFlowable(width="100%", thickness=1, color=navy, spaceAfter=2))

    if cv.get("summary"):
        story_cv += csection("Profil professionnel") + [cp(cv["summary"]), Spacer(1, 3)]
    if cv.get("experience"):
        story_cv += csection("Expérience professionnelle")
        for exp in cv.get("experience", []):
            role = " — ".join(str(x) for x in [exp.get("role"), exp.get("company")] if x)
            dates = str(exp.get("dates") or "")
            block = [cp(role, "CVRoleCompact")]
            if dates: block.append(cp(dates, "CVMetaCompact"))
            block += cbullets(exp.get("bullets", []))
            story_cv.append(KeepTogether(block))
            story_cv.append(Spacer(1, 3))
    if cv.get("skills"):
        story_cv += csection("Compétences techniques")
        skills = [str(x).strip() for x in cv["skills"] if str(x).strip()]
        # Compact inline list instead of one oversized vertical bullet per skill.
        story_cv.append(cp(" • ".join(skills)))
    if cv.get("projects"):
        story_cv += csection("Projets sélectionnés")
        projects = []
        for project in cv.get("projects", []):
            if isinstance(project, dict):
                line = " — ".join(str(x) for x in [project.get("name"), project.get("description")] if x)
            else:
                line = str(project)
            if line.strip(): projects.append("• " + line)
        if projects: story_cv.append(cp("   |   ".join(projects)))
        story_cv.append(Spacer(1, 3))
    if cv.get("education"):
        story_cv += csection("Formation")
        for edu in cv.get("education", []):
            line = " — ".join(str(x) for x in [edu.get("degree"), edu.get("institution"), edu.get("dates")] if x)
            if line.strip(): story_cv.append(cp(line))
    if cv.get("languages"):
        story_cv += csection("Langues") + [cp(" • ".join(str(x) for x in cv["languages"] if str(x).strip()))]
    if cv.get("certifications"):
        story_cv += csection("Certifications") + [cp(" • ".join(str(x) for x in cv["certifications"] if str(x).strip()))]

    cv_path_out = out_dir / f"{prefix}_CV_adapte.pdf"
    cv_doc = SimpleDocTemplate(str(cv_path_out), pagesize=A4, rightMargin=1.55*cm, leftMargin=1.55*cm, topMargin=1.15*cm, bottomMargin=1.15*cm, title="CV adapté", author="Job Finder Pro")
    cv_doc.build(story_cv)

    # Motivation letter PDF
    letter_path = out_dir / f"{prefix}_Lettre_motivation.pdf"
    letter_story = [para("Lettre de motivation", "AITitle"), para(f"Poste : {data.get('job_title') or job.get('Poste', '')}"), para(f"Entreprise : {data.get('company') or job.get('Entreprise', '')}"), Spacer(1, 8)]
    letter_text = str(data.get("motivation_letter") or "").strip()
    if not letter_text:
        letter_text = "La génération de la lettre n'a pas retourné de contenu. Relancez l'analyse."
    for paragraph in re.split(r"\n\s*\n", letter_text):
        if paragraph.strip(): letter_story.append(para(paragraph.strip()))
    _build_pdf(letter_path, "Lettre de motivation", letter_story)

    # Match report PDF
    report_path = out_dir / f"{prefix}_Analyse_compatibilite.pdf"
    score = data.get("match_score", 0)
    try: score = max(0, min(100, int(score)))
    except (TypeError, ValueError): score = 0
    report_story = [para("Analyse de compatibilité", "AITitle"), para(f"Poste : {data.get('job_title') or job.get('Poste', '')}"), para(f"Entreprise : {data.get('company') or job.get('Entreprise', '')}"), para(f"Score indicatif : {score}/100", "AIHeading"), para(data.get("match_summary", "")), heading("Points forts du CV"), *bullets(data.get("strengths", [])), heading("Écarts ou compétences non démontrées"), *bullets(data.get("gaps", [])), heading("Mots-clés à mettre en valeur"), *bullets(data.get("keywords_to_emphasize", [])), heading("À vérifier avant l'envoi"), para(data.get("disclaimer", "Vérifiez toutes les informations et coordonnées avant d'envoyer la candidature.")), Spacer(1, 8), para("Le score est une estimation automatisée et ne prédit pas la décision du recruteur.")]
    _build_pdf(report_path, "Analyse de compatibilité", report_story)

    return {"cv_pdf": str(cv_path_out), "letter_pdf": str(letter_path), "report_pdf": str(report_path), "match_score": score, "output_dir": str(out_dir)}

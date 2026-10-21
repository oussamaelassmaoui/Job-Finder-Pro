# Changelog

Job Finder Pro - Corrections du 21/10/2026

1) CV PDF : taille de texte augmentée (nom, titres, contenu, dates) et espacements de sections plus confortables afin de mieux utiliser la page A4 et d'éviter un texte trop petit et tassé.
2) Clé OpenRouter : la clé est demandée la première fois seulement puis enregistrée dans %APPDATA%\JobFinderPro\settings.json pour les lancements suivants. La variable d'environnement OPENROUTER_API_KEY reste prioritaire.

Sécurité : settings.json contient la clé en texte lisible dans le profil Windows local. Ne partagez pas ce fichier ni le dossier AppData de l'application. Pour supprimer la clé mémorisée, supprimez %APPDATA%\JobFinderPro\settings.json.

Installation : décompressez dans un nouveau dossier, lancez Installer_dependances.bat, puis Lancer_Job_Finder.bat.

# Job Finder Pro

**Job Finder Pro** is a Windows desktop application written in Python to search job listings from configured sources and help prepare job-application documents with an AI assistant.

> **Status:** Community/open-source release preparation. Please test the app on your own machine before relying on it.

## Features

- Search job listings using configured search backends and source websites.
- Manage the list of job-search sources in `sites.json`.
- Select a job listing and a PDF CV to generate:
  - an adapted CV,
  - a cover letter,
  - a job-fit summary report.
- Use OpenRouter for the AI-assisted document generation.

The AI-generated documents may contain errors. Always check dates, employers, qualifications, skills, and every other claim before sending an application.

## Requirements

- Windows
- Python 3.10 or newer recommended
- Internet connection for job search and AI features
- An OpenRouter API key for AI document generation; API usage may incur charges according to your provider/account and selected model.

## Installation

1. Download or clone this repository.
2. Install Python and ensure it is available from Command Prompt.
3. In the project directory, run:

   ```bat
   python -m pip install -r requirements.txt
   ```

   Alternatively, on Windows, run `Installer_dependances.bat`.
4. Start the app:

   ```bat
   python Job_Finder.py
   ```

   Or run `Lancer_Job_Finder.bat`.

## OpenRouter API key

Set `OPENROUTER_API_KEY` as an environment variable, or enter the key in the app when prompted.

The current Windows app can save the key locally at:

`%APPDATA%\JobFinderPro\settings.json`

That local settings file contains the key in readable text. **Never commit or share it.** The repository's `.gitignore` excludes common secret/configuration files, but always inspect `git status` and the staged files before publishing.

## Privacy

When you use AI document generation, text extracted from your CV and details from the selected job listing are sent to OpenRouter's API for processing. Do not use this feature unless you are comfortable sharing that information with the provider. Review the provider's current terms and privacy policy before use.

Job-source websites may have their own terms, rate limits, and restrictions. Use the application responsibly and respect each site's terms and robots/access policies.

## Configuration

- `sites.json` contains the configured job-search sources.
- `requirements.txt` lists Python dependencies.
- `ai_career_assistant.py` contains the AI-assisted CV/cover-letter generation logic.

## Contributing

Issues and pull requests are welcome. Please:
- describe bugs with clear reproduction steps,
- avoid posting CVs, personal information, API keys, or other secrets in issues,
- test changes before submitting a pull request.

## Developer / Author

**Name:** oussama elassmaoui

- **GitHub:** [https://github.com/oussamaelassmaoui](https://github.com/oussamaelassmaoui)
- **Email:** [oussama.assmaoui@gmail.com](mailto:oussama.assmaoui@gmail.com)
- **LinkedIn:** [linkedin.com/in/oussamaelassmaoui](https://linkedin.com/in/oussamaelassmaoui)

## License

This project is distributed under the **GNU General Public License v3.0 (GPL-3.0-only)**. See [`LICENSE`](LICENSE) for the full license text.

Third-party Python packages and external websites remain subject to their own licenses and terms.
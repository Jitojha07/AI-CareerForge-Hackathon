from flask import Flask, render_template, request
import os
import re
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)

# Upload folder configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Resume keywords
KEYWORDS = [
    "python", "java", "c++", "javascript", "sql", "html", "css",
    "react", "node", "flask", "django", "machine learning",
    "data structures", "algorithms", "git", "github"
]


def extract_text(filepath):
    """
    Extract text from PDF or DOCX file.
    """
    text = ""

    if filepath.lower().endswith(".pdf"):
        reader = PdfReader(filepath)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "

    elif filepath.lower().endswith(".docx"):
        doc = Document(filepath)
        for para in doc.paragraphs:
            text += para.text + " "

    return text.lower()


def score_resume(text):
    """
    Score resume based on sections and keywords.
    """
    score = 0
    suggestions = []

    # Technical keywords
    found_keywords = [kw for kw in KEYWORDS if kw in text]
    keyword_score = min(len(found_keywords) * 3, 30)
    score += keyword_score

    if keyword_score < 15:
        suggestions.append("Add more relevant technical keywords to your resume.")

    # Projects section
    if "project" in text:
        score += 20
    else:
        suggestions.append("Include a Projects section with detailed descriptions.")

    # Experience section
    if "experience" in text or "internship" in text:
        score += 20
    else:
        suggestions.append("Add internship or work experience if available.")

    # Education section
    if "education" in text:
        score += 10
    else:
        suggestions.append("Include an Education section.")

    # Email
    if re.search(r"\\S+@\\S+", text):
        score += 10
    else:
        suggestions.append("Add a professional email address.")

    # GitHub
    if "github.com" in text:
        score += 5
    else:
        suggestions.append("Add your GitHub profile link.")

    # LinkedIn
    if "linkedin.com" in text:
        score += 5
    else:
        suggestions.append("Add your LinkedIn profile link.")

    return min(score, 100), suggestions


def score_technical(skills):
    """
    Score technical skills entered by the user.
    """
    skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]

    if not skill_list:
        return 0, ["Add your technical skills."]

    score = min(len(skill_list) * 8, 100)

    suggestions = []
    important_skills = [
        "python",
        "java",
        "sql",
        "data structures",
        "algorithms",
        "git"
    ]

    for skill in important_skills:
        if skill not in skill_list:
            suggestions.append(f"Consider learning {skill.title()}.")

    return score, suggestions


def score_communication(rating):
    """
    Score communication based on self-rating (1-10).
    """
    try:
        rating = int(rating)
    except ValueError:
        rating = 5

    rating = max(1, min(10, rating))
    score = rating * 10

    suggestions = []
    if rating < 7:
        suggestions.append("Practice speaking clearly and confidently.")
        suggestions.append("Record mock interview answers and review them.")

    return score, suggestions


def score_portfolio(github, linkedin):
    """
    Score GitHub and LinkedIn presence.
    """
    score = 0
    suggestions = []

    if github.strip():
        score += 50
    else:
        suggestions.append("Create a GitHub profile and upload your projects.")

    if linkedin.strip():
        score += 50
    else:
        suggestions.append("Create a LinkedIn profile and keep it updated.")

    return score, suggestions


def calculate_overall_score(
    resume_score,
    technical_score,
    communication_score,
    portfolio_score
):
    """
    Weighted overall interview readiness score.
    """
    final_score = (
        resume_score * 0.35 +
        technical_score * 0.30 +
        communication_score * 0.20 +
        portfolio_score * 0.15
    )

    return round(final_score, 2)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    # Get form data
    resume_file = request.files["resume"]
    skills = request.form["skills"]
    communication = request.form["communication"]
    github = request.form["github"]
    linkedin = request.form["linkedin"]

    # Save uploaded file
    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        resume_file.filename
    )
    resume_file.save(filepath)

    # Extract resume text
    resume_text = extract_text(filepath)

    # Calculate scores
    resume_score, resume_suggestions = score_resume(resume_text)
    technical_score, technical_suggestions = score_technical(skills)
    communication_score, communication_suggestions = score_communication(
        communication
    )
    portfolio_score, portfolio_suggestions = score_portfolio(
        github,
        linkedin
    )

    # Final score
    final_score = calculate_overall_score(
        resume_score,
        technical_score,
        communication_score,
        portfolio_score
    )

    # Readiness level
    if final_score >= 85:
        readiness = "Excellent - You are highly interview ready."
    elif final_score >= 70:
        readiness = "Good - Minor improvements needed."
    elif final_score >= 50:
        readiness = "Average - Significant improvement recommended."
    else:
        readiness = "Needs Preparation - Focus on fundamentals."

    # Combine suggestions
    suggestions = (
        resume_suggestions +
        technical_suggestions +
        communication_suggestions +
        portfolio_suggestions
    )

    return render_template(
        "result.html",
        final_score=final_score,
        readiness=readiness,
        resume_score=resume_score,
        technical_score=technical_score,
        communication_score=communication_score,
        portfolio_score=portfolio_score,
        suggestions=suggestions
    )


if __name__ == "__main__":
    app.run(debug=True)
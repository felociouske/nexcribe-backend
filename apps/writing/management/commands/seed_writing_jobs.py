"""
python manage.py seed_writing_jobs
Seeds the database with realistic writing tasks at all levels.
Safe to re-run — skips titles that already exist.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.writing.models import WritingJob, Category

User = get_user_model()

JOBS = [
    # ── Level 1 · Basic ────────────────────────────────────────────────────
    {"title": "Write a 300-word blog post about morning routines",
     "description": "Write an engaging blog post about how a productive morning routine can change your day. Include 3 practical tips. Audience: general public.",
     "instructions": "Use simple language. Write in second person ('you'). No headers needed.",
     "difficulty": "BASIC", "level": 1, "budget_kes": 1500, "words": 300, "category": "Lifestyle"},

    {"title": "Product description for a bamboo water bottle",
     "description": "Write a compelling product description for an eco-friendly bamboo water bottle. Highlight sustainability, design, and durability.",
     "instructions": "Keep it under 200 words. Use bullet points for features.",
     "difficulty": "BASIC", "level": 1, "budget_kes": 1250, "words": 200, "category": "Copywriting"},

    {"title": "Short story: A child finds a mysterious map",
     "description": "Write a 300-word short story for children (ages 8-12) about a child who discovers a hand-drawn map hidden inside an old library book.",
     "instructions": "End on a positive note. Keep vocabulary age-appropriate.",
     "difficulty": "BASIC", "level": 1, "budget_kes": 1500, "words": 300, "category": "Creative Writing"},

    {"title": "5 tips for saving money as a student",
     "description": "Write a practical listicle for university students on how to manage their finances and save money on a tight budget.",
     "instructions": "Use numbered list format. Each tip should have 2-3 sentences of explanation.",
     "difficulty": "BASIC", "level": 1, "budget_kes": 1400, "words": 350, "category": "Finance"},

    {"title": "Restaurant review template — local Kenyan cuisine",
     "description": "Write a sample restaurant review of a fictional Kenyan restaurant called 'Mama Oliech's'. Cover food, ambience, service, and value.",
     "instructions": "Write as if you visited personally. 250-300 words. Positive tone.",
     "difficulty": "BASIC", "level": 1, "budget_kes": 1300, "words": 280, "category": "Travel & Food"},

    {"title": "Email newsletter intro paragraph for a fitness brand",
     "description": "Write an engaging opening paragraph for a weekly fitness brand newsletter. Theme: staying motivated during the rainy season.",
     "instructions": "150 words max. Energetic and motivating tone.",
     "difficulty": "BASIC", "level": 1, "budget_kes": 1100, "words": 150, "category": "Copywriting"},

    {"title": "Social media captions for a new clothing brand (5 captions)",
     "description": "Write 5 Instagram captions for a Nairobi-based streetwear brand launching its first collection. Each caption should include a call to action.",
     "instructions": "Each caption 50-80 words. Include 3-5 relevant hashtags per caption.",
     "difficulty": "BASIC", "level": 1, "budget_kes": 1750, "words": 350, "category": "Social Media"},

    # ── Level 2 · Basic/Intermediate ───────────────────────────────────────
    {"title": "500-word article: Benefits of solar energy in Kenya",
     "description": "Write an informative article on how solar energy adoption is transforming rural Kenya. Include statistics where possible (you may use estimated figures).",
     "instructions": "Use 2-3 subheadings. Maintain a neutral, journalistic tone.",
     "difficulty": "BASIC", "level": 2, "budget_kes": 2500, "words": 500, "category": "Technology"},

    {"title": "SEO blog post: Best hiking trails near Nairobi",
     "description": "Write an SEO-optimised blog post covering 5 popular hiking spots within 100km of Nairobi. Include practical info (distance, difficulty, cost).",
     "instructions": "Target keyword: 'hiking trails near Nairobi'. Use the keyword naturally 4-5 times.",
     "difficulty": "BASIC", "level": 2, "budget_kes": 2750, "words": 600, "category": "Travel & Food"},

    {"title": "Essay: How social media affects mental health in teenagers",
     "description": "Write a balanced 500-word essay exploring both the positive and negative effects of social media on the mental health of teenagers aged 13-18.",
     "instructions": "Include an introduction, two body paragraphs (pros and cons), and a conclusion.",
     "difficulty": "INTERMEDIATE", "level": 2, "budget_kes": 2600, "words": 500, "category": "Health"},

    # ── Level 2 · Maths (Simple) ───────────────────────────────────────────
    {"title": "Maths assignment: Introduction to sets and Venn diagrams",
     "description": "Complete a short university-style maths assignment explaining the concept of sets, subsets, unions, intersections, and complement using Venn diagrams. Include 3 worked examples.",
     "instructions": "Use clear notation (A ∩ B, A ∪ B, A'). Provide step-by-step solutions for each example. 400-500 words of explanation plus diagrams described in text.",
     "difficulty": "BASIC", "level": 2, "budget_kes": 2800, "words": 450, "category": "Mathematics"},

    {"title": "Maths project: Real-world applications of linear equations",
     "description": "Write a 500-word project exploring how linear equations are used in everyday life — budgeting, speed/distance, and simple business pricing models. Include 2 solved word problems.",
     "instructions": "Show full working for each problem. Use simple language suitable for Form 3 level.",
     "difficulty": "BASIC", "level": 2, "budget_kes": 2600, "words": 500, "category": "Mathematics"},

    # ── Level 3-4 · Intermediate ────────────────────────────────────────────
    {"title": "University project: Literature review on climate change adaptation in East Africa",
     "description": "Write a 700-word literature review on climate change adaptation strategies in East Africa. Reference at least 5 key themes from existing research (no actual citations needed — summarise themes).",
     "instructions": "Use academic language. Structure: intro, thematic sections, conclusion. No plagiarism.",
     "difficulty": "INTERMEDIATE", "level": 3, "budget_kes": 4500, "words": 700, "category": "Academic"},

    {"title": "University project: Case study on mobile money adoption in Sub-Saharan Africa",
     "description": "Write a 600-word case study analysing how M-Pesa transformed financial inclusion in Kenya and what lessons other Sub-Saharan African nations have drawn from it.",
     "instructions": "Use a structured format: background, analysis, outcomes, lessons learned.",
     "difficulty": "INTERMEDIATE", "level": 3, "budget_kes": 4250, "words": 600, "category": "Academic"},

    {"title": "Business plan executive summary for a laundry startup",
     "description": "Write a 600-word executive summary for a tech-enabled on-demand laundry service targeting urban Kenyan professionals.",
     "instructions": "Cover: problem, solution, market size, revenue model, team, funding ask.",
     "difficulty": "INTERMEDIATE", "level": 3, "budget_kes": 4000, "words": 600, "category": "Business"},

    {"title": "White paper: The future of fintech in Africa (800 words)",
     "description": "Write an 800-word white paper exploring trends in African fintech: mobile banking, crypto adoption, regulatory challenges, and investment outlook.",
     "instructions": "Professional tone. Use subheadings for each major theme.",
     "difficulty": "INTERMEDIATE", "level": 4, "budget_kes": 5500, "words": 800, "category": "Finance"},

    {"title": "University project: Argumentative essay on free university education",
     "description": "Write a 700-word argumentative essay arguing FOR free public university education in Kenya. Address counterarguments.",
     "instructions": "Include thesis statement. Use logical arguments. No personal anecdotes.",
     "difficulty": "INTERMEDIATE", "level": 3, "budget_kes": 4250, "words": 700, "category": "Academic"},

    # ── Level 3-4 · Maths (Intermediate) ──────────────────────────────────
    {"title": "Maths university assignment: Differential calculus — differentiation rules",
     "description": "Write a university-level assignment covering the power rule, product rule, quotient rule, and chain rule. Include 4 fully worked example problems — one per rule.",
     "instructions": "Show all steps clearly. Use proper mathematical notation. Each example should increase in complexity. 600-700 words of working and explanation.",
     "difficulty": "INTERMEDIATE", "level": 3, "budget_kes": 4500, "words": 650, "category": "Mathematics"},

    {"title": "Maths project: Matrices and systems of linear equations",
     "description": "Write a 600-word university project demonstrating how matrices are used to solve systems of linear equations using Gaussian elimination and Cramer's Rule. Provide 2 fully worked 3×3 systems.",
     "instructions": "Show row operations clearly. Verify solutions by substitution. Include brief real-world application (e.g. traffic flow or economics).",
     "difficulty": "INTERMEDIATE", "level": 3, "budget_kes": 4200, "words": 600, "category": "Mathematics"},

    {"title": "Maths assignment: Probability theory and Bayes' theorem",
     "description": "Complete a 500-word university assignment on probability: conditional probability, independence, and Bayes' theorem. Solve 3 applied problems involving medical testing or quality control scenarios.",
     "instructions": "Define all terms before use. Express all probabilities as fractions and decimals. Show full working.",
     "difficulty": "INTERMEDIATE", "level": 4, "budget_kes": 5000, "words": 550, "category": "Mathematics"},

    {"title": "Maths project: Introduction to complex numbers",
     "description": "Write a 600-word project introducing complex numbers for a university audience. Cover the imaginary unit, arithmetic of complex numbers, the Argand diagram, modulus, and De Moivre's theorem with one proof.",
     "instructions": "Include at least 3 fully worked examples. Use correct notation throughout (e.g. z = a + bi).",
     "difficulty": "INTERMEDIATE", "level": 4, "budget_kes": 5200, "words": 600, "category": "Mathematics"},

    # ── Level 5-6 · Advanced ────────────────────────────────────────────────
    {"title": "Research report: Impact of COVID-19 on informal sector workers in Nairobi",
     "description": "Write a 1000-word research-style report on how the COVID-19 pandemic affected informal sector (jua kali) workers in Nairobi. Cover income loss, coping strategies, and recovery.",
     "instructions": "Use a formal report structure. Include an executive summary, findings sections, and recommendations.",
     "difficulty": "ADVANCED", "level": 5, "budget_kes": 8000, "words": 1000, "category": "Academic"},

    {"title": "University thesis chapter: Methodology section (1000 words)",
     "description": "Write a methodology chapter section for a fictional university thesis on 'Factors affecting academic performance among secondary school students in urban Kenya'. Cover research design, data collection, and analysis approach.",
     "instructions": "Use academic third-person voice. Reference common research methodologies (e.g. mixed methods, purposive sampling).",
     "difficulty": "ADVANCED", "level": 5, "budget_kes": 8500, "words": 1000, "category": "Academic"},

    {"title": "Long-form article: Corruption and governance in East Africa (1200 words)",
     "description": "Write a 1200-word in-depth journalistic article on the challenges of corruption in East African governance. Discuss specific sectors (health, education, procurement) and proposed reforms.",
     "instructions": "Balanced, evidence-based tone. Use subheadings. Avoid partisan language.",
     "difficulty": "ADVANCED", "level": 5, "budget_kes": 9000, "words": 1200, "category": "Politics & Society"},

    {"title": "Technical writing: User guide for a mobile banking app",
     "description": "Write a clear, user-friendly 800-word guide explaining how to use a fictional mobile banking app called 'SwiftPay'. Cover account setup, sending money, paying bills, and security tips.",
     "instructions": "Use numbered steps. Include a troubleshooting section at the end.",
     "difficulty": "ADVANCED", "level": 5, "budget_kes": 7000, "words": 800, "category": "Technology"},

    # ── Level 5 · Maths (Advanced) ─────────────────────────────────────────
    {"title": "Maths thesis chapter: Real analysis — limits and continuity",
     "description": "Write an 800-word university-level chapter section on the epsilon-delta definition of a limit, continuity, and the intermediate value theorem. Include 2 rigorous proofs and 2 worked examples.",
     "instructions": "Use formal proof structure (Theorem / Proof / QED). Assume the reader has completed first-year calculus. Notation must be precise.",
     "difficulty": "ADVANCED", "level": 5, "budget_kes": 8000, "words": 850, "category": "Mathematics"},

    {"title": "Maths project: Numerical methods — Newton-Raphson and bisection",
     "description": "Write a 900-word project comparing the Newton-Raphson and bisection methods for finding roots of equations. Include derivations, convergence analysis, and fully worked iterations for f(x) = x³ − 2x − 5.",
     "instructions": "Show at least 4 iterations for each method. Include a convergence comparison table. Discuss advantages and limitations of each method.",
     "difficulty": "ADVANCED", "level": 5, "budget_kes": 7500, "words": 900, "category": "Mathematics"},

    {"title": "Maths assignment: Linear algebra — eigenvalues and eigenvectors",
     "description": "Write a 700-word university assignment on eigenvalues and eigenvectors. Derive the characteristic equation, find eigenvalues and eigenvectors for two 3×3 matrices, and explain the geometric interpretation.",
     "instructions": "Show all determinant calculations. Verify results. Include one application (e.g. diagonalisation or Markov chains).",
     "difficulty": "ADVANCED", "level": 5, "budget_kes": 7000, "words": 700, "category": "Mathematics"},

    # ── Level 6-8 · Advanced/Expert ─────────────────────────────────────────
    {"title": "University dissertation introduction chapter (1500 words)",
     "description": "Write a comprehensive introduction chapter for a fictional dissertation titled 'The Role of Microfinance in Empowering Women Entrepreneurs in Rural Kenya'. Cover background, problem statement, objectives, significance, and scope.",
     "instructions": "Full academic structure required. Formal language. Use hedging language appropriately.",
     "difficulty": "ADVANCED", "level": 6, "budget_kes": 14000, "words": 1500, "category": "Academic"},

    {"title": "Policy brief: Improving public health infrastructure in Kenya",
     "description": "Write a 1000-word policy brief addressed to the Kenya Ministry of Health recommending improvements to rural health infrastructure. Include evidence-based recommendations.",
     "instructions": "Follow standard policy brief format: executive summary, background, recommendations, conclusion.",
     "difficulty": "ADVANCED", "level": 6, "budget_kes": 11000, "words": 1000, "category": "Academic"},

    {"title": "Grant proposal: Community digital literacy programme (1000 words)",
     "description": "Write a 1000-word grant proposal for a fictional NGO seeking funding to run digital literacy workshops in rural Kenyan schools.",
     "instructions": "Cover: problem statement, proposed solution, target beneficiaries, budget rationale, expected outcomes.",
     "difficulty": "ADVANCED", "level": 6, "budget_kes": 12000, "words": 1000, "category": "Nonprofit"},

    {"title": "Master's thesis literature review: Urban migration and housing in Africa (2000 words)",
     "description": "Write a 2000-word literature review on urban migration trends and housing challenges in sub-Saharan African cities. Synthesise major theoretical frameworks and empirical findings.",
     "instructions": "Thematic structure (not author-by-author). Academic English. Include a brief intro and conclusion.",
     "difficulty": "ADVANCED", "level": 7, "budget_kes": 20000, "words": 2000, "category": "Academic"},

    {"title": "Feasibility study: Establishing a cold storage facility in Western Kenya",
     "description": "Write a 1500-word feasibility study for a private investor considering building a cold storage facility in Kisumu to serve local farmers.",
     "instructions": "Cover market analysis, technical requirements, financial viability overview, risks, and conclusion.",
     "difficulty": "ADVANCED", "level": 7, "budget_kes": 17500, "words": 1500, "category": "Business"},

    # ── Level 6-8 · Maths (Expert) ─────────────────────────────────────────
    {"title": "Maths thesis chapter: Fourier series and convergence (1000 words)",
     "description": "Write a 1000-word thesis-level chapter on Fourier series. Derive the Fourier coefficients, prove Dirichlet's conditions for convergence, and apply the series to solve a heat equation boundary value problem.",
     "instructions": "Use LaTeX-style notation written out in text (e.g. \\sum, \\int). Rigorous proof required for convergence. Show full derivation of the heat equation solution.",
     "difficulty": "ADVANCED", "level": 6, "budget_kes": 13000, "words": 1050, "category": "Mathematics"},

    {"title": "Maths thesis chapter: Group theory — subgroups, cosets, and Lagrange's theorem",
     "description": "Write a 1000-word chapter section on abstract algebra covering group axioms, subgroup criteria, coset decomposition, and a complete proof of Lagrange's theorem. Include examples using Z_n and S_3.",
     "instructions": "All theorems must be formally stated and proved. Use standard algebraic notation. Include at least 2 concrete examples illustrating each major concept.",
     "difficulty": "ADVANCED", "level": 6, "budget_kes": 13500, "words": 1000, "category": "Mathematics"},

    {"title": "Master's maths project: Stochastic processes and Markov chains",
     "description": "Write a 1200-word master's-level project on discrete-time Markov chains. Cover the Chapman-Kolmogorov equations, classification of states (transient/recurrent), steady-state distributions, and a fully worked queueing theory example.",
     "instructions": "Include a transition matrix, derive the steady-state vector, and interpret results. Use rigorous but accessible language. Show all matrix computations.",
     "difficulty": "ADVANCED", "level": 7, "budget_kes": 18000, "words": 1200, "category": "Mathematics"},

    {"title": "Maths dissertation chapter: Topology — metric spaces and compactness (1500 words)",
     "description": "Write a 1500-word dissertation-level chapter on metric spaces. Cover open/closed sets, convergence, completeness, compactness (Heine-Borel theorem), and connectedness. Include full proofs for at least two major theorems.",
     "instructions": "Write at postgraduate level. All definitions must be formal. Proofs should use standard topological arguments. Include one non-trivial example (e.g. Cantor set or function spaces).",
     "difficulty": "ADVANCED", "level": 7, "budget_kes": 22000, "words": 1500, "category": "Mathematics"},

    {"title": "PhD-level maths writing: Partial differential equations — existence and uniqueness",
     "description": "Write a 2000-word chapter-level discussion on existence and uniqueness of solutions to second-order linear PDEs. Cover classification (elliptic, parabolic, hyperbolic), the Cauchy-Kovalevskaya theorem, and energy methods for uniqueness.",
     "instructions": "Write at doctoral level. Use precise mathematical language and formal theorem-proof structure. Reference the method of characteristics and Sobolev spaces conceptually. Include two fully worked classification examples.",
     "difficulty": "ADVANCED", "level": 8, "budget_kes": 32000, "words": 2000, "category": "Mathematics"},
]


class Command(BaseCommand):
    help = 'Seed the database with realistic writing jobs at all plan levels'

    def handle(self, *args, **options):
        admin = User.objects.filter(is_staff=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('No staff user found. Create a superuser first.'))
            return

        created = 0
        skipped = 0

        for job_data in JOBS:
            slug = job_data['category'].lower().replace(' ', '-').replace('&', 'and')
            cat_name = job_data['category']
            # Try slug first, then name, then create — handles any existing data safely
            cat = Category.objects.filter(slug=slug).first() \
               or Category.objects.filter(name=cat_name).first()
            if not cat:
                # Both slug and name are free — safe to create
                try:
                    cat = Category.objects.create(name=cat_name, slug=slug)
                except Exception:
                    # Last resort: grab any active category
                    cat = Category.objects.filter(is_active=True).first()
            if not cat:
                self.stdout.write(self.style.WARNING(f'No category found for "{cat_name}", skipping.'))
                skipped += 1
                continue

            if WritingJob.objects.filter(title=job_data['title']).exists():
                skipped += 1
                continue

            WritingJob.objects.create(
                title=job_data['title'],
                description=job_data['description'],
                instructions=job_data.get('instructions', ''),
                category=cat,
                budget_kes=job_data['budget_kes'],
                word_count_required=job_data['words'],
                difficulty=job_data['difficulty'],
                minimum_plan_level=job_data['level'],
                status=WritingJob.STATUS_OPEN,
                created_by=admin,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done — {created} jobs created, {skipped} already existed.'
        ))
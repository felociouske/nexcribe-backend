import random
from django.core.management.base import BaseCommand


QUIZ_QUESTIONS = [
    # Technology
    ("What does CPU stand for?", "Central Processing Unit", "Central Power Unit", "Computer Processing Unit", "Core Processing Unit", "a"),
    ("Which company created the Python programming language?", "Guido van Rossum (individual, not company)", "Microsoft", "Google", "Apple", "a"),
    ("What does HTML stand for?", "HyperText Markup Language", "High Transfer Markup Language", "HyperText Machine Language", "High Tech Markup Language", "a"),
    ("Which protocol is used to send emails?", "SMTP", "HTTP", "FTP", "SSH", "a"),
    ("What is the binary representation of decimal 10?", "1010", "1100", "1001", "1111", "a"),
    ("Which data structure operates on LIFO principle?", "Stack", "Queue", "Array", "Linked List", "a"),
    ("What does SQL stand for?", "Structured Query Language", "Simple Query Language", "Standard Query Logic", "System Query Language", "a"),
    ("What is the time complexity of binary search?", "O(log n)", "O(n)", "O(n²)", "O(1)", "a"),
    ("Which layer of OSI model handles routing?", "Network Layer", "Transport Layer", "Data Link Layer", "Application Layer", "a"),
    ("What does API stand for?", "Application Programming Interface", "Application Process Integration", "Automated Program Interface", "Application Protocol Interface", "a"),
    ("Which language is primarily used for Android development?", "Java/Kotlin", "Swift", "Python", "Ruby", "a"),
    ("What is Git used for?", "Version control", "Database management", "Server hosting", "Email sending", "a"),
    ("What does CSS stand for?", "Cascading Style Sheets", "Computer Style Sheets", "Creative Style Sheets", "Cascading System Sheets", "a"),
    ("Which sorting algorithm has O(n log n) average case?", "Merge Sort", "Bubble Sort", "Insertion Sort", "Selection Sort", "a"),
    ("What is a cookie in web development?", "Small data stored in browser", "A type of virus", "Server-side code", "Database record", "a"),

    # Finance & Business
    ("What does ROI stand for?", "Return on Investment", "Rate of Interest", "Return on Income", "Revenue on Investment", "a"),
    ("What is inflation?", "Rise in general price level", "Fall in interest rates", "Increase in money supply only", "Decrease in GDP", "a"),
    ("What is a stock market index?", "Measure of stock market performance", "A list of all stocks", "Government bond rating", "Bank interest rate", "a"),
    ("What does GDP stand for?", "Gross Domestic Product", "General Domestic Profit", "Gross Development Plan", "General Development Product", "a"),
    ("What is compound interest?", "Interest on principal and accumulated interest", "Interest on principal only", "Fixed interest rate", "Government interest rate", "a"),
    ("What is a balance sheet?", "Financial statement of assets and liabilities", "Income and expenses record", "Cash flow statement", "Tax filing document", "a"),
    ("What does B2B mean?", "Business to Business", "Back to Basics", "Business to Buyer", "Brand to Brand", "a"),
    ("What is market capitalization?", "Total value of company's shares", "Company's annual revenue", "Company's profit margin", "Total company assets", "a"),
    ("What is venture capital?", "Funding for startups with high growth potential", "Government business loans", "Bank credit line", "Personal savings investment", "a"),
    ("What is diversification in investing?", "Spreading investments across assets", "Investing in one stock heavily", "Selling all assets at once", "Borrowing to invest", "a"),

    # Science & Nature
    ("What is the chemical symbol for gold?", "Au", "Go", "Gd", "Ag", "a"),
    ("How many planets are in our solar system?", "8", "9", "7", "10", "a"),
    ("What gas do plants absorb for photosynthesis?", "Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen", "a"),
    ("What is the powerhouse of the cell?", "Mitochondria", "Nucleus", "Ribosome", "Golgi apparatus", "a"),
    ("What is the speed of light?", "299,792,458 m/s", "199,792,458 m/s", "399,792,458 m/s", "499,792,458 m/s", "a"),
    ("What is the atomic number of carbon?", "6", "12", "8", "4", "a"),
    ("Which planet is known as the Red Planet?", "Mars", "Venus", "Jupiter", "Saturn", "a"),
    ("What is the largest organ in the human body?", "Skin", "Liver", "Brain", "Heart", "a"),
    ("What force keeps planets in orbit?", "Gravity", "Magnetism", "Friction", "Electricity", "a"),
    ("How many bones are in the adult human body?", "206", "186", "226", "196", "a"),

    # History & Geography
    ("On which continent is Kenya located?", "Africa", "Asia", "South America", "Australia", "a"),
    ("Who wrote 'Romeo and Juliet'?", "William Shakespeare", "Charles Dickens", "Mark Twain", "Jane Austen", "a"),
    ("What is the capital of France?", "Paris", "Lyon", "Marseille", "Bordeaux", "a"),
    ("Which ocean is the largest?", "Pacific Ocean", "Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "a"),
    ("In what year did World War II end?", "1945", "1944", "1946", "1943", "a"),
    ("What is the longest river in the world?", "Nile", "Amazon", "Mississippi", "Yangtze", "a"),
    ("Which country has the largest population?", "India", "China", "USA", "Indonesia", "a"),
    ("What is the capital of Kenya?", "Nairobi", "Mombasa", "Kisumu", "Nakuru", "a"),
    ("Which mountain is the highest in Africa?", "Mount Kilimanjaro", "Mount Kenya", "Mount Elgon", "Rwenzori Mountains", "a"),
    ("What language is most spoken in the world?", "Mandarin Chinese", "English", "Spanish", "Hindi", "a"),

    # Health & Wellness
    ("How many hours of sleep do adults typically need?", "7-9 hours", "4-5 hours", "10-12 hours", "5-6 hours", "a"),
    ("What vitamin does sunlight provide?", "Vitamin D", "Vitamin A", "Vitamin C", "Vitamin B12", "a"),
    ("What is the normal human body temperature?", "37°C (98.6°F)", "36°C (96.8°F)", "38°C (100.4°F)", "35°C (95°F)", "a"),
    ("How many chambers does the human heart have?", "4", "2", "3", "6", "a"),
    ("What nutrient builds and repairs body tissue?", "Protein", "Carbohydrates", "Fat", "Fiber", "a"),
    ("Which organ produces insulin?", "Pancreas", "Liver", "Kidney", "Stomach", "a"),
    ("What is the recommended daily water intake for adults?", "2-3 liters", "1 liter", "5 liters", "0.5 liters", "a"),
    ("What does BMI stand for?", "Body Mass Index", "Body Muscle Index", "Basic Metabolic Index", "Body Measurement Index", "a"),
]

TRIVIA_QUESTIONS = [
    # Fun facts
    ("How many colors are in a rainbow?", "7", "6", "8", "5", "a"),
    ("What is the fastest land animal?", "Cheetah", "Lion", "Leopard", "Horse", "a"),
    ("How many strings does a standard guitar have?", "6", "4", "8", "5", "a"),
    ("What is the smallest country in the world?", "Vatican City", "Monaco", "San Marino", "Liechtenstein", "a"),
    ("Which planet has the most moons?", "Saturn", "Jupiter", "Uranus", "Neptune", "a"),
    ("What is the most spoken language in Africa?", "Swahili", "Arabic", "French", "Hausa", "a"),
    ("How long is a marathon race?", "42.195 km", "40 km", "45 km", "38 km", "a"),
    ("What is the currency of Japan?", "Yen", "Won", "Yuan", "Rupee", "a"),
    ("Which fruit has seeds on the outside?", "Strawberry", "Raspberry", "Blackberry", "Blueberry", "a"),
    ("How many sides does a hexagon have?", "6", "5", "7", "8", "a"),
    ("What is the largest desert in the world?", "Antarctic Desert", "Sahara", "Arabian Desert", "Gobi Desert", "a"),
    ("Which element is a diamond made of?", "Carbon", "Silicon", "Oxygen", "Nitrogen", "a"),
    ("How many days are in a leap year?", "366", "365", "364", "367", "a"),
    ("What is the tallest animal in the world?", "Giraffe", "Elephant", "Camel", "Ostrich", "a"),
    ("Which continent has no countries?", "Antarctica", "Australia", "Arctic", "Greenland", "a"),
    ("What is 15% of 200?", "30", "25", "35", "20", "a"),
    ("How many minutes are in a day?", "1440", "1200", "1600", "1000", "a"),
    ("Which ocean surrounds the North Pole?", "Arctic Ocean", "Atlantic Ocean", "Pacific Ocean", "Indian Ocean", "a"),
    ("What does a barometer measure?", "Atmospheric pressure", "Temperature", "Humidity", "Wind speed", "a"),
    ("What year was the iPhone first released?", "2007", "2005", "2009", "2010", "a"),
    ("How many bones are in the human hand?", "27", "20", "30", "25", "a"),
    ("What is the chemical formula for water?", "H2O", "HO2", "H2O2", "HO", "a"),
    ("Which is the biggest continent?", "Asia", "Africa", "North America", "Europe", "a"),
    ("How many teeth does an adult human have?", "32", "28", "30", "34", "a"),
    ("What is the national animal of Kenya?", "Lion", "Elephant", "Buffalo", "Rhino", "a"),
]


class Command(BaseCommand):
    help = 'Seed quiz and trivia questions for games'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing questions first')

    def handle(self, *args, **options):
        from apps.games.models import Game, QuizQuestion

        if options['clear']:
            QuizQuestion.objects.all().delete()
            self.stdout.write('Cleared existing questions.')

        quiz_game = Game.objects.filter(slug='quiz').first()
        trivia_game = Game.objects.filter(slug='trivia').first()

        if not quiz_game or not trivia_game:
            self.stdout.write(self.style.ERROR(
                'Games not found. Run: python manage.py seed_platform first.'
            ))
            return

        created_quiz = 0
        created_trivia = 0

        for q in QUIZ_QUESTIONS:
            question_text, a, b, c, d, correct = q
            if not QuizQuestion.objects.filter(question=question_text, game=quiz_game).exists():
                difficulty = random.choice(['easy', 'easy', 'medium', 'hard'])
                QuizQuestion.objects.create(
                    game=quiz_game,
                    question=question_text,
                    option_a=a,
                    option_b=b,
                    option_c=c,
                    option_d=d,
                    correct_option=correct,
                    difficulty=difficulty,
                    is_active=True,
                )
                created_quiz += 1

        for q in TRIVIA_QUESTIONS:
            question_text, a, b, c, d, correct = q
            if not QuizQuestion.objects.filter(question=question_text, game=trivia_game).exists():
                difficulty = random.choice(['easy', 'easy', 'medium'])
                QuizQuestion.objects.create(
                    game=trivia_game,
                    question=question_text,
                    option_a=a,
                    option_b=b,
                    option_c=c,
                    option_d=d,
                    correct_option=correct,
                    difficulty=difficulty,
                    is_active=True,
                )
                created_trivia += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! {created_quiz} quiz questions + {created_trivia} trivia questions created.\n'
            f'Total: {QuizQuestion.objects.count()} questions across all games.'
        ))
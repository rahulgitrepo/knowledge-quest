from flask import Flask, request, render_template_string, session, jsonify
import random
import logging
import json
import os

flask_app = Flask(__name__)
flask_app.secret_key = 'secure_quiz_key'

QUESTION_BANK_FILE = "question_bank.json"

def load_question_bank():
    if not os.path.exists(QUESTION_BANK_FILE):
        with open(QUESTION_BANK_FILE, "w") as f:
            json.dump([], f)
    with open(QUESTION_BANK_FILE, "r") as f:
        return json.load(f)

def save_question_bank(data):
    with open(QUESTION_BANK_FILE, "w") as f:
        json.dump(data, f, indent=4)

question_bank = load_question_bank()

# Templates
home_template = """<!doctype html>
<html>
<head>
  <title>Knowledge Quest</title>
  <style>
    body { background-color: #121212; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; text-align: center; padding: 50px; }
    h1 { font-size: 3em; color: #00ffcc; }
    p { font-size: 1.2em; }
    .prizes { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-top: 30px; }
    .prize-item { text-align: center; }
    .prize-item img { max-width: 192px; height: 192px; border-radius: 10px; }
    button {
      background-color: #00ffcc; color: #121212; border: none;
      padding: 15px 30px; font-size: 1.2em; cursor: pointer;
      border-radius: 10px; transition: background-color 0.3s;
    }
    button:hover { background-color: #00cc99; }
  </style>
</head>
<body>
  <h1>🧠 Knowledge Quest</h1>
  <p>
    Embark on the Knowledge Quest!<br>
    Test your knowledge of AI/ML, Nuclear Industry, and Southern Company with 5 random questions — and win exciting prizes! 🎁
  </p>

  <div class="prizes">
    <div class="prize-item">
      <img src="{{ url_for('static', filename='jbl_speaker.png') }}" alt="JBL Speaker Prize">
      <p><strong>🎧 JBL Speaker</strong><br>Score 5 out of 5</p>
    </div>
    <div class="prize-item">
      <img src="{{ url_for('static', filename='cap.png') }}" alt="Southern Company Cap Prize">
      <p><strong>🧢 Southern Company Cap</strong><br>Score 4 out of 5</p>
    </div>
  </div>

  <a href="/quiz"><button>🚀 Start Quiz</button></a>
</body>
</html>
"""

quiz_template = """<!doctype html>
<html>
<head>
  <title>Take the Quiz</title>
  <style>
    body { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI', sans-serif; padding: 40px; }
    h2 { color: #00ffcc; text-align: center; }
    form { max-width: 600px; margin: auto; }
    .question { margin-bottom: 30px; padding: 20px; background-color: #2c2c2c; border-radius: 10px; }
    .question strong { font-size: 1.2em; }
    input[type="radio"] { margin-right: 10px; }
    input[type="submit"] {
      background-color: #00ffcc; color: #121212; border: none;
      padding: 15px 30px; font-size: 1.2em; cursor: pointer;
      border-radius: 10px; display: block; margin: 30px auto;
    }
    input[type="submit"]:hover { background-color: #00cc99; }
  </style>
</head>
<body>
  <h2>🧠 Answer the Questions</h2>
  <form method="post">
    {% for q in questions %}
      {% set idx = loop.index0 %}
      <div class="question">
        <p><strong>{{ q.question }}</strong></p>
        {% for opt in q.options %}
          <label><input type="radio" name="q{{ idx }}" value="{{ opt }}" required> {{ opt }}</label><br>
        {% endfor %}
      </div>
    {% endfor %}
    <input type="submit" value="✅ Submit Answers">
  </form>
</body>
</html>
"""

result_template = """<!doctype html>
<html>
<head>
  <title>Quiz Result</title>
  <style>
    body { background-color: #121212; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; text-align: center; padding: 50px; }
    h2 { font-size: 2.5em; color: #00ffcc; }
    .incorrect { margin-top: 30px; text-align: left; max-width: 600px; margin-left: auto; margin-right: auto; }
    .incorrect h3 { color: #ff6666; }
    .incorrect p { font-size: 1.1em; margin-bottom: 20px; }
    a { text-decoration: none; }
    button {
      background-color: #00ffcc; color: #121212; border: none;
      padding: 15px 30px; font-size: 1.2em; cursor: pointer;
      border-radius: 10px; margin-top: 30px;
    }
    button:hover { background-color: #00cc99; }
  </style>
</head>
<body>
  <h2>{{ message }}</h2>

  {% if incorrect_answers %}
    <div class="incorrect">
      <h3>Review Your Answers:</h3>
      {% for item in incorrect_answers %}
        <p>
          <strong>Question:</strong> {{ item.question }}<br>
          <strong>Your Answer:</strong> {{ item.your_answer }}<br>
          <strong>Correct Answer:</strong> {{ item.correct_answer }}
        </p>
      {% endfor %}
    </div>
  {% endif %}

  <a href="/"><button>🏠 Back to Home</button></a>
</body>
</html>
"""

submit_template = """<!doctype html>
<html>
<head>
  <title>Submit a Question</title>
  <style>
    body { background-color: #121212; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; padding: 40px; }
    form { max-width: 600px; margin: auto; }
    label, input { display: block; width: 100%; margin-bottom: 15px; font-size: 1em; }
    input[type="submit"] {
      background-color: #00ffcc; color: #121212; border: none;
      padding: 15px; font-size: 1.2em; cursor: pointer;
      border-radius: 10px;
    }
    input[type="submit"]:hover { background-color: #00cc99; }
  </style>
</head>
<body>
  <h2>📝 Submit a New Quiz Question</h2>
  <form method="post">
    <label>Question:</label>
    <input type="text" name="question" required>

    <label>Option 1:</label>
    <input type="text" name="option1" required>

    <label>Option 2:</label>
    <input type="text" name="option2" required>

    <label>Option 3:</label>
    <input type="text" name="option3" required>

    <label>Option 4:</label>
    <input type="text" name="option4" required>

    <label>Correct Answer (must match one of the options):</label>
    <input type="text" name="answer" required>

    <input type="submit" value="➕ Submit Question">
  </form>
</body>
</html>
"""

@flask_app.route('/')
def home():
    return render_template_string(home_template)

@flask_app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        selected_questions = session.get('selected_questions', [])
        incorrect_answers = []
        for i, q in enumerate(selected_questions):
            user_answer = request.form.get(f'q{i}')
            if user_answer != q['answer']:
                incorrect_answers.append({
                    "question": q['question'],
                    "your_answer": user_answer,
                    "correct_answer": q['answer']
                })
        correct = len(selected_questions) - len(incorrect_answers)
        message = "🎉 You Win!" if correct == len(selected_questions) else f"❌ You got {len(incorrect_answers)} wrong."
        return render_template_string(result_template, message=message, incorrect_answers=incorrect_answers)

    selected_questions = random.sample(question_bank, 5)
    session['selected_questions'] = selected_questions
    return render_template_string(quiz_template, questions=selected_questions)

@flask_app.route('/submit-question', methods=['GET', 'POST'])
def submit_question():
    if request.method == 'POST':
        question = request.form.get('question')
        options = [request.form.get(f'option{i}') for i in range(1, 5)]
        answer = request.form.get('answer')

        if question and all(options) and answer in options:
            new_question = {
                "question": question,
                "options": options,
                "answer": answer
            }

            question_bank.append(new_question)
            save_question_bank(question_bank)

            return render_template_string("<h2 style='color:lime;'>✅ Question submitted successfully!</h2><a href='/'>Back to Home</a>")
        else:
            return render_template_string("<h2 style='color:red;'>❌ Invalid submission. Please fill all fields correctly.</h2><a href='/submit-question'>Try Again</a>")

    return render_template_string(submit_template)

@flask_app.errorhandler(Exception)
def handle_exception(e):
    logging.exception("Unhandled exception:")
    return jsonify(error=str(e)), 500

@flask_app.route('/<path:path>')
def catch_all(path):
    logging.warning(f"⚠️ Unknown route accessed: /{path}")
    return f"404 Not Found: /{path}", 404

# Azure-compatible startup
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=8000, debug=True)

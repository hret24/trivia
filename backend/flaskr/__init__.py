from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample
    route after completing the TODOs
    """
    with app.app_context():
        db.create_all()

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(res):
        res.headers.add('Access-Control-Allow-Methods',
                        'GET,PATCH,POST,DELETE,OPTIONS')
        return res

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories')
    def categories():

        return jsonify({
            'success': True,
            'categories': {
                category.id: category.type
                for category in Category.query.all()
                }
        }), 200

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of
    the screen for three pages. Clicking on the page numbers
    should update the questions.
    """
    @app.route('/questions')
    def questions():

        # * Implement pagniation
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        # * ---------------------

        total_questions = [question.format()
                           for question in Question.query.all()]
        paginated_questions = total_questions[start:end]

        if (len(paginated_questions) == 0):
            abort(404)

        return jsonify({
            'questions': paginated_questions,
            'totalQuestions': len(total_questions),
            'categories': {
                category.id: category.type
                for category in Category.query.all()
                },
            'currentCategory': None,
            'success': True
        }), 200

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
    the question will be removed. This removal will persist in the
    database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):

        Question.query.get_or_404(question_id).delete()

        return jsonify({'id': question_id, 'success': True}), 200

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at
    the end of the last page of the questions list in
    the "List" tab.
    """
    def create_question():
        body = request.get_json()
        data = [body.get('question'), body.get('answer'),
                body.get('difficulty'), body.get('category')]

        for required in data:
            if required is None:
                abort(422)
            Question(data[0], data[1], data[2], data[3]).insert()
            return jsonify({'success': True}), 201

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    def search_question(search_term):

        search_results = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()

        if (len(search_results) == 0):
            abort(404)

        formatted_questions = [question.format()
                               for question in search_results]

        return jsonify({
            "questions": formatted_questions,
            "totalQuestions": len(formatted_questions),
            'currentCategory': None,
            'success': True
        }), 200

    @app.route('/questions', methods=['POST'])
    def create_or_search():
        body = request.get_json()
        search_term = body.get('searchTerm')

        if search_term:
            # Search logic
            questions = Question.query.filter(
                Question.question.ilike(f"%{search_term}%")).all()
            if not questions:
                abort(404)
            return jsonify({
                'questions': [question.format() for question in questions],
                'totalQuestions': len(questions),
                'currentCategory': None,
                'success': True
            }), 200
        else:
            # Create logic
            question = body.get('question')
            answer = body.get('answer')
            difficulty = body.get('difficulty')
            category = body.get('category')

            if not all([question, answer, difficulty, category]):
                abort(422)

            new_question = Question(
                question=question,
                answer=answer,
                difficulty=difficulty,
                category=category)
            new_question.insert()

            return jsonify({'success': True}), 201

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def questions_in_category(category_id):

        category = Category.query.get_or_404(category_id)
        questions_in_category = Question.query.filter_by(
            category=category_id).all()

        return jsonify({
            'questions': [question.format()
                          for question in questions_in_category
                          ],
            'totalQuestions': len(questions_in_category),
            'currentCategory': category.type,
            'success': True
        }), 200

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def random_question():
        body = request.get_json()
        previous_questions = body.get('previous_questions', [])
        category = body.get('quiz_category', {}).get('id')

        if category:
            questions = Question.query.filter(
                Question.category == category,
                Question.id.notin_(previous_questions)
                ).all()
        else:
            questions = Question.query.filter(
                Question.id.notin_(previous_questions)).all()

        if not questions:
            return jsonify({'success': True}), 200

        random_question = random.choice(questions)
        return jsonify({
            'question': random_question.format(),
            'success': True
            }), 200

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "success": False,
            "message": "Unprocessable entity"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

    return app

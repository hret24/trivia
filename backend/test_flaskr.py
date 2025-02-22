import os
import unittest
from dotenv import load_dotenv
from flaskr import create_app
from models import db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        load_dotenv()
        
        self.database_name = os.getenv('DB_TEST_NAME')
        self.database_user = os.getenv('DB_TEST_USER')
        self.database_host = os.getenv('DB_TEST_HOST')
        self.database_path = f"postgresql://{self.database_user}@{self.database_host}/{self.database_name}"

        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": self.database_path,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "TESTING": True
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Executed after each test"""
        pass

    # """
    # TODO
    # Write at least one test for each test for successful operation and for expected errors.
    # """
    def post_json(self, url, data):
        return self.client.post(url, json=data)

    def test_get_categories(self):
        """Test retrieving all categories."""
        res = self.client.get('/categories')
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['categories']))

    def test_get_categories_error(self):
        """Test retrieving categories when no categories exist."""
        with self.app.app_context():
            Category.query.delete()
            db.session.commit()

        res = self.client.get('/categories')
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['categories']), 0)
        
        with self.app.app_context():
            categories = [
                Category(type='Science'),
                Category(type='Art'),
                Category(type='Geography'),
            ]
            db.session.add_all(categories)
            db.session.commit()

    def test_get_paginated_questions(self):
        """Test retrieving paginated questions."""
        res = self.client.get('/questions?page=1')
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['questions']))

    def test_get_paginated_questions_error(self):
        """Test retrieving paginated questions with an invalid page number."""
        res = self.client.get('/questions?page=100')
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])

    def test_delete_question(self):
        """Test deleting a question."""
        question = Question.query.first()
        res = self.client.delete(f'/questions/{question.id}')
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])

        deleted_question = Question.query.get(question.id)
        self.assertIsNone(deleted_question)

    def test_delete_question_error(self):
        """Test deleting a non-existent question."""
        res = self.client.delete('/questions/9999')
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])

    def test_create_question(self):
        """Test creating a new question."""
        question_data = {
            "question": "What is the capital of Germany?",
            "answer": "Berlin",
            "category": 1,
            "difficulty": 2
        }
        res = self.post_json('/questions', question_data)
        data = res.get_json()

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data['success'])

        new_question = Question.query.filter_by(question=question_data['question']).first()
        self.assertIsNotNone(new_question)

    def test_create_question_error(self):
        """Test creating a question with missing fields."""
        question_data = {
            "question": "What is the capital of Spain?",
            "answer": "Madrid"
        }
        res = self.post_json('/questions', question_data)
        data = res.get_json()

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data['success'])

    def test_search_question(self):
        """Test searching for a question."""
        res = self.post_json('/questions', {"searchTerm": "capital"})
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['questions']))

    def test_search_question_error(self):
        """Test searching for a question with no results."""
        res = self.client.post(
            '/questions', 
            json={"searchTerm": "nonexistent"}
            )
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])

    def test_get_questions_by_category(self):
        """Test retrieving questions by category."""
        res = self.client.get('/categories/1/questions')
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['questions']))

    def test_get_questions_by_category_error(self):
        """Test retrieving questions by a non-existent category."""
        res = self.client.get('/categories/9999/questions')
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertFalse(data['success'])

    def test_play_quiz(self):
        """Test playing the quiz."""
        quiz_data = {
            "previous_questions": [],
            "quiz_category": {"id": 1}
        }
        res = self.post_json('/quizzes', quiz_data)
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertTrue('question' in data)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()

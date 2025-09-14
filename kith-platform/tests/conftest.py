import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import create_app
from config.settings import TestingConfig
from models import Base, User, Contact, RawNote, SynthesizedEntry
from app.utils.database import DatabaseManager
from app.utils.dependencies import container
import factory
from factory.alchemy import SQLAlchemyModelFactory

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/kith_test'

@pytest.fixture(scope='session')
def test_db():
    """Create test database"""
    # Create test database if it doesn't exist
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='postgres',
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute('CREATE DATABASE kith_test')
        cursor.close()
        conn.close()
    except psycopg2.errors.DuplicateDatabase:
        pass  # Database already exists
    
    # Create tables
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/kith_test')
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def app(test_db):
    """Create test Flask application"""
    app = create_app(TestingConfig)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def db_session(test_db):
    """Create database session for tests"""
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def db_manager(test_db):
    """Create database manager for tests"""
    manager = DatabaseManager()
    manager.engine = test_db
    manager.SessionLocal = sessionmaker(bind=test_db)
    return manager

# Factory classes for test data generation
class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    username = factory.Sequence(lambda n: f"user{n}")
    password_hash = factory.LazyFunction(lambda: "hashed_password")
    password_plaintext = "test_password"
    role = "user"

class ContactFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Contact
        sqlalchemy_session_persistence = "commit"
    
    user_id = factory.SubFactory(UserFactory)
    full_name = factory.Faker('name')
    tier = 2
    telegram_username = factory.Faker('user_name')
    is_verified = False
    is_premium = False

class RawNoteFactory(SQLAlchemyModelFactory):
    class Meta:
        model = RawNote
        sqlalchemy_session_persistence = "commit"
    
    contact_id = factory.SubFactory(ContactFactory)
    content = factory.Faker('text', max_nb_chars=200)
    metadata_tags = factory.LazyFunction(lambda: {"category": "test"})

class SynthesizedEntryFactory(SQLAlchemyModelFactory):
    class Meta:
        model = SynthesizedEntry
        sqlalchemy_session_persistence = "commit"
    
    contact_id = factory.SubFactory(ContactFactory)
    category = factory.Faker('word')
    content = factory.Faker('text', max_nb_chars=100)
    confidence_score = factory.Faker('pyfloat', min_value=0.0, max_value=1.0)

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = UserFactory()
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_contact(db_session, sample_user):
    """Create a sample contact for testing"""
    contact = ContactFactory(user_id=sample_user.id)
    db_session.add(contact)
    db_session.commit()
    return contact

@pytest.fixture
def sample_note(db_session, sample_contact):
    """Create a sample note for testing"""
    note = RawNoteFactory(contact_id=sample_contact.id)
    db_session.add(note)
    db_session.commit()
    return note

@pytest.fixture
def authenticated_user(client, sample_user):
    """Create an authenticated user session"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_user.id)
        sess['_fresh'] = True
    return sample_user

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    with patch('app.services.ai_service.AIService') as mock:
        mock_instance = Mock()
        mock_instance.analyze_note.return_value = {
            'categories': {
                'personal_info': {'content': 'Test content', 'confidence': 0.8},
                'preferences': {'content': 'Test preferences', 'confidence': 0.7}
            }
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_celery():
    """Mock Celery for testing"""
    with patch('app.tasks.ai_tasks.process_note_async') as mock:
        mock.delay.return_value = Mock(id='test-task-id')
        yield mock

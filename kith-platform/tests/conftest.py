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
from app.utils.dependencies import Container
import factory
from factory.alchemy import SQLAlchemyModelFactory
from werkzeug.security import generate_password_hash

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
# FORCE SQLite for testing - NEVER use production database for tests
os.environ['DATABASE_URL'] = 'sqlite:///test_kith_platform.db'
print("🔧 TEST SETUP: Forcing SQLite database for test isolation")

@pytest.fixture(scope='session')
def test_db():
    """Create test database - Always uses SQLite for complete isolation"""
    print("🔧 Creating isolated SQLite test database")
    
    # Always use SQLite for tests - complete isolation from production
    engine = create_engine('sqlite:///test_kith_platform.db')
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    print("🔧 Cleaning up test database")
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
    # Bind factory-boy SQLAlchemy session to the same session
    UserFactory._meta.sqlalchemy_session = session
    ContactFactory._meta.sqlalchemy_session = session
    RawNoteFactory._meta.sqlalchemy_session = session
    SynthesizedEntryFactory._meta.sqlalchemy_session = session
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

@pytest.fixture(autouse=True)
def override_container_db_manager(db_manager):
    """Override the container's database manager with the test database manager"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🔧 DEBUG: Overriding container database manager for tests...")
    # Since we no longer have a global container, we'll skip the override
    # The test database manager should be used directly in tests
    logger.info(f"🔧 DEBUG: Test manager: {db_manager}")
    logger.info(f"🔧 DEBUG: Test manager engine: {db_manager.engine}")
    logger.info("✅ Using test database manager directly")
    
    yield
    
    logger.info("🔧 DEBUG: Test database manager cleanup completed")

# Factory classes for test data generation
class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
        sqlalchemy_session = None
    
    username = factory.Sequence(lambda n: f"user{n}")
    password_hash = factory.LazyFunction(lambda: generate_password_hash("test_password", method='pbkdf2:sha256'))
    password_plaintext = "test_password"
    role = "user"

class ContactFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Contact
        sqlalchemy_session_persistence = "commit"
        sqlalchemy_session = None
    
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
        sqlalchemy_session = None
    
    contact_id = factory.SubFactory(ContactFactory)
    content = factory.Faker('text', max_nb_chars=200)
    metadata_tags = factory.LazyFunction(lambda: {"category": "test"})

class SynthesizedEntryFactory(SQLAlchemyModelFactory):
    class Meta:
        model = SynthesizedEntry
        sqlalchemy_session_persistence = "commit"
        sqlalchemy_session = None
    
    contact_id = factory.SubFactory(ContactFactory)
    category = factory.Faker('word')
    content = factory.Faker('text', max_nb_chars=100)
    confidence_score = factory.Faker('pyfloat', min_value=0.0, max_value=1.0)

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🔧 DEBUG: Creating sample user...")
    user = UserFactory()
    logger.info(f"🔧 DEBUG: User factory created user: {user.username} (ID: {user.id})")
    
    db_session.add(user)
    logger.info("🔧 DEBUG: User added to session")
    
    db_session.commit()
    logger.info("🔧 DEBUG: Session committed")
    
    logger.info(f"✅ Sample user created: {user.username} (ID: {user.id})")
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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔧 DEBUG: Creating authenticated user session for: {sample_user.username} (ID: {sample_user.id})")
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(sample_user.id)
        sess['_fresh'] = True
        logger.info(f"🔧 DEBUG: Session variables set - _user_id: {sess.get('_user_id')}, _fresh: {sess.get('_fresh')}")
    
    logger.info(f"✅ Authenticated user session created for: {sample_user.username}")
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

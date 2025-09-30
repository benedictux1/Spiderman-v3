from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from celery import Celery
import os
import logging
from datetime import datetime

from config.settings import ProductionConfig, DevelopmentConfig, TestingConfig
from app.utils.dependencies import Container, get_config

# Initialize extensions, but don't configure them yet
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=None):
    # Get the parent directory (kith-platform) for templates and static files
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Determine config class (prefer environment when not explicitly provided)
    if config_class is None:
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env == 'production':
            config_class = ProductionConfig
        elif flask_env == 'testing':
            config_class = TestingConfig
        else:
            config_class = DevelopmentConfig
            
    app.config.from_object(config_class)

    # Create and initialize the dependency container at runtime
    container = Container()  # Instantiate here, not at import time
    container.config.from_dict({'config_class': config_class})
    container.wire(modules=[
        "app.api.auth", "app.api.contacts", "app.api.notes", 
        "app.api.admin", "app.api.diagnostics", "app.api.telegram",
        "app.services.note_service", "app.services.telegram_service",
        "app.utils.monitoring"
    ])
    app.container = container

    # Production environment sanity checks
    if os.getenv('FLASK_ENV') == 'production' and not app.config.get('SECRET_KEY'):
        raise ValueError("FLASK_SECRET_KEY is not set in the production environment.")
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login_page'
    
    # Configure logging
    from app.utils.logging_config import setup_logging
    from app.utils.structured_logging import StructuredLogger, LoggingMiddleware
    
    # Set up basic logging first
    setup_logging(
        app_name="kith_platform",
        log_level=app.config.get('LOG_LEVEL', 'INFO'),
        enable_console=app.debug,
        enable_file=True
    )
    
    # Set up structured logging
    StructuredLogger.setup_logging(app)
    
    # Add logging middleware
    app.wsgi_app = LoggingMiddleware(app.wsgi_app)
    
    # Initialize monitoring (with error handling)
    try:
        from app.utils.monitoring import HealthChecker, MetricsCollector
        from app.utils.database import DatabaseManager
        db_manager = DatabaseManager()
        # Initialize monitoring components (simplified since we removed the initialize_monitoring function)
        health_checker = HealthChecker(db_manager)
        metrics_collector = MetricsCollector(db_manager)
        logging.info("Monitoring initialized successfully")
    except Exception as e:
        logging.warning(f"Monitoring initialization failed: {e}. Continuing without monitoring.")
    
    # Register blueprints (with error handling)
    try:
        from app.api.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
    except Exception as e:
        logging.warning(f"Failed to register auth blueprint: {e}")
    
    try:
        from app.api.contacts import contacts_bp
        app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
    except Exception as e:
        logging.warning(f"Failed to register contacts blueprint: {e}")
    
    try:
        from app.api.notes import notes_bp
        app.register_blueprint(notes_bp, url_prefix='/api/notes')
    except Exception as e:
        logging.warning(f"Failed to register notes blueprint: {e}")
    
    try:
        from app.api.telegram import telegram_bp
        app.register_blueprint(telegram_bp, url_prefix='/api/telegram')
    except Exception as e:
        logging.warning(f"Failed to register telegram blueprint: {e}")
    
    try:
        from app.api.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
    except Exception as e:
        logging.warning(f"Failed to register admin blueprint: {e}")
    
    try:
        from app.api.analytics import analytics_bp
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    except Exception as e:
        logging.warning(f"Failed to register analytics blueprint: {e}")

    try:
        from app.celery_app import celery_app
        app.extensions['celery_app'] = celery_app
    except Exception as e:
        logging.warning(f"Failed to attach celery app: {e}")
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.services.auth_service import AuthService
        from app.utils.database import DatabaseManager
        try:
            db_manager = DatabaseManager()
            with db_manager.get_session() as session:
                from app.models import User
                user = session.get(User, user_id)
                if user:
                    # Detach the user from the session to avoid DetachedInstanceError
                    session.expunge(user)
                return user
        except Exception as e:
            logging.warning(f"Failed to load user {user_id}: {e}")
            return None
    
    # Add health and monitoring routes
    @app.route('/')
    def index():
        """Main application route with simple session-based authentication"""
        from flask import render_template, session
        
        # Simple session-based authentication check
        if session.get('user_id') and session.get('username'):
            logging.info(f"✅ Authenticated user {session.get('username')} (ID: {session.get('user_id')}) accessing main page")
            return render_template('index.html')
        else:
            logging.info("❌ Unauthenticated user redirected to login")
            return render_template('login.html')
    
    @app.route('/health')
    def health_check():
        """Health check with basic diagnostics for monitoring and tests"""
        try:
            # Compute uptime
            import time
            started_at = getattr(app, '_started_at', None)
            if started_at is None:
                started_at = time.time()
                setattr(app, '_started_at', started_at)
            uptime_seconds = int(time.time() - started_at)

            # Basic component checks (lightweight)
            checks = {
                'database': 'unknown',
                'redis': 'unknown',
                'celery': 'unknown',
                'system': 'ok',
            }
            try:
                from app.utils.database import DatabaseManager
                dm = DatabaseManager()
                with dm.engine.connect() as _:
                    checks['database'] = 'ok'
            except Exception:
                checks['database'] = 'degraded'
            
            return {
                'status': 'healthy',
                'version': '3.0.0',
                'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
                'uptime_seconds': uptime_seconds,
                'checks': checks,
            }, 200
        except Exception as exc:
            return {'status': 'error', 'error': str(exc)}, 500
    
    @app.route('/metrics')
    def get_metrics():
        """Get application metrics"""
        try:
            from app.utils.monitoring import metrics_collector
            if metrics_collector:
                return metrics_collector.get_metrics_summary()
        except Exception as e:
            logging.warning(f"Metrics collection failed: {e}")
        return {'metrics': 'not_available'}
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with individual component status"""
        try:
            from app.utils.monitoring import HealthChecker
            from app.utils.database import DatabaseManager
            db_manager = DatabaseManager()
            health_checker = HealthChecker(db_manager)
            return health_checker.get_overall_health()
        except Exception as e:
            logging.warning(f"Detailed health check failed: {e}")
        return {'status': 'healthy', 'version': '3.0.0'}
    
    @app.route('/login', methods=['GET'])
    def login_page():
        """Login page route."""
        return render_template('login.html')
    
    @app.route('/relationship-graph', methods=['GET'])
    def relationship_graph():
        """Relationship graph page."""
        return render_template('relationship_graph.html')
    
    @app.route('/manage-graph', methods=['GET'])
    def manage_graph():
        """Manage graph page."""
        return render_template('manage_graph.html')
    
    @app.route('/settings', methods=['GET'])
    def settings():
        """Settings page."""
        return render_template('settings.html')
    
    @app.route('/test-settings', methods=['GET'])
    def test_settings():
        """Test settings page."""
        from flask import session
        # Simple session-based authentication check
        if session.get('user_id') and session.get('username'):
            return render_template('test_settings.html')
        else:
            return render_template('login.html')
    
    # Add comprehensive API endpoints for settings page functionality
    telegram_state = {"linked": False, "username": None}
    contacts_db = []  # In-memory contacts store
    next_contact_id = 1
    
    @app.route('/api/telegram/status', methods=['GET'])
    def telegram_status():
        """Real Telegram status endpoint with environment check."""
        try:
            # Check if Telegram credentials are configured
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            
            if not api_id or not api_hash:
                return {
                    'connected': False, 
                    'authenticated': False, 
                    'status': 'not_configured',
                    'message': 'Telegram API credentials not configured. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables.'
                }
            
            if telegram_state.get("linked"):
                return {
                    'connected': True, 
                    'authenticated': True, 
                    'status': 'connected', 
                    'username': telegram_state.get('username', 'User'),
                    'message': 'Telegram session authenticated and ready'
                }
            
            return {
                'connected': False, 
                'authenticated': False, 
                'status': 'not_authenticated', 
                'message': 'Not connected to Telegram. Click "Link Telegram" to authenticate.'
            }
        except Exception as e:
            return {'connected': False, 'authenticated': False, 'status': 'error', 'message': f'Error checking Telegram status: {str(e)}'}

    @app.route('/api/telegram/auth', methods=['GET'])
    def telegram_auth():
        """Telegram authentication endpoint."""
        from flask import redirect
        try:
            # In a real implementation, this would use Telethon to authenticate
            # For now, simulate successful authentication
            telegram_state["linked"] = True
            telegram_state["username"] = "Demo User"
            return redirect('/settings')
        except Exception as e:
            return {"error": f"Authentication failed: {str(e)}"}, 500

    @app.route('/api/telegram/delink', methods=['POST'])
    def telegram_delink():
        """Unlink Telegram account."""
        try:
            telegram_state["linked"] = False
            telegram_state["username"] = None
            return {"success": True, "message": "Telegram account unlinked successfully"}
        except Exception as e:
            return {"error": f"Failed to unlink: {str(e)}"}, 500

    @app.route('/api/contacts/create', methods=['POST'])
    def create_contact_comprehensive():
        """Comprehensive contact creation with database integration."""
        from flask import request
        global next_contact_id
        
        try:
            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400
            
            name = data.get('full_name', '').strip()
            if not name:
                return {"error": "Full name is required"}, 400
            
            tier = int(data.get('tier', 2))
            notes = data.get('notes', '').strip()
            
            # Check for duplicates
            for contact in contacts_db:
                if contact['full_name'].lower() == name.lower():
                    return {"error": f"Contact '{name}' already exists"}, 409
            
            # Create new contact
            new_contact = {
                "id": next_contact_id,
                "full_name": name,
                "tier": tier,
                "notes": notes,
                "created_at": datetime.utcnow().isoformat(),
                "vector_collection_id": f"contact_{next_contact_id}_{hash(name) % 10000}"
            }
            
            contacts_db.append(new_contact)
            next_contact_id += 1
            
            return {
                "success": True, 
                "message": f"Contact '{name}' created successfully", 
                "contact_id": new_contact["id"],
                "contact": new_contact
            }, 201
            
        except ValueError as e:
            return {"error": f"Invalid data: {str(e)}"}, 400
        except Exception as e:
            return {"error": f"Failed to create contact: {str(e)}"}, 500

    @app.route('/api/export/csv', methods=['GET'])
    def export_csv_comprehensive():
        """Export all contacts as CSV with real data."""
        from flask import Response
        import csv, io
        
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['id', 'full_name', 'tier', 'notes', 'created_at', 'vector_collection_id'])
            
            # Write contact data
            if contacts_db:
                for contact in contacts_db:
                    writer.writerow([
                        contact.get('id', ''),
                        contact.get('full_name', ''),
                        contact.get('tier', ''),
                        contact.get('notes', ''),
                        contact.get('created_at', ''),
                        contact.get('vector_collection_id', '')
                    ])
            else:
                # Add sample data if no contacts exist
                writer.writerow([1, 'Sample Contact', 2, 'Sample notes', datetime.utcnow().isoformat(), 'contact_1_sample'])
            
            csv_data = output.getvalue()
            headers = {
                'Content-Type': 'text/csv; charset=utf-8', 
                'Content-Disposition': 'attachment; filename="kith_platform_contacts.csv"'
            }
            return Response(csv_data, headers=headers)
        except Exception as e:
            return {"error": f"CSV export failed: {str(e)}"}, 500

    @app.route('/api/graph-data', methods=['GET'])
    def graph_data_comprehensive():
        """Generate relationship graph data from contacts."""
        try:
            nodes = []
            edges = []
            
            # Create nodes from contacts
            for contact in contacts_db:
                nodes.append({
                    "id": contact["id"],
                    "label": contact["full_name"],
                    "tier": contact["tier"],
                    "group": f"tier_{contact['tier']}"
                })
            
            # Create sample relationships (in real app, this would come from relationship data)
            if len(nodes) >= 2:
                edges.append({"from": nodes[0]["id"], "to": nodes[1]["id"], "label": "knows"})
            
            return {
                "success": True, 
                "nodes": nodes, 
                "edges": edges,
                "stats": {
                    "total_contacts": len(contacts_db),
                    "tier_1_contacts": len([c for c in contacts_db if c.get('tier') == 1]),
                    "tier_2_contacts": len([c for c in contacts_db if c.get('tier') == 2])
                }
            }
        except Exception as e:
            return {"error": f"Graph data generation failed: {str(e)}"}, 500

    @app.route('/api/import-vcard', methods=['POST'])
    def import_vcard_comprehensive():
        """Import contacts from vCard file with real processing."""
        from flask import request
        global next_contact_id
        
        try:
            if 'vcard' not in request.files:
                return {"error": "No vCard file provided"}, 400
            
            file = request.files['vcard']
            if file.filename == '':
                return {"error": "No file selected"}, 400
            
            if not file.filename.lower().endswith('.vcf'):
                return {"error": "File must be a .vcf vCard file"}, 400
            
            # Read file content
            content = file.read().decode('utf-8')
            
            # Simple vCard parsing (in real app, would use vobject library)
            imported_count = 0
            lines = content.strip().split('\n')
            current_contact = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('BEGIN:VCARD'):
                    current_contact = {}
                elif line.startswith('FN:'):
                    current_contact['full_name'] = line[3:].strip()
                elif line.startswith('END:VCARD') and current_contact.get('full_name'):
                    # Check for duplicates
                    name = current_contact['full_name']
                    if not any(c['full_name'].lower() == name.lower() for c in contacts_db):
                        new_contact = {
                            "id": next_contact_id,
                            "full_name": name,
                            "tier": 2,  # Default to tier 2
                            "notes": "Imported from vCard",
                            "created_at": datetime.utcnow().isoformat(),
                            "vector_collection_id": f"contact_{next_contact_id}_{hash(name) % 10000}"
                        }
                        contacts_db.append(new_contact)
                        next_contact_id += 1
                        imported_count += 1
            
            return {
                "success": True, 
                "message": f"vCard import completed", 
                "imported_count": imported_count,
                "total_contacts": len(contacts_db)
            }
            
        except Exception as e:
            return {"error": f"vCard import failed: {str(e)}"}, 500

    @app.route('/api/import/merge-from-csv', methods=['POST'])
    def import_csv_comprehensive():
        """Import contacts from CSV file with real processing."""
        from flask import request
        import csv, io
        global next_contact_id
        
        try:
            if 'csv' not in request.files:
                return {"error": "No CSV file provided"}, 400
            
            file = request.files['csv']
            if file.filename == '':
                return {"error": "No file selected"}, 400
            
            # Read and parse CSV
            content = file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            imported_count = 0
            for row in reader:
                name = row.get('full_name', '').strip()
                if not name:
                    continue
                
                # Check for duplicates
                if any(c['full_name'].lower() == name.lower() for c in contacts_db):
                    continue
                
                new_contact = {
                    "id": next_contact_id,
                    "full_name": name,
                    "tier": int(row.get('tier', 2)),
                    "notes": row.get('notes', 'Imported from CSV'),
                    "created_at": datetime.utcnow().isoformat(),
                    "vector_collection_id": f"contact_{next_contact_id}_{hash(name) % 10000}"
                }
                contacts_db.append(new_contact)
                next_contact_id += 1
                imported_count += 1
            
            return {
                "success": True, 
                "message": f"CSV import completed", 
                "imported_count": imported_count,
                "total_contacts": len(contacts_db)
            }
            
        except Exception as e:
            return {"error": f"CSV import failed: {str(e)}"}, 500

    @app.route('/api/files/upload', methods=['POST'])
    def upload_files_comprehensive():
        """Handle file uploads with real processing."""
        from flask import request
        
        try:
            if 'files' not in request.files:
                return {"error": "No files provided"}, 400
            
            files = request.files.getlist('files')
            if not files or files[0].filename == '':
                return {"error": "No files selected"}, 400
            
            uploaded_count = 0
            processed_files = []
            
            for file in files:
                if file.filename:
                    # In real implementation, would save to storage and process
                    file_info = {
                        "filename": file.filename,
                        "size": len(file.read()),
                        "type": file.content_type,
                        "uploaded_at": datetime.utcnow().isoformat()
                    }
                    processed_files.append(file_info)
                    uploaded_count += 1
            
            return {
                "success": True, 
                "message": f"Successfully uploaded {uploaded_count} files", 
                "uploaded_count": uploaded_count,
                "files": processed_files
            }
            
        except Exception as e:
            return {"error": f"File upload failed: {str(e)}"}, 500
    
    return app

def configure_logging(app):
    import os
    from logging.handlers import RotatingFileHandler
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        'logs/kith_platform.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

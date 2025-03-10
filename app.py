from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configuración específica para Render
# Ajusta la URL de la base de datos para manejar correctamente SQLite y PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Render usa 'postgres://', pero SQLAlchemy necesita 'postgresql://'
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///crm.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)
# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    customers = db.relationship('Customer', backref='user', lazy=True)
    contacts = db.relationship('Contact', backref='user', lazy=True)
    deals = db.relationship('Deal', backref='user', lazy=True)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='new')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    contacts = db.relationship('Contact', backref='customer', lazy=True)
    deals = db.relationship('Deal', backref='customer', lazy=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100))
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    stage = db.Column(db.String(20), default='prospect')
    close_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    related_type = db.Column(db.String(20))
    related_id = db.Column(db.Integer)
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Token Required Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'error': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

# Auth API Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user:
        return jsonify({'error': 'Email or password is incorrect'}), 401
    
    if check_password_hash(user.password, data.get('password')):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token, 'user': {'id': user.id, 'name': user.name, 'email': user.email}}), 200
    
    return jsonify({'error': 'Email or password is incorrect'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    existing_user = User.query.filter_by(email=data.get('email')).first()
    
    if existing_user:
        return jsonify({'error': 'Email already in use'}), 409
    
    hashed_password = generate_password_hash(data.get('password'), method='sha256')
    
    new_user = User(
        name=data.get('name'),
        email=data.get('email'),
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/auth/user', methods=['GET'])
@token_required
def get_user(current_user):
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email
    }), 200

# Customer API Routes
@app.route('/api/customers', methods=['GET'])
@token_required
def get_customers(current_user):
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    result = []
    
    for customer in customers:
        result.append({
            'id': customer.id,
            'name': customer.name,
            'company': customer.company,
            'email': customer.email,
            'phone': customer.phone,
            'status': customer.status,
            'notes': customer.notes,
            'created_at': customer.created_at.isoformat()
        })
    
    return jsonify(result), 200

@app.route('/api/customers', methods=['POST'])
@token_required
def create_customer(current_user):
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('company') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    new_customer = Customer(
        name=data.get('name'),
        company=data.get('company'),
        email=data.get('email'),
        phone=data.get('phone', ''),
        status=data.get('status', 'new'),
        notes=data.get('notes', ''),
        user_id=current_user.id
    )
    
    db.session.add(new_customer)
    db.session.commit()
    
    return jsonify({
        'id': new_customer.id,
        'name': new_customer.name,
        'company': new_customer.company,
        'email': new_customer.email,
        'phone': new_customer.phone,
        'status': new_customer.status,
        'notes': new_customer.notes,
        'created_at': new_customer.created_at.isoformat()
    }), 201

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@token_required
def update_customer(current_user, customer_id):
    customer = Customer.query.filter_by(id=customer_id, user_id=current_user.id).first()
    
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        customer.name = data.get('name')
    if data.get('company'):
        customer.company = data.get('company')
    if data.get('email'):
        customer.email = data.get('email')
    if data.get('phone') is not None:
        customer.phone = data.get('phone')
    if data.get('status'):
        customer.status = data.get('status')
    if data.get('notes') is not None:
        customer.notes = data.get('notes')
    
    db.session.commit()
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'company': customer.company,
        'email': customer.email,
        'phone': customer.phone,
        'status': customer.status,
        'notes': customer.notes,
        'created_at': customer.created_at.isoformat()
    }), 200

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@token_required
def delete_customer(current_user, customer_id):
    customer = Customer.query.filter_by(id=customer_id, user_id=current_user.id).first()
    
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    db.session.delete(customer)
    db.session.commit()
    
    return jsonify({'message': 'Customer deleted'}), 200

# Contact API Routes
@app.route('/api/contacts', methods=['GET'])
@token_required
def get_contacts(current_user):
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    result = []
    
    for contact in contacts:
        result.append({
            'id': contact.id,
            'name': contact.name,
            'position': contact.position,
            'email': contact.email,
            'phone': contact.phone,
            'notes': contact.notes,
            'customer_id': contact.customer_id,
            'customer_name': contact.customer.name,
            'created_at': contact.created_at.isoformat()
        })
    
    return jsonify(result), 200

@app.route('/api/contacts', methods=['POST'])
@token_required
def create_contact(current_user):
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email') or not data.get('customer_id'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify customer belongs to current user
    customer = Customer.query.filter_by(id=data.get('customer_id'), user_id=current_user.id).first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    new_contact = Contact(
        name=data.get('name'),
        position=data.get('position', ''),
        email=data.get('email'),
        phone=data.get('phone', ''),
        notes=data.get('notes', ''),
        customer_id=data.get('customer_id'),
        user_id=current_user.id
    )
    
    db.session.add(new_contact)
    db.session.commit()
    
    return jsonify({
        'id': new_contact.id,
        'name': new_contact.name,
        'position': new_contact.position,
        'email': new_contact.email,
        'phone': new_contact.phone,
        'notes': new_contact.notes,
        'customer_id': new_contact.customer_id,
        'customer_name': customer.name,
        'created_at': new_contact.created_at.isoformat()
    }), 201

@app.route('/api/contacts/<int:contact_id>', methods=['PUT', 'DELETE'])
@token_required
def manage_contact(current_user, contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if data.get('name'):
            contact.name = data.get('name')
        if data.get('position') is not None:
            contact.position = data.get('position')
        if data.get('email'):
            contact.email = data.get('email')
        if data.get('phone') is not None:
            contact.phone = data.get('phone')
        if data.get('notes') is not None:
            contact.notes = data.get('notes')
        if data.get('customer_id'):
            # Verify customer belongs to current user
            customer = Customer.query.filter_by(id=data.get('customer_id'), user_id=current_user.id).first()
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
            contact.customer_id = data.get('customer_id')
        
        db.session.commit()
        
        return jsonify({
            'id': contact.id,
            'name': contact.name,
            'position': contact.position,
            'email': contact.email,
            'phone': contact.phone,
            'notes': contact.notes,
            'customer_id': contact.customer_id,
            'customer_name': contact.customer.name,
            'created_at': contact.created_at.isoformat()
        }), 200
    
    elif request.method == 'DELETE':
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({'message': 'Contact deleted'}), 200

# Deal API Routes
@app.route('/api/deals', methods=['GET'])
@token_required
def get_deals(current_user):
    deals = Deal.query.filter_by(user_id=current_user.id).all()
    result = []
    
    for deal in deals:
        close_date = deal.close_date.isoformat() if deal.close_date else None
        result.append({
            'id': deal.id,
            'title': deal.title,
            'value': deal.value,
            'stage': deal.stage,
            'close_date': close_date,
            'notes': deal.notes,
            'customer_id': deal.customer_id,
            'customer_name': deal.customer.name,
            'created_at': deal.created_at.isoformat()
        })
    
    return jsonify(result), 200

@app.route('/api/deals', methods=['POST'])
@token_required
def create_deal(current_user):
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('value') or not data.get('customer_id'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify customer belongs to current user
    customer = Customer.query.filter_by(id=data.get('customer_id'), user_id=current_user.id).first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    close_date = None
    if data.get('close_date'):
        try:
            close_date = datetime.datetime.strptime(data.get('close_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    new_deal = Deal(
        title=data.get('title'),
        value=data.get('value'),
        stage=data.get('stage', 'prospect'),
        close_date=close_date,
        notes=data.get('notes', ''),
        customer_id=data.get('customer_id'),
        user_id=current_user.id
    )
    
    db.session.add(new_deal)
    db.session.commit()
    
    return jsonify({
        'id': new_deal.id,
        'title': new_deal.title,
        'value': new_deal.value,
        'stage': new_deal.stage,
        'close_date': new_deal.close_date.isoformat() if new_deal.close_date else None,
        'notes': new_deal.notes,
        'customer_id': new_deal.customer_id,
        'customer_name': customer.name,
        'created_at': new_deal.created_at.isoformat()
    }), 201

@app.route('/api/deals/<int:deal_id>', methods=['PUT', 'DELETE'])
@token_required
def manage_deal(current_user, deal_id):
    deal = Deal.query.filter_by(id=deal_id, user_id=current_user.id).first()
    
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if data.get('title'):
            deal.title = data.get('title')
        if data.get('value') is not None:
            deal.value = data.get('value')
        if data.get('stage'):
            deal.stage = data.get('stage')
        if data.get('close_date'):
            try:
                deal.close_date = datetime.datetime.strptime(data.get('close_date'), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        if data.get('notes') is not None:
            deal.notes = data.get('notes')
        if data.get('customer_id'):
            # Verify customer belongs to current user
            customer = Customer.query.filter_by(id=data.get('customer_id'), user_id=current_user.id).first()
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
            deal.customer_id = data.get('customer_id')
        
        db.session.commit()
        
        return jsonify({
            'id': deal.id,
            'title': deal.title,
            'value': deal.value,
            'stage': deal.stage,
            'close_date': deal.close_date.isoformat() if deal.close_date else None,
            'notes': deal.notes,
            'customer_id': deal.customer_id,
            'customer_name': deal.customer.name,
            'created_at': deal.created_at.isoformat()
        }), 200
    
    elif request.method == 'DELETE':
        db.session.delete(deal)
        db.session.commit()
        
        return jsonify({'message': 'Deal deleted'}), 200

# Task API Routes
@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks(current_user):
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    result = []
    
    for task in tasks:
        related_name = ""
        if task.related_type == 'customer' and task.related_id:
            related = Customer.query.filter_by(id=task.related_id, user_id=current_user.id).first()
            related_name = related.name if related else ""
        elif task.related_type == 'contact' and task.related_id:
            related = Contact.query.filter_by(id=task.related_id, user_id=current_user.id).first()
            related_name = related.name if related else ""
        elif task.related_type == 'deal' and task.related_id:
            related = Deal.query.filter_by(id=task.related_id, user_id=current_user.id).first()
            related_name = related.title if related else ""
        
        result.append({
            'id': task.id,
            'title': task.title,
            'related_type': task.related_type,
            'related_id': task.related_id,
            'related_name': related_name,
            'due_date': task.due_date.isoformat(),
            'priority': task.priority,
            'status': task.status,
            'description': task.description,
            'created_at': task.created_at.isoformat()
        })
    
    return jsonify(result), 200

@app.route('/api/tasks', methods=['POST'])
@token_required
def create_task(current_user):
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('due_date'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    related_id = data.get('related_id')
    related_type = data.get('related_type', '')
    
    # Verify related entity belongs to current user if provided
    if related_type and related_id:
        if related_type == 'customer':
            related = Customer.query.filter_by(id=related_id, user_id=current_user.id).first()
        elif related_type == 'contact':
            related = Contact.query.filter_by(id=related_id, user_id=current_user.id).first()
        elif related_type == 'deal':
            related = Deal.query.filter_by(id=related_id, user_id=current_user.id).first()
        else:
            related = None
        
        if not related:
            return jsonify({'error': 'Related entity not found'}), 404
    
    try:
        due_date = datetime.datetime.strptime(data.get('due_date'), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    new_task = Task(
        title=data.get('title'),
        related_type=related_type,
        related_id=related_id,
        due_date=due_date,
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'pending'),
        description=data.get('description', ''),
        user_id=current_user.id
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    related_name = ""
    if related_type == 'customer' and related_id:
        related = Customer.query.filter_by(id=related_id).first()
        related_name = related.name if related else ""
    elif related_type == 'contact' and related_id:
        related = Contact.query.filter_by(id=related_id).first()
        related_name = related.name if related else ""
    elif related_type == 'deal' and related_id:
        related = Deal.query.filter_by(id=related_id).first()
        related_name = related.title if related else ""
    
    return jsonify({
        'id': new_task.id,
        'title': new_task.title,
        'related_type': new_task.related_type,
        'related_id': new_task.related_id,
        'related_name': related_name,
        'due_date': new_task.due_date.isoformat(),
        'priority': new_task.priority,
        'status': new_task.status,
        'description': new_task.description,
        'created_at': new_task.created_at.isoformat()
    }), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@token_required
def manage_task(current_user, task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        
        if data.get('title'):
            task.title = data.get('title')
        
        if data.get('related_type') is not None or data.get('related_id') is not None:
            related_type = data.get('related_type', task.related_type)
            related_id = data.get('related_id', task.related_id)
            
            # Verify related entity belongs to current user if provided
            if related_type and related_id:
                if related_type == 'customer':
                    related = Customer.query.filter_by(id=related_id, user_id=current_user.id).first()
                elif related_type == 'contact':
                    related = Contact.query.filter_by(id=related_id, user_id=current_user.id).first()
                elif related_type == 'deal':
                    related = Deal.query.filter_by(id=related_id, user_id=current_user.id).first()
                else:
                    related = None
                
                if not related:
                    return jsonify({'error': 'Related entity not found'}), 404
            
            task.related_type = related_type
            task.related_id = related_id
        
        if data.get('due_date'):
            try:
                task.due_date = datetime.datetime.strptime(data.get('due_date'), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        
        if data.get('priority'):
            task.priority = data.get('priority')
        
        if data.get('status'):
            task.status = data.get('status')
        
        if data.get('description') is not None:
            task.description = data.get('description')
        
        db.session.commit()
        
        related_name = ""
        if task.related_type == 'customer' and task.related_id:
            related = Customer.query.filter_by(id=task.related_id).first()
            related_name = related.name if related else ""
        elif task.related_type == 'contact' and task.related_id:
            related = Contact.query.filter_by(id=task.related_id).first()
            related_name = related.name if related else ""
        elif task.related_type == 'deal' and task.related_id:
            related = Deal.query.filter_by(id=task.related_id).first()
            related_name = related.title if related else ""
        
        return jsonify({
            'id': task.id,
            'title': task.title,
            'related_type': task.related_type,
            'related_id': task.related_id,
            'related_name': related_name,
            'due_date': task.due_date.isoformat(),
            'priority': task.priority,
            'status': task.status,
            'description': task.description,
            'created_at': task.created_at.isoformat()
        }), 200
    
    elif request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Task deleted'}), 200

# Dashboard API
@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard(current_user):
    # Get customer count
    customer_count = Customer.query.filter_by(user_id=current_user.id).count()
    
    # Get open deals count
    open_deals = Deal.query.filter(
        Deal.user_id == current_user.id,
        Deal.stage.in_(['prospect', 'negotiation', 'proposal'])
    ).count()
    
    # Get current month's revenue
    current_date = datetime.datetime.now()
    start_of_month = datetime.datetime(current_date.year, current_date.month, 1)
    end_of_month = (start_of_month.replace(month=start_of_month.month % 12 + 1, day=1) if start_of_month.month < 12 
                   else start_of_month.replace(year=start_of_month.year + 1, month=1, day=1)) - datetime.timedelta(days=1)
    
    month_revenue = db.session.query(db.func.sum(Deal.value)).filter(
        Deal.user_id == current_user.id,
        Deal.stage == 'won',
        Deal.close_date.between(start_of_month.date(), end_of_month.date())
    ).scalar() or 0
    
    # Get pending tasks count
    pending_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status.in_(['pending', 'in_progress'])
    ).count()
    
    # Get recent activity
    recent_activities = []
    
    # Recent customers
    recent_customers = Customer.query.filter_by(user_id=current_user.id).order_by(Customer.created_at.desc()).limit(3).all()
    for customer in recent_customers:
        recent_activities.append({
            'type': 'customer',
            'message': f'Se agregó el cliente {customer.name}',
            'time': customer.created_at.isoformat()
        })
    
    # Recent deals
    recent_deals = Deal.query.filter_by(user_id=current_user.id).order_by(Deal.created_at.desc()).limit(3).all()
    for deal in recent_deals:
        recent_activities.append({
            'type': 'deal',
            'message': f'Se creó la oportunidad {deal.title} por ${deal.value}',
            'time': deal.created_at.isoformat()
        })
    
    # Sort activities by time
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:5]  # Limit to 5 activities
    
    return jsonify({
        'customer_count': customer_count,
        'open_deals': open_deals,
        'month_revenue': month_revenue,
        'pending_tasks': pending_tasks,
        'recent_activities': recent_activities
    }), 200

with app.app_context():
    db.create_all()

# Configuración para Render - usa el puerto asignado por la plataforma
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

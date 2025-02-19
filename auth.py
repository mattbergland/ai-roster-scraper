from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import stripe
from os import getenv

auth = Blueprint('auth', __name__)
stripe.api_key = getenv('STRIPE_SECRET_KEY')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('auth.signup'))
        
        # Create Stripe customer
        customer = stripe.Customer.create(email=email)
        
        # Create user
        user = User(email=email, stripe_customer_id=customer.id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('main.pricing'))
    
    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
            
        flash('Invalid email or password')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    try:
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': getenv('STRIPE_PRICE_ID'),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription/cancel',
        )
        return {'checkoutUrl': checkout_session.url}
    except Exception as e:
        return {'error': str(e)}, 400

@auth.route('/subscription/success')
@login_required
def subscription_success():
    session_id = request.args.get('session_id')
    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        subscription = stripe.Subscription.retrieve(session.subscription)
        
        current_user.subscription_status = subscription.status
        current_user.subscription_end = datetime.fromtimestamp(subscription.current_period_end)
        db.session.commit()
        
        flash('Successfully subscribed!')
    return redirect(url_for('main.dashboard'))

@auth.route('/subscription/cancel')
@login_required
def subscription_cancel():
    flash('Subscription cancelled')
    return redirect(url_for('main.pricing'))

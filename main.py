from datetime import datetime, timedelta
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session, jsonify
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, JSON, DateTime, func, UniqueConstraint, desc, Boolean, Float
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import random
from typing import List
import pandas as pd
from supermemo2 import first_review, review
from definitions import update_card, initialize_decks_and_cards, get_flashcards_for_today
from database import db, User, Card, Deck

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI", 'sqlite:////Users/danibuchsbaum/Acadalang/instance/acadalang_users.db')

Bootstrap5(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# HOME
@app.route('/', methods=['POST', 'GET'])
def home():

    if current_user.is_authenticated:
        decks = db.session.query(Deck).all()
        deck_size = []
        for deck in decks:
            if deck.date < datetime.now().date() - timedelta(days=2):
                deck.streak = 0
                db.session.commit()
            size = get_flashcards_for_today(deck)
            deck_size.append(len(size))
    
        return render_template("home.html", active_page='home', decks=decks, deck_size=deck_size)

    return render_template("home.html", active_page='home')


# FLASHCARDS ROUTE
@app.route('/flashcards/<deck_name>', methods=['POST', 'GET'])
def flashcards(deck_name):

    card_id = request.args.get('card_id')
    chosen_deck = db.session.query(Deck).where(Deck.name == deck_name).first()
    counter = session.get('counter')

    if card_id == None:
        return redirect(url_for('hebrew', deck_id=chosen_deck.id))
    
    elif card_id == "end":
        return render_template("flashcards.html", lang='none', deck=chosen_deck, counter=counter)
        
    else:
        lang = session.get('lang')
        card = db.session.get(Card, card_id)
        return render_template("flashcards.html", card=card, lang=lang, deck=chosen_deck, counter=counter)


# ENGLISH SIDE LOGIC
@app.route('/english-side', methods=['POST', 'GET'])
def english():
    card_id = request.args.get('card_id')
    session['lang'] = 'hebrew'
    deck_name = request.args.get('deck_name')
    return redirect( url_for('flashcards', card_id=card_id, deck_name=deck_name))


# HEBREW SIDE LOGIC
@app.route('/hebrew-side', methods=['POST', 'GET'])
def hebrew():
    session['lang'] = 'english'
    card_id = request.args.get('card_id')
    deck_id = request.args.get('deck_id')

    deck = db.session.get(Deck, deck_id)
    deck_name = deck.name

    if card_id:
        rating = int(request.args.get('rating'))
        card = db.session.get(Card, card_id)
        update_card(card, rating)
        db.session.commit()

    # pick the next card at random
    card_list = get_flashcards_for_today(deck)

    if card_list:
        chosen_card = random.choice(card_list)
        card_id = chosen_card.id
        session['counter'] = len(card_list)

    else:
        return redirect( url_for('flashcards', card_id='end', deck_name=deck_name))

    return redirect( url_for('flashcards', card_id=card_id, deck_name=deck_name))


# LOGIN
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    user = db.session.execute(db.select(User).where(User.email == data['email'])).scalar()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return redirect(url_for('home'))
    elif user is None:
        flash("That email doesn't exist.")
        return redirect(url_for('home'))
    elif check_password_hash(user.password, data['password']) is False:
        flash("Incorrect password, try again.")
        return redirect(url_for('home'))


# LOGOUT
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# RESET CARDS
@app.route('/reset', methods=['GET', 'POST'])
def reset_cards():
    cards = db.session.query(Card).all()
    decks = db.session.query(Deck).all()
    for card in cards:
        card.next_shown = datetime.now()
        card.interval = 0
        card.seen = False

    for deck in decks:
        deck.unseen_count = 0

    db.session.commit()

    return redirect(url_for('home'))


# ADD CUSTOM DECK
@app.route('/custom-deck', methods=['GET', 'POST'])
def add_deck():

    if request.method == 'POST':
        data = request.form
        custom_deck = Deck(
            name = data['deck_name'],
            num_cards = 0,
            streak = 0,
        )
        db.session.add(custom_deck)
        db.session.commit()
    
    return redirect(url_for('home')) 




# REGISTER
@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        form_data = request.form
        email_exists = db.session.execute(db.select(User).where(User.email == form_data['someUnusualEmail'])).scalars().first()
        if email_exists:
            flash('That email address is already in use.')
            return redirect(url_for('register'))
        else:
            hashed_pass = generate_password_hash(form_data['someUnusualPassword'], method='pbkdf2:sha256', salt_length=8)
            new_user = User(
                email=form_data['someUnusualEmail'],
                password=hashed_pass,
                name=form_data['someUnusualName'],
            )
            db.session.add(new_user)
            db.session.commit()

            # add decks to user 

            initialize_decks_and_cards()

            login_user(new_user)
            return redirect(url_for('home'))
        
    return render_template("register.html", active_page='register')


if __name__ == "__main__":
    app.run(debug=True)

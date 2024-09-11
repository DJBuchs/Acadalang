from datetime import datetime, timedelta
import pandas as pd
from database import db, Deck, Card, User
import random


def update_card(card, rating):
    # SM2 Base Values
    initial_interval = 1
    deck = db.session.query(Deck).where(Deck.id == card.deck_id).scalar()

    if deck.date != datetime.now().date():
        deck.date = datetime.now().date()
        deck.unseen_count = 0
        deck.streak += 1
        db.session.commit()

    if card.seen == False:
        deck.unseen_count += 1
        card.seen = True
        db.session.commit()
    
    # Determine the interval based on the rating
    if rating == 0:  # Wrong answer
        card.next_shown = datetime.now()
        card.interval = 0
        card.ease_factor -= 0.5
        
    else:
        # Adjust interval based on previous interval and ease factor
        if card.interval == 0:
            # First correct answer after a wrong attempt
            card.interval = initial_interval
        else:
            # Update interval
            card.interval = card.interval * card.ease_factor
        
        # Update next_shown
        card.next_shown = datetime.now() + timedelta(days=card.interval)

        # Adjust ease factor based on rating
        if rating == 2:
            card.ease_factor -= 0.15  # Decrease ease factor if the rating is low

        elif rating == 3:
            card.ease_factor += 0.15  # Increase ease factor if the rating is high
    
    # Ensure ease factor remains within reasonable bounds
    card.ease_factor = max(1.3, min(card.ease_factor, 2.5))

    return card


def initialize_decks_and_cards(current_user):
    # Read word list and create 'Standard' deck
    df = pd.read_csv("./static/data/word_list.csv")
    standard_deck = Deck(name='Standard', num_cards=df.shape[0], user_id=current_user.id)
    
    # Read verb list and create 'Verbs' deck
    df_verbs = pd.read_csv("./static/data/verb_list.csv")
    verbs_deck = Deck(name='Verbs', num_cards=df_verbs.shape[0], user_id=current_user.id)
    
    # Start a session and perform operations
    try:
        # Add decks
        db.session.add_all([standard_deck, verbs_deck])
        db.session.flush()  # Flush to get the deck IDs

        # Prepare cards for 'Standard' deck
        standard_cards = [Card(english=pair['english'], hebrew=pair['hebrew'], transliteration=pair['transliteration'],
                                seen=False, next_shown=datetime.now(),
                                deck_id=standard_deck.id, interval=0) for pair in df.to_dict(orient="records")]
        
        # Prepare cards for 'Verbs' deck
        verbs_cards = [Card(english=pair['english'], hebrew=pair['hebrew'], transliteration=pair['transliteration'],
                            seen=False, next_shown=datetime.now(),
                            deck_id=verbs_deck.id, interval=0) for pair in df_verbs.to_dict(orient="records")]

        # Add cards
        db.session.bulk_save_objects(standard_cards + verbs_cards)
        
        # Commit all changes
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")


def get_flashcards_for_today(deck):

    unseen_list = db.session.query(Card).where(Card.deck_id == deck.id, datetime.now()>Card.next_shown, Card.seen==False).all()
    todays_unseens = []
    unseens_left = min(10 - deck.unseen_count, len(unseen_list))
    
    if unseens_left > 0:
        todays_unseens = random.sample(unseen_list, unseens_left)

    seen_list = db.session.query(Card).where(Card.deck_id == deck.id, datetime.now()>Card.next_shown, Card.seen==True).all()

    card_list = todays_unseens + seen_list

    return card_list





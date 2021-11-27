from logging import debug
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.choices import RadioField
import flask.scaffold
import datetime
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api, Resource, marshal, reqparse, abort, fields, marshal_with

app=Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SECRET_KEY'] = '22ee22f7b19d15dd4035b2fc'

db = SQLAlchemy(app)

class user(db.Model):   
    user_id = db.Column(db.Integer(), primary_key = True)
    user_name = db.Column(db.String(length = 50), nullable = False)
    email_id = db.Column(db.String(length = 50), nullable = False)
    password = db.Column(db.String(length = 50), nullable = True)
    user_decks = db.relationship('deck', backref = 'owned_user', lazy = True)
    

class deck(db.Model):
    deck_id = db.Column(db.Integer(), primary_key = True)
    deck_name = db.Column(db.String(length = 50), nullable = False)
    deck_score = db.Column(db.Integer(), nullable = False, default = 0) 
    deck_viewed = db.Column(db.Integer(), nullable = True, default = 0) #number of times reviewed
    deck_description = db.Column(db.String(length = 256), nullable = True)
    deck_owner = db.Column(db.Integer(), db.ForeignKey('user.user_id'), nullable = False)
    deck_public = db.Column(db.Integer(), nullable = False, default = 0)
    last_viewed = db.Column(db.DateTime(), nullable =False, default = datetime.datetime.now())
    deck_cards = db.relationship('card', backref = 'owned_deck', lazy = True)

    
class card(db.Model):
    card_id = db.Column(db.Integer(), primary_key = True)
    card_question = db.Column(db.String(length = 512), nullable = False)
    card_answer = db.Column(db.String(length = 512), nullable = False)
    #card_score = db.Column(db.Interger(), nullable = True, unique = False)
    deck_of_card = db.Column(db.Integer(), db.ForeignKey('deck.deck_id'), nullable = False)
 
    
class deckForm(FlaskForm):
    deck_name = StringField(label = "Name of Deck :")
    description = StringField(label = "Add Description : ")
    publish = RadioField(label = "Publish?:", choices = [('yes', 'Publish Deck for Everyone to See'), ('no', 'Keep Collection Private')])
    submit = SubmitField(label = "Create Deck")


class addForm(FlaskForm):
    question = StringField(label = "Question : ")
    answer = StringField(label = "Correct Answer : ")
    submit = SubmitField(label = "Create Card")
    
    
class viewForm(FlaskForm):  
    difficulty = RadioField(label = "Difficulty : ", choices = [('easy', 'Trivial'), ('medium', 'Had to think Hard'), ('hard', 'Got it wrong')])
    submit = SubmitField(label = "Next")


class registerForm(FlaskForm):
    username = StringField(label = "Enter Username")
    email_id = StringField(label = "Enter Email-Id")
    password1 = PasswordField(label = "Enter Password")
    password2 = PasswordField(label = "Confirm Password")
    submit = SubmitField(label = "Create Account")
    

class loginForm(FlaskForm):
    username = StringField(label = "Enter Username")
    password1 = PasswordField(label = "Enter Password")
    submit = SubmitField(label = "Login")
     
    
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():
        u = user.query.filter_by(user_name = form.username.data).first()
        if u != None and u.password == form.password1.data:
            if u.user_name == "sysadmin":
                return redirect(url_for('sysuser'))
            return redirect(url_for('mycards', uid = u.user_id))
        else:
            return redirect(url_for('login'))

    return render_template('login.html', form = form)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = registerForm()
    if form.validate_on_submit():        
        uname = form.username.data
        if user.query.filter_by(user_name = uname).first() != None:
            return redirect(url_for('register'))
        else :    
            new_user = user(user_name = form.username.data, email_id = form.email_id.data, password = form.password1.data)
            db.session.add(new_user)
            db.session.commit()
            default_deck = deck(deck_name = "Default", deck_owner = user.query.filter_by(user_name = form.username.data).first().user_id)
            db.session.add(default_deck)
            db.session.commit()
            return redirect(url_for('login'))
    elif request.method != 'POST':
        return render_template('register.html', form = form)    
    
@app.route('/<uid>/mycards') # dashboard
def mycards(uid):
    u = user.query.filter_by(user_id = uid).first()
    d = deck.query.filter_by(deck_owner = uid).order_by(-deck.deck_score)
    c = card.query.all()
    cards = []
    for ca in c:
        for de in d:
            if ca.deck_of_card == de.deck_id:
                cards.append(ca)

    return render_template('mycards.html', user = u, decks = d, cards = cards)

@app.route('/<uid>/modifycards',  methods = ['GET', 'POST']) # edit deck
def modifycards(uid):
    u = user.query.filter_by(user_id = uid).first()
    d = deck.query.filter_by(deck_owner = uid).order_by(-deck.deck_score)
    c = card.query.all()
    cards = []
    for ca in c:
        for de in d:
            if ca.deck_of_card == de.deck_id:
                cards.append(ca)
    return render_template('modifycards.html', user = u, decks = d, cards = cards)

@app.route('/<id>/adddeck.html', methods = ['GET', 'POST']) #crud deck
def adddeck(id):
    u = user.query.filter_by(user_id = id).first()
    form = deckForm()
    if form.validate_on_submit():
        pub = form.publish.data
        if pub == 'yes':
            deck_to_add = deck(deck_name = form.deck_name.data, deck_description = form.description.data, deck_owner = u.user_id, deck_score = 0, deck_viewed = 0, deck_public = 1)
        else:
            deck_to_add = deck(deck_name = form.deck_name.data, deck_description = form.description.data, deck_owner = u.user_id, deck_score = 0, deck_viewed = 0)

        db.session.add(deck_to_add)
        db.session.commit()
        return redirect(url_for('mycards', uid = u.user_id))
    return render_template('adddeck.html', users = u, form = form)

@app.route('/<id>/deletedeck.html') 
def deletedeck(id):
    d = deck.query.filter_by(deck_id = id).first()
    uid = d.deck_owner
    for c in card.query.all():
        if c.deck_of_card == id:
            card.query.filter_by(card_id = c.id).delete()
            db.session.commit()
    deck.query.filter_by(deck_id = id).delete()
    db.session.commit()
    return redirect(url_for('modifycards', uid = uid))

@app.route('/<did>/editdeck.html', methods = ['GET', 'POST'])
def editdeck(did):
    d = deck.query.filter_by(deck_id = did).first()
    did = d.deck_id 
    uid = d.deck_owner
    form = deckForm()
    if form.validate_on_submit():
        if not form.deck_name:
            return redirect(url_for('editdeck'), did = d.deck_owner)
        deck.query.filter_by(deck_id = did).delete()    
        db.session.commit()
        
        pub = form.publish.data
        if pub == 'yes':
            deck_to_add = deck(deck_id = did, deck_name = form.deck_name.data, deck_description = form.description.data, deck_owner = uid, deck_score = 0, deck_viewed = 0, deck_public = 1)
            db.session.add(deck_to_add)
            db.session.commit()
        else:
            deck_to_add = deck(deck_id = d.deck_id, deck_name = form.deck_name.data, deck_description = form.description.data, deck_owner = d.deck_owner, deck_score = 0, deck_viewed = 0)
            db.session.add(deck_to_add)
            db.session.commit()
        return redirect(url_for('mycards', uid = uid))
    return render_template('editdeck.html', form = form)

@app.route('/<id>/addcards.html', methods = ['GET', 'POST']) # crud cards
def addcards(id):
    u = user.query.all()
    d = deck.query.filter_by(deck_id = id).first()
    c = card.query.filter_by(deck_of_card = id)
    form = addForm()
    if form.validate_on_submit():
        card_to_add = card(card_question = form.question.data, card_answer = form.answer.data, deck_of_card = d.deck_id)
        parent_deck = deck.query.filter_by(deck_id = id).first()
        parent_deck.deck_score = deck.deck_score - deck.deck_score
        parent_deck.deck_viewed = deck.deck_viewed - deck.deck_viewed 
        db.session.add(card_to_add)
        db.session.commit()
        return redirect(url_for('modifycards', uid = parent_deck.deck_owner))
    return render_template('addcards.html', users = u, decks = d, cards = c, form = form)

@app.route('/<id>/deletecards.html')
def deletecards(id):
    
    d = deck.query.filter_by(deck_id = id).first()
    uid = deck.query.filter_by(deck_id = id).first().deck_owner
    u = user.query.filter_by(user_id = uid)
    c = card.query.filter_by(deck_of_card = id)
    return render_template('deletecards.html', users = u, decks = d, cards = c, uid = uid)

@app.route('/<id>/deletecard')
def deletecard(id):
    ca = card.query.filter_by(card_id = id).first()
    de = deck.query.all()
    for i in de:
        if i.deck_id == ca.deck_of_card:
            uid = i.deck_owner
            break 
        
    card.query.filter_by(card_id = id).delete()    
    db.session.commit()
    return redirect(url_for('modifycards', uid = uid))
     
@app.route('/<id>/viewdeck.html') # review
def viewdeck(id):
    cards = card.query.filter_by(deck_of_card = id)
    
    if not cards.first():
        uid = deck.query.filter_by(deck_id = id).first().deck_owner
        return redirect(url_for('modifycards', uid = uid ))
    
    a = cards[0].deck_of_card
    b = cards[0].card_id
    return redirect(url_for('viewcard', did = a, cid = b))

@app.route('/<did>/<cid>/viewcard', methods = ['POST', 'GET']) #review
def viewcard(did, cid):    

    form = viewForm()
    if form.validate_on_submit():
        t = form.difficulty.data

        if t == "easy":
            diff = 1
        elif t == "medium":
            diff = 0
        else:
            diff = -1

        t = deck.query.filter_by(deck_id = did).first()
        t.deck_score = deck.deck_score + diff
        t.update(dict(last_viewed = datetime.datetime.now()))
        db.session.commit()

        

    d = card.query.filter_by(deck_of_card = did)
    c = card.query.filter_by(card_id = cid).first()
    l = []
    for i in d:
        l.append(i)
        
    for i in range(len(l)):
        if l[i].card_id == c.card_id:
            if i < len(l) -1 :
                n = l[i+1]
            else:
                
                return redirect(url_for('mycards', uid = deck.query.filter_by(deck_id = did).first().deck_owner))
    
    return render_template('viewcard.html', all_cards = l, curr_card = c, next_card = n, deck = d, form = form)

@app.route('/publicdecks', methods = ['POST', 'GET']) #public decks view 
def publicdecks():
    decks = deck.query.filter_by(deck_public = True)
    users = {}
    for de in decks:
        for us in user.query.all():
            if de.deck_owner == us.user_id:
                users[de.deck_owner] = us.user_name
    return render_template('publicdecks.html', decks = decks, users = users)

@app.route('/<did>/viewpublicdecks', methods = ['POST', 'GET'])
def viewpublicdecks(did):
    cards = card.query.filter_by(deck_of_card = did)
    return render_template('viewpublicdecks.html', cards = cards)

@app.route('/<did>/importdecks', methods = ['POST', 'GET'])
def importdecks(did):    
    form = loginForm()
    if form.validate_on_submit():
        u = user.query.filter_by(user_name = form.username.data).first()
        if u != None and u.password == form.password1.data:

            de = deck.query.filter_by(deck_id = did).first()
            import_deck = deck(deck_name = de.deck_name, deck_owner = u.user_id, deck_description = de.deck_description, deck_public = False)
            db.session.add(import_deck)
            db.session.commit()
            
            for ca in card.query.all():
 
                if ca.deck_of_card == int(did):
                    import_card = card(card_question = ca.card_question, card_answer = ca.card_answer,
                                       deck_of_card = deck.query.filter_by(deck_owner = u.user_id).filter_by(deck_name = de.deck_name).first().deck_id)

                    db.session.add(import_card)
                    db.session.commit()
            return redirect(url_for('mycards', uid = u.user_id))
                    
        else:
            return redirect(url_for('importdecks', did = did))

    return render_template('login.html', form = form)

@app.route('/sysuser') #system admin view
def sysuser():
    u = user.query.all()
    d = deck.query.all()
    c = card.query.all()
    return render_template('sysuser.html', users = u, decks = d, cards = c)

@app.route('/sysdeck/<uid>', methods = ['GET', 'POST'])
def sysdeck(uid):
    u = user.query.filter_by(user_id = uid).first()
    d = deck.query.filter_by(deck_owner = uid)
    c = []
    for ca in card.query.all():
        for de in d:
            if de.deck_id == ca.deck_of_card:
                c.append(ca)
    if request.method == 'POST':
        d = deck.query.filter_by(deck_owner = uid)
        for de in d:    
            for c in card.query.all():
                if c.deck_of_card == de.deck_id:
                    db.session.delete(c)
                    db.session.commit()
        for de in d:
            db.session.delete(de)
            db.session.commit()
        user.query.filter_by(user_id = uid).delete()
        db.session.commit()
        return redirect(url_for('sysuser'))
    return render_template('sysdeck.html', users = u, decks = d, cards = c)

@app.route('/syscard/<did>', methods = ['GET', 'POST'])
def syscard(did):
    d = deck.query.filter_by(deck_id = did).first()
    u = user.query.filter_by(user_id = d.deck_owner).first()
    c = card.query.filter_by(deck_of_card = did)
    if request.method == 'POST':
        uid = deck.query.filter_by(deck_id = did).first().deck_owner
        for c in card.query.all():
            if c.deck_of_card == did:
                db.session.delete(c)
                db.session.commit()
        deck.query.filter_by(deck_id = did).delete()
        db.session.commit()
        return redirect(url_for('sysdeck', uid = uid))
    return render_template('syscard.html', users = u, decks = d, cards = c)
    
@app.route('/sysview/<cid>', methods = ['GET', 'POST'])
def sysview(cid):
    c = card.query.filter_by(card_id = cid)
    if request.method == 'POST':
        did = card.query.filter_by(card_id = cid).first().deck_of_card
        card.query.filter_by(card_id = cid).delete()
        db.session.commit()
        return redirect(url_for('syscard', did = did ))
    return render_template('sysview.html', cards = c)

#----------------------------api routing

#CRUD for user
user_put_args = reqparse.RequestParser()
user_put_args.add_argument("username", type = str, help = "Username not given", required = True)
user_put_args.add_argument("password", type = str, help = "Password not given", required = True)
user_put_args.add_argument("email_id", type = str, help = "Email-Id not given", required = True)

user_fields = {
    'user_id':fields.Integer,
    'user_name':fields.String,
    'password':fields.String,
    'email_id':fields.String
}

class user_api(Resource):
    @marshal_with(user_fields)
    def get(self, username):
        usr = user.query.filter_by(user_name = username).first()
        return usr

    #@marshal_with(user_fields)
    def put(self, username):

        args = user_put_args.parse_args()
    
        for i in user.query.all():
            if i.user_name == username:
                return 'Username already exists'
        if not args.username == username:
            return 'Cannot add that resource as username provided in url and json dont match'
        else:
            usr = user(user_name = username, password = args['password'], email_id = args['email_id'])
            db.session.add(usr)
            db.session.commit()
            return 'Succesfully added user'
        
    #@marshal_with(user_fields)
    def delete(self, username):
        usr = user.query.filter_by(user_name = username).first()
        if not user.user_name :
            return 'User doesnt exist'
        else:
            uid = usr.user_id
            for d in deck.query.all():
                if d.deck_owner == uid:
                    did = d.deck_id
                    for c in card.query.all():
                        if c.deck_of_card == did:
                            card.query.filter_by(card_id = c.card_id).delete()
                            db.session.commit()
                    deck.query.filter_by(deck_id = d.deck_id).delete()
                    db.session.commit()
            user.query.filter_by(user_name = username).delete()
            db.session.commit()
            return 'Deleted succesfully'
    
    @marshal_with(user_fields)
    def patch(self, username):
        usr = user.query.filter_by(user_name = username).first()
    
        if not user.user_name:
            return usr, 204 
        args = user_put_args.parse_args()
        if not usr.password == args['password']:
            return 'Not updated, password and username dont match', 202 
        uid = usr.user_id
        uname = usr.user_name
        eid = usr.email_id
        pwrd = usr.password
        new_usr = user(user_id = uid, user_name = args['username'], email_id = args['email_id'], 
                       password = pwrd )
        db.session.delete(usr)
        db.session.commit()
        
        db.session.add(new_usr)
        db.session.commit()
        return new_usr                
api.add_resource(user_api, "/api/user/<string:username>")

#CRUD for deck
deck_arg = reqparse.RequestParser()
deck_arg.add_argument("deckname", type = str, help = "Name of deck not provided", required = True)
deck_arg.add_argument("deckdesc", type = str, help = "You may publish a description for the deck")
deck_arg.add_argument("deckpublic", type = bool, help = "Do you want to pusblish the deck?", required = True)
deck_arg.add_argument("password", type = str, help = "Enter the password of the user", required = True)

deck_fields = {
    'deck_name' : fields.String,
    'deck_description' : fields.String,
    'deck_public' : fields.Boolean,
    'deck_score' : fields.Integer,
    'deck_viewed' : fields.Integer
}

class deck_api(Resource):
    @marshal_with(deck_fields)
    def get(self, username, deckname):
        usr = user.query.filter_by(user_name = username).first()
        dk = []
        for d in deck.query.all():
            if d.deck_name == deckname and d.deck_owner == usr.user_id:
                dk.append(d)
        if len(dk) == 0:
            return f'No decks found with {deckname} as name of deck'
        else:
            return dk[0]
    
    @marshal_with(deck_fields) 
    def put(self, username, deckname):
        args = deck_arg.parse_args()
        usr = user.query.filter_by(user_name = username).first()
        if not usr:
            return 'User not found'
        if not usr.password == args['password']:
            return 'Username and password mismatch'
        new_deck = deck(deck_name = args['deckname'], deck_description = args['deckdesc'], 
                        deck_public = args['deckpublic'], deck_owner = usr.user_id)
        db.session.add(new_deck) 
        db.session.commit()
        return new_deck

    def delete(self, username, deckname):
        usr = user.query.filter_by(user_name = username).first()
        dk = deck.query.filter_by(deck_name = deckname)
        for d in dk:
            if d.deck_owner == usr.user_id:
                dk = d 
                break
        if not dk:
            return 'No decks with that name'
        for c in card.query.all():
            if c.deck_of_card == dk.deck_id:
                db.session.delete(c)
                db.session.commit()
        db.session.delete(dk)
        db.session.commit()
        return 'Deleted'
        
    @marshal_with(deck_fields)
    def patch(self, username, deckname):
        usr = user.query.filter_by(user_name = username).first()
        args = deck_arg.parse_args()
        dk = 0
        for d in deck.query.all():
            if d.deck_name == deckname and d.deck_owner == usr.user_id:
                dk = d
                break
 
        if not usr.password == args['password']:
            return 'Username and password mismatch'

        if not dk:
            return 'No decks with that name'
        new_deck = deck(deck_name = args['deckname'], deck_id = dk.deck_id, deck_description = args['deckdesc'],
                        deck_public = args['deckpublic'], deck_owner = usr.user_id)
        db.session.delete(dk)
        db.session.commit()        
        db.session.add(new_deck)
        db.session.commit()
        return new_deck 
api.add_resource(deck_api, "/api/deck/<string:username>/<string:deckname>")

#CRUD for card
# card_arg = reqparse.RequestParser()
# card_arg.add_argument("cardquestion", type = str, help = "Question on card not provided", required = True)
# card_arg.add_argument("cardanswer", type = str, help = "Answer on card not provided", required = True)

# card_fields = {
#     'card_question' : fields.String,
#     'card_answer' : fields.String,
#     'card_id' : fields.Integer
# }


# class card_api(Resource):
#     @marshal_with(card_fields)
#     def get(self, deckid, cardid):
#         if not cardid:
#             return 'yes'
    
# api.add_resource(deck_api, "/api/card/<int:deckid>/<int:cardid>")


if __name__ == "__main__":
    app.run(debug=True)

#~api~
#~edit deck~
#error messages

#sysadmin 123
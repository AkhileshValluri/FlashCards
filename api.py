from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api, Resource, marshal, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from app import user as User
from app import card as Card
from app import deck as Deck 
from app import db as DB 
import requests

app = Flask(__name__)
api = Api(app)
app.config['SQL_ALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
db = SQLAlchemy(app)

user_put_args = reqparse.RequestParser()
user_put_args.add_argument("username", type = str, help = "Username is not given", required = True)
user_put_args.add_argument("password", type = str, help = "Password for user is not given", required = True)
user_put_args.add_argument("email", type = str, help = "Email-Id is not given", required = True)

user_fields = {
    
    'user_name' : fields.String,
    'password' : fields.String,
    'email_id' : fields.String 
}

class user(Resource):
    def get(self, username):
        usr = User.query.filter_by(user_name = username).first()
        return usr

    def put(self, username):
        args = user_put_args.parse_args()
        usrs = DB.User.query.all()
        for i in usrs:
            if i.user_name == username:
                return 'User with that username already exists'
        if not args.username == username:
            return 'The url and username do not match, you cannot put that record there '
        else:
            usr = User(user_name = username, user_password = args['password'], email_id = args['email_id'])
            DB.session.add(usr)
            DB.session.commit()
            return f'Successfully added user : {usr}' 
        

api.add_resource(user, "/user/<string:username>")



if __name__ == "__main__":
    app.run(debug = True)
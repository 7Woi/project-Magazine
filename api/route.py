from flask import request
from flask_api import status
from bson.json_util import loads, dumps
from pymongo import MongoClient

import services


# TODO IMPORTANT : use flask_restful for a real flask api (big refactor)
# TODO : refactor routes and queries access
# TODO : find a way like javascript spread operator for queries customization
# TODO : discuss about before_request and after_this_request decorators for response and headers settings
# TODO : Custom response class. Link  : https://blog.miguelgrinberg.com/post/customizing-the-flask-response-class
# TODO : discuss about the terminology in responses messages
# (example : what to return when it's the right email but wrong password ?)
# TODO : handle errors when mongodb is off during an request
# TODO : use Blueprint http://flask.pocoo.org/docs/0.12/blueprints/#blueprints
# TODO FUN : store data for machine learning user analytics


class Route:
    def __init__(self, app):
        client = MongoClient('mongodb://localhost:27017/')
        db = client.magazine

        @app.route("/", methods=['GET'])
        def index():
            return "Bienvenue sur la page d'accueil du Magazine. Le site est actuellement en construction"

        @app.route("/home", methods=['GET'])
        def home():
            # TODO : send important data for Home page (last Magazine numbers, top trending, discover new category, news)
            return "Home"

        @app.route("/login", methods=['POST'])
        def login():
            # TODO : check if token exists in request.headers (user is already logged)
            req = services.validate_request(request)
            res = services.create_default_response(app)

            if hasattr(req, 'err'):
                res.status_code = req.status_code
                res.response = req.err
                return res

            try:
                # TODO : custom queries with dynamic args handling (props used in query and result props wanted)
                result_query = db.users.find_one({"email": req.data["email"]}, {"_id":False})
            except:
                res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                res.response = dumps({"message" : "Server error"})
                return res

            if result_query is None:
                res.status_code = status.HTTP_401_UNAUTHORIZED
                res.response = dumps({"message" : "Wrong login"})
                return res
            else:
                data = result_query

                if not services.validate_user_password(req.data["password"].encode('utf-8'), data["password"]):
                    res.status_code = status.HTTP_401_UNAUTHORIZED
                    res.response = dumps({"message": "Wrong password"})
                else:
                    res.status_code = status.HTTP_200_OK
                    # TODO : format data before send response (prevent api to send sensible data)
                    # TODO : check if token already exists
                    del data["password"]
                    # TODO : Implement OAuth2 and review his flaws (exemple : https://tools.ietf.org/html/rfc6749#section-10.12 )
                    # TODO : check if boolean remember me for extend token duration
                    res.response = dumps({"user": data, "jwt": services.get_auth_token(result_query['username'])})
            return res

        # TODO : add auth guard
        # @app.route("/logout", methods=['POST'])
        # def logout():
        #     # TODO : use request.data to find the user and unvalidate his auth token
        #     req = services.validate_request(request)
        #     res = services.create_default_response(app)
        #
        #     services.disconnectUser(req.data["users"])
        #
        #     return res

        # TODO : add auth guard
        @app.route("/magazine", methods=['GET'])
        def get_magazine():
            # TODO : Discuter des données contenues dans l'accueil du magazine

            return "Magazine"
        
        # TODO : add auth guard
        @app.route("/users/", methods=['GET'])
        def get_users():
            req = services.validate_request(request)
            res = services.create_default_response(app)

            try:
                result_query = dumps(db.users.find())
            except:
                res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                res.response = "Server error"
                return res

            res.status_code = status.HTTP_200_OK
            res.response = result_query

            return res

        # Public route
        @app.route("/posts/", methods=['GET'])
        def get_posts():
            res = services.create_default_response(app)


            # TODO : faire une validation sur le request.data pour savoir quels posts récupérer
            try:
                result_query = dumps(db.posts.find())
            except:
                res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                res.response = "Server error"
                return res

            res.status_code = status.HTTP_200_OK
            res.response = result_query

            return res

        @app.route("/posts/", methods=['POST'])
        def add_post():
            req = services.validate_request(request)
            res = services.create_default_response(app)

            if hasattr(req, 'err'):
                res.status_code = req.status_code
                res.response = req.err
                return res

            try:
                result_query = dumps(db.posts.insert_one(req.data["post"]))
            except:
                res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                res.response = "Server error"
                return res

            if result_query is None:
                res.status_code = status.HTTP_204_NO_CONTENT
                res.response = "Problem"
            else:
                res.status_code = status.HTTP_201_CREATED
                res.response = result_query

            return res

        @app.route("/posts/<int:uuidPost>", methods=['GET'])
        def get_post():
            req = services.validate_request(request)
            res = services.create_default_response(app)

            if hasattr(req, 'err'):
                res.status_code = req.status_code
                res.response = req.err
                return res

            try:
                # TODO : custom queries with dynamic args handling (props used in query and result props wanted)
                result_query = db.posts.find_one({"uuidPost": req.data["uuidPost"]}, {"_id":False})
            except:
                res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                res.response = dumps({"message" : "Server error"})
                return res

            if result_query is None:
                res.status_code = status.HTTP_404_NOT_FOUND
                res.response = dumps({"message" : "Wrong login"})
                return res
            else:
                data = result_query
                # TODO : check if private post
                res.status_code = status.HTTP_200_OK
                res.response = dumps({"post":data})

            return res
        
        @app.route("/posts/<int:uuidPost>/comments", methods=['GET'])
        def get_comments():
            req = services.validate_request(request)
            res = services.create_default_response(app)

            if hasattr(req, 'err'):
                res.status_code = req.status_code
                res.response = req.err
                return res

            try:
                result_query = dumps(db.comments.find({"uuidPost": req.data["uuidPost"]}, {"_id":False}))
            except:
                res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                res.response = "Server error"
                return res

            if result_query is None:
                res.status_code = status.HTTP_404_NOT_FOUND
                res.response = dumps({"message" : "Wrong login"})
                return res
            else:
                data = result_query
                res.status.code = res.status_code = status.HTTP_200_OK
                res.response = dumps({"comments": data})
            
            return res

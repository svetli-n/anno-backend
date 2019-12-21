from flask import send_file
from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt,
)

from models import (
    UserModel,
    RevokedTokenModel,
    LabeledDatasetModel,
    UnlabeledDatasetModel,
)

parser = reqparse.RequestParser()
parser.add_argument("username", help="User name")
parser.add_argument("password", help="Password")
parser.add_argument("unlabeled_dataset_id", help="Not yet evaluated item")
parser.add_argument("label", help="Label given by user")
parser.add_argument("get_all", help="Fetch all, not only unlabeled")
parser.add_argument("img", help="Image name")


def username_password():
    data = parser.parse_args()
    return data["username"], data["password"]


def access_refresh_tokens(username):
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return access_token, refresh_token


class UserRegistration(Resource):
    def post(self):
        username, password = username_password()

        if UserModel.find_by_username(username):
            return {"msg": f"User {username} already exists"}, 400

        current_user = UserModel(
            username=username, password=UserModel.generate_hash(password)
        )
        try:
            current_user.save()
            access_token, refresh_token = access_refresh_tokens(username)
            return {
                "msg": f"User {current_user} was created",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "username": username,
            }
        except Exception as e:
            return {"msg": str(e)}, 500


class UserLogin(Resource):
    def post(self):
        username, password = username_password()

        current_user = UserModel.find_by_username(username)

        if current_user is None:
            return {"msg": f"User {username} does not exist"}, 400

        if not UserModel.verify_hash(password=password, hash=current_user.password):
            return {"msg": f"Wrong password"}, 400

        access_token, refresh_token = access_refresh_tokens(username)
        return {
            "msg": "Logged in",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "username": username,
        }


class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()["jti"]
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {"msg": "Access token has been revoked"}
        except Exception as e:
            return {"msg": str(e)}, 500


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()["jti"]
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {"msg": "Refresh token has been revoked"}
        except Exception as e:
            return {"msg": str(e)}, 500


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return {"access_token": access_token}


class AllUsers(Resource):
    def get(self):
        return UserModel.get_all()

    def delete(self):
        return UserModel.delete_all()


class SecretResource(Resource):
    @jwt_required
    def get(self):
        return {"answer": 42}


class UnlabeledDataset(Resource):
    def get(self):
        return UnlabeledDatasetModel.get_all()


class StaticContent(Resource):
    def get(self):
        data = parser.parse_args()
        img_name = data["img"]
        file_name = f'static/{img_name}'
        return send_file(file_name, 'image/jpg')


class LabeledDataset(Resource):
    def get(self):
        data = parser.parse_args()
        get_all = data.get("get_all")
        username = data["username"]
        user_id = UserModel.find_by_username(username).id
        return (
            LabeledDatasetModel.get_unlabeled(user_id)
            if not get_all
            else LabeledDatasetModel.get_all()
        )

    def post(self):
        data = parser.parse_args()
        username = data["username"]
        unlabeled_dataset_id = data["unlabeled_dataset_id"]
        user_id = UserModel.find_by_username(username).id
        label = data["label"]
        user = LabeledDatasetModel(
            unlabeled_dataset_id=unlabeled_dataset_id, user_id=user_id, label=label
        )
        user.save()
        return {"msg": "Label added."}

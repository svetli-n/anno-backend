from passlib.hash import pbkdf2_sha256 as sha256
from sqlalchemy.ext.declarative import declarative_base

from run import db

Base = declarative_base()


class LabeledDatasetModel(db.Model):
    __tablename__ = "labeled_dataset"
    __table_args__ = (
        db.UniqueConstraint("unlabeled_dataset_id", "user_id", name="uix_1"),
    )

    id = db.Column(db.Integer, primary_key=True)
    unlabeled_dataset_id = db.Column(db.Integer, db.ForeignKey("unlabeled_dataset.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    label = db.Column(db.Integer)
    user = db.relationship("UserModel", back_populates="evaluations")
    evaluation = db.relationship("UnlabeledDatasetModel", back_populates="users")

    @classmethod
    def get_unlabeled(cls, user_id):
        subquery = (
            cls.query.filter(cls.user_id == user_id)
            .with_entities(cls.unlabeled_dataset_id)
            .distinct(cls.unlabeled_dataset_id)
        )
        dataset = UnlabeledDatasetModel.query.filter(
            ~UnlabeledDatasetModel.id.in_(subquery)
        ).all()
        return {
            "dataset": list(
                map(
                    lambda row: {
                        "id": row.id,
                        "item_1": row.item_1,
                        "item_2": row.item_2,
                    },
                    dataset,
                )
            )
        }

    @classmethod
    def get_all(cls):
        dataset = UnlabeledDatasetModel.query.all()
        return {
            "dataset": list(
                map(
                    lambda row: {
                        "id": row.id,
                        "item_1": row.item_1,
                        "item_2": row.item_2,
                    },
                    dataset,
                )
            )
        }

    def save(self):
        db.session.add(self)
        db.session.commit()


class UnlabeledDatasetModel(db.Model):
    __tablename__ = "unlabeled_dataset"

    id = db.Column(db.Integer, primary_key=True)
    item_1 = db.Column(db.String(120), nullable=False)
    item_2 = db.Column(db.String(120), nullable=False)
    users = db.relationship("LabeledDatasetModel", back_populates="evaluation")

    @classmethod
    def get_all(cls):
        return {
            "dataset": list(
                map(
                    lambda row: {
                        "id": row.id,
                        "item_1": row.item_1,
                        "item_2": row.item_2,
                    },
                    cls.query.all(),
                )
            )
        }


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    evaluations = db.relationship("LabeledDatasetModel", back_populates="user")

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_all(cls):
        return {"users": list(map(lambda u: {"user": u.username}, cls.query.all()))}

    @classmethod
    def delete_all(cls):
        try:
            num_rows = db.session.query(cls).delete()
            db.session.commit()
            return {"msg": f"Deletes {num_rows} users"}
        except Exception as e:
            return {"msg": str(e)}, 500


class RevokedTokenModel(db.Model):
    __tablename__ = "revoked_tokens"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)

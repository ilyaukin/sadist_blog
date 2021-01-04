import datetime
import traceback
import uuid
import os
from libgravatar import Gravatar
from sqlalchemy import exc, and_
from common import db, cache
from common.models import posts_model, comments_model
from common.services.comment_state_enums import States


class CommentService():
    def __init__(self):
        pass

    @classmethod
    def serialize_comments(cls, comments_db_obj, is_admin=False):
        comments_list = list()
        for comment_db_obj in comments_db_obj:
            if is_admin:
                comments_list.append({
                    "author_name": comment_db_obj.author_name,
                    "author_email": comment_db_obj.author_email,
                    "comment_ref_id": comment_db_obj.comment_uuid,
                    "content": comment_db_obj.author_comment,
                    "posted_date": comment_db_obj.posted_date.strftime('%B %d, %Y'),
                    "post_link": "http://" + os.environ.get("FLASK_HOST") + ":" + os.environ.get("FLASK_BLOG_PORT") + "/blog/" + comment_db_obj.posts.title
                })
            else:
                comments_list.append({
                    "author_name": comment_db_obj.author_name,
                    "author_email": comment_db_obj.author_email,
                    "comment_ref_id": comment_db_obj.comment_uuid,
                    "content": comment_db_obj.author_comment,
                    "image_url": Gravatar(comment_db_obj.author_email).get_image(default="robohash"),
                    "posted_date": comment_db_obj.posted_date.strftime('%B %d, %Y'),
                })

        return comments_list

    def add_comment(self, author_name, author_email, author_comment, post_db_obj):
        try:
            comment_db_obj = comments_model.Comments(author_name=author_name,
                                                     author_email=author_email,
                                                     author_comment=author_comment,
                                                     comment_uuid=str(
                                                         uuid.uuid4()).split("-")[0],
                                                     posted_date=datetime.datetime.now(),
                                                     comment_state=States.UNDER_MODERATION.value,
                                                     posts=post_db_obj)
            db.session.add(comment_db_obj)
            db.session.commit()
            return True
        except exc.SQLAlchemyError:
            traceback.print_exc()
            return False

    @classmethod
    def get_comments(cls, post_db_obj=None, is_admin=False):
        if not post_db_obj and is_admin:
            comments = comments_model.Comments.query.filter_by(
                comment_state=States.UNDER_MODERATION.value).all()
        elif post_db_obj and is_admin:
            comments = comments_model.Comments.query.filter_by(posts=post_db_obj).filter_by(
                comment_state=States.UNDER_MODERATION.value).all()
        elif post_db_obj and not is_admin:
            comments = comments_model.Comments.query.filter_by(posts=post_db_obj).filter_by(
                comment_state=States.APPROVED.value).all()

        serialized_comments = cls.serialize_comments(comments, is_admin)
        return serialized_comments

    def get_comment(self):
        pass

    def delete_comment(self):
        pass

    def edit_comment(self, comment_ref_id, comment_status):
        try:
            #If the status is reject delete from db
            comment = comments_model.Comments.query.filter_by(comment_uuid=comment_ref_id)
            if comment_status == States.REJECTED:
                db.session.delete(comment)
                db.session.commit()
                return True
            elif comment_status == States.APPROVED.value:
                # Edit the comment to be accept for posting
                comment.comment_state = States.APPROVED.value
                db.session.add(comment)
                db.session.commit()
                return True
        except exc.SQLAlchemyError:
            traceback.print_exc()
            return False

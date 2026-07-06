from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import uuid
from datetime import datetime, timezone
import bcrypt
from pathlib import Path
from threading import Lock
from sqlalchemy import select, update, insert, delete, func
from database.models import User, Post, PostLike, Auth, UserFollow, PostComment
from database.schemas import UserCreate, UserPublicResponse, PostResponse, PostCreate, PostUpdate, UserUpdate, LoginRequest, TokenResponse, FollowListResponse


def get_user_by_id(db: Session, user_id: str) -> User | None:
    result = db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> User | None:
    result = db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> User | None:
    result = db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def add_user(db: Session, user_data: dict) -> User:
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_public_user(db: Session, username: str) -> dict | None:
    user = get_user_by_username(db, username)
    if user is None:
        return None

    post_count = db.execute(
        select(func.count()).select_from(Post).where(
            Post.user_id == user.id,
            Post.is_deleted == False
        )
    ).scalar()

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "is_private": user.is_private,
        "follower_count": user.followers_count or 0,
        "following_count": user.following_count or 0,
        "post_count": post_count or 0,
    }


def update_user_role(db: Session, user_id: str, new_role: str) -> bool:
    db_user = get_user_by_id(db, user_id)
    if db_user is None:
        return False
    db_user.role = new_role
    db.commit()
    db.refresh(db_user)
    return True


def delete_user(db: Session, user_id: str) -> bool:
    db_user = get_user_by_id(db, user_id)
    if db_user is None:
        return False
    db_user.is_deleted = True
    db.commit()
    db.refresh(db_user)
    return True


def get_user_followers(db: Session, username: str) -> list[UserFollow]:
    user = get_user_by_username(db, username)
    user_id = user.id
    result = db.execute(select(UserFollow).where(UserFollow.following_id == user_id))
    return list(result.scalars().all())


def get_user_following(db: Session, username: str) -> list[UserFollow]:
    user = get_user_by_username(db, username)
    user_id = user.id
    result = db.execute(
        select(UserFollow).where(UserFollow.follower_id == user_id)
    )
    return list(result.scalars().all())



def follow_a_user(db: Session, to_follow_username: str, request_user_id) -> tuple[str, User | None]:

    # 1. Check user exists
    db_user = get_user_by_username(db, to_follow_username)
    if db_user is None:
        return "missing", None
    
    # 2. Cant follow yourself
    if request_user_id == db_user.id:
        return "self-follow", None

    # 3. Check if already followed
    existing_follow = db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == request_user_id,
            UserFollow.following_id == db_user.id,
        )
    )
    
    already_followed = existing_follow.scalar_one_or_none()

    if already_followed:
        return "already-followed", db_user

    # 4. Add the followers row
    new_follow = UserFollow(following_id=db_user.id, follower_id=request_user_id)
    db.add(new_follow)
    # After adding new_follow
    db_user.followers_count = (db_user.followers_count or 0) + 1
    # Also update the follower's following_count
    follower_user = get_user_by_id(db, request_user_id)
    follower_user.following_count = (follower_user.following_count or 0) + 1

    db.commit()
    db.refresh(db_user)
    return "follower", db_user



def unfollow_a_user(db: Session, to_unfollow_user: str, requested_user_id: str) -> tuple[str, User | None]:

    db_user = get_user_by_username(db, to_unfollow_user)
    if db_user is None:
        return "missing", None

    result = db.execute(
        delete(UserFollow).where(
            UserFollow.following_id == db_user.id,
            UserFollow.follower_id == requested_user_id,
        )
    )

    # rowcount 0 means the followers didn't exist
    if result.rowcount == 0:
        return "not-followed", db_user

    db_user.followers_count = max(0, (db_user.followers_count or 0) - 1)
    unfollower = get_user_by_id(db, requested_user_id)
    if unfollower:
        unfollower.following_count = max(0, (unfollower.following_count or 0) - 1)
    db.commit()
    db.refresh(db_user)
    return "unfollowed", db_user
    
    
    



def update_user(db: Session, user_id: str, updates: UserUpdate) -> User | None:
    db_user = get_user_by_id(db, user_id)
    if db_user is None:
        return None
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_all_posts(db: Session, skip: int = 0, limit: int = 20) -> list[dict]:
    result = db.execute(
        select(Post)
        .where(Post.is_deleted == False)
        .order_by(Post.created_at.desc())
        .offset(skip).limit(limit)
    )
    
    return result.scalars().all()




def get_post_by_id(db: Session, post_id: str) -> Post | None:
    return db.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()


def get_user_posts(db: Session, username: str) -> list[Post]:
    result = db.execute(
        select(Post).where(
            Post.username == username,
            Post.is_deleted == False
        )
    )
    return list(result.scalars().all())


def add_post(db: Session, post: PostCreate, user_id: str, username: str) -> Post:
    db_post = Post(
        id=str(uuid.uuid4()),
        user_id=user_id,
        username=username,
        caption=post.caption,
        image_url=str(post.image_url),
        like_count=0,
        comment_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        is_deleted=False,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post



def update_post(db: Session, post_id: str, updates: PostUpdate) -> Post | None:
    db_post = get_post_by_id(db, post_id)

    if db_post is None:
        return None

    # model_dump(exclude_unset=True) only gives fields the caller actually sent
    # so PATCH /posts/123 {"title": "new"} won't wipe out body, published, etc.
    update_data = updates.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_post, field, value)

    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: str) -> bool:
    db_post = get_post_by_id(db, post_id)
    
    if db_post is None:
        return False
    
    db_post.is_deleted = True
    db.commit()
    db.refresh(db_post)
    return True


def like_post(db: Session, post_id: str, user_id: str) -> tuple[str, Post | None]:

    # 1. Check post exists
    db_post = get_post_by_id(db, post_id)
    if db_post is None:
        return "missing", None

    # 2. Check if already liked
    existing_like = db.execute(
        select(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id,
        )
    )
    already_liked = existing_like.scalar_one_or_none()

    if already_liked:
        return "already-liked", db_post

    # 3. Add the like row
    new_like = PostLike(post_id=post_id, user_id=user_id)
    db.add(new_like)

    # 4. Increment like_count on the post
    db_post.like_count += 1

    db.commit()
    db.refresh(db_post)
    return "liked", db_post


def unlike_post(db: Session, post_id: str, user_id: str) -> tuple[str, Post | None]:

    db_post = get_post_by_id(db, post_id)
    if db_post is None:
        return "missing", None

    result = db.execute(
        delete(PostLike).where(
            PostLike.post_id == post_id,
            PostLike.user_id == user_id,
        )
    )

    # rowcount 0 means the like didn't exist
    if result.rowcount == 0:
        return "not-liked", db_post

    db_post.like_count = max(0, db_post.like_count - 1)  # never go below 0

    db.commit()
    db.refresh(db_post)
    return "unliked", db_post


def comment_on_post(db: Session, post_id: str, user_id: str, comment: str) -> tuple[str, Post | None]:

    # 1. Check post exists
    db_post = get_post_by_id(db, post_id)
    if db_post is None:
        return "missing", None

    ## one user can make 'n' no. of comments on a post
    
    # 2. Add the comment row
    new_comment = PostComment(id=str(uuid.uuid4()), post_id=post_id, user_id=user_id, comment=comment)
    db.add(new_comment)

    # 3. Increment comment_count on the post
    db_post.comment_count += 1

    db.commit()
    db.refresh(db_post)
    return "commented", db_post


def delete_comment_on_post(db: Session, comment_id: str) -> bool:
    db_comment = db.execute(
        select(PostComment).where(PostComment.id == comment_id)
    ).scalar_one_or_none()
    
    if db_comment is None:
        return False
    
    db_comment.is_deleted = True
    db.commit()
    db.refresh(db_comment)
    return True

def get_comment_by_id(db: Session, comment_id: str) -> PostComment | None:
    db_comment = db.execute(
        select(PostComment).where(PostComment.id == comment_id)
    )
    
    return db_comment.scalar_one_or_none()


def _auth_record_to_dict(record: Auth | None) -> dict | None:
    if record is None:
        return None
    return {
        "id": record.id,
        "user_id": record.user_id,
        "token": record.token,
        "is_revoked": record.is_revoked,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
    }


def get_refresh_token(db: Session, token: str):
    result = db.execute(select(Auth).where(Auth.token == token))
    return _auth_record_to_dict(result.scalar_one_or_none())


def save_refresh_token(db: Session, token_data: dict):
    record = Auth(**token_data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return _auth_record_to_dict(record)


def revoke_refresh_token(db: Session, token: str):
    result = db.execute(select(Auth).where(Auth.token == token))
    record = result.scalar_one_or_none()
    if record is None:
        return None

    record.is_revoked = True
    db.commit()
    db.refresh(record)
    return _auth_record_to_dict(record)


def delete_all_user_tokens(db: Session, user_id: str) -> int:
    result = db.execute(delete(Auth).where(Auth.user_id == user_id))
    db.commit()
    return int(result.rowcount or 0)

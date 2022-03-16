from django import template
from ..models import FriendRequests


register = template.Library()


@register.simple_tag
def is_liked(post, user):
    if post.likes.filter(id=user.id).exists():
        return True
    return False


@register.simple_tag
def is_disliked(post, user):
    if post.dislikes.filter(id=user.id).exists():
        return True
    return False


@register.simple_tag
def is_friend(user, friend):
    if user.friends.filter(id=friend.profile.id).exists():
        return True
    return False


@register.simple_tag
def is_friend_request(sender, receiver):
    if FriendRequests.objects.filter(sender_user=sender, receiver_user=receiver).exists():
        return True
    return False

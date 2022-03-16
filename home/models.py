from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
import uuid


def get_pp_path(instance, filename):
    return f'user_{instance.user.username}_{instance.user.id}/pp/{filename}'


def get_cp_path(instance, filename):
    return f'user_{instance.user.username}_{instance.user.id}/cp/{filename}'


def get_post_path(instance, filename):
    return f'user_{instance.user.username}/{instance.id}/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # photos
    profile_pic = models.ImageField(upload_to=get_pp_path, blank=True)
    cover_pic = models.ImageField(upload_to=get_cp_path, blank=True)
    # basic info
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    gender = models.CharField(choices=GENDER_CHOICES, default='Male', max_length=10)
    birth_date = models.DateField(null=True, blank=True)
    family = models.CharField(max_length=100, blank=True)
    current_city = models.CharField(max_length=30, blank=True)
    hometown = models.CharField(max_length=30, blank=True)
    # contact info
    phone_number = models.CharField(max_length=30, blank=True)
    website = models.URLField(max_length=200, blank=True)
    address = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=30, blank=True)
    # bio
    bio = models.TextField(blank=True, max_length=500)
    # education
    university = models.CharField(max_length=30, blank=True)
    major = models.CharField(max_length=30, blank=True)
    gpa = models.FloatField(blank=True, null=True)
    # work
    company = models.CharField(max_length=30, blank=True)
    position = models.CharField(max_length=30, blank=True)
    duration_start = models.DateField(null=True, blank=True)
    duration_end = models.DateField(null=True, blank=True)
    duration_current = models.BooleanField(default=False)
    # friends
    friends = models.ManyToManyField('Profile', blank=True, symmetrical=True)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('profile', kwargs={'pk': self.pk})

    def get_full_name(self):
        return User.objects.get(pk=self.user.pk).get_full_name()

    def get_friends(self):
        return self.friends.all()

    def remove_friend(self, friend):
        self.friends.remove(friend)

    def get_friends_count(self):
        return self.friends.count()

    def get_friends_request_count(self):
        return FriendRequests.objects.filter(receiver_user=self.user).count()

    def get_friends_list(self):
        return self.friends.all().values_list('username', flat=True)

    def get_post_count(self):
        return Post.objects.filter(user=self.user).count()

    def get_newsfeed(self):
        # combine user's posts and friends' posts into one queryset
        user_posts = Post.objects.filter(user=self.user)
        friends_posts = Post.objects.filter(user__profile__in=self.friends.all())
        result = user_posts | friends_posts
        return result.order_by('-created_at')

    def get_public_post_count(self):
        return Post.objects.filter(user=self.user, visibility__iexact='public').count()

    def send_friend_request(self, receiver):
        FriendRequests.objects.create(sender_user=self.user, receiver_user=receiver)

    def revoke_friend_request(self, receiver):
        FriendRequests.objects.filter(sender_user=self.user, receiver_user=receiver).delete()

    def accept_friend_request(self, sender):
        FriendRequests.objects.filter(sender_user=sender, receiver_user=self.user).delete()
        self.friends.add(sender.profile)


class FriendRequests(models.Model):
    sender_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='request_sender')
    receiver_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                      related_name='request_receiver')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender_user.username} sent a friend request to {self.receiver_user.username}'

    def accept(self):
        self.sender_user.profile.friends.add(self.receiver_user.profile)
        self.receiver_user.profile.friends.add(self.sender_user.profile)
        self.delete()

    def reject(self):
        self.delete()


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, unique=True)
    post_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    content = models.TextField()
    attachment = models.FileField(upload_to=get_post_path, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='likes', blank=True)
    dislikes = models.ManyToManyField(User, related_name='dislikes', blank=True)
    VIEWS_CHOICES = [('public', 'Public'), ('friends', 'Friends')]
    visibility = models.CharField(max_length=10, default='public', choices=VIEWS_CHOICES)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        self.post_id = uuid.uuid4()
        self.slug = slugify(self.user.username + '-' + str(self.post_id))
        super().save(*args, **kwargs)

    def get_comments(self):
        return self.comment_set.all()

    def get_comment_count(self):
        return self.comment_set.count()

    def get_like_count(self):
        return self.likes.count()

    def get_dislike_count(self):
        return self.dislikes.count()


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content

    def get_absolute_url(self):
        return reverse('comment', kwargs={'pk': self.post.pk})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.user.username + '-' + str(uuid.uuid4()))
        super().save(*args, **kwargs)


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='receiver', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.sender.username} sent message to {self.receiver.username}'

    def get_absolute_url(self):
        return reverse('messages', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class MessageContent(models.Model):
    FROM_CHOICES = [('sender', 'Sender'), ('receiver', 'Receiver')]
    from_user = models.CharField(max_length=10, choices=FROM_CHOICES, default='sender')
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content

    def get_absolute_url(self):
        return reverse('messages', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

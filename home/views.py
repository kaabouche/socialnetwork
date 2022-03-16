import random

from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views import View, generic
from django.http import JsonResponse

from .forms import *
from .models import Post, Profile, FriendRequests, Message, MessageContent


# Helper functions
def new_post_function(request):
    post_form = PostForm(request.POST)
    if post_form.is_valid():
        post = Post(user=request.user, content=post_form.cleaned_data['content'],
                    visibility=post_form.cleaned_data['visibility'],
                    attachment=post_form.cleaned_data['attachment'])
        post.save()
        messages.success(request, 'Post created successfully!')
        return redirect('post_detail', post_id=post.id)
    else:
        messages.error(request, 'Something went wrong!')
        return redirect('userprofile', request.user.username)


def new_profile_function(user, form):
    new_profile = Profile(user=user)
    new_profile.birth_date = form.cleaned_data.get('birth_date')
    random_cover = random.randint(1, 8)
    fs = FileSystemStorage()
    fs.save(f'user_{user.username}_{user.id}/cp/cover{random_cover}.svg',
            open('static/img/covers/cover' + str(random_cover) + '.svg', 'rb'))
    new_profile.cover_pic = f'user_{user.username}_{user.id}/cp/cover{random_cover}.svg'
    random_pp = random.randint(1, 8)
    fs.save(f'user_{user.username}_{user.id}/pp/avatar{random_pp}.png',
            open('static/img/avatar/avatar' + str(random_pp) + '.png', 'rb'))
    new_profile.profile_pic = f'user_{user.username}_{user.id}/pp/avatar{random_pp}.png'
    new_profile.save()


def post_delete_function(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user == request.user:
        post.delete()
        messages.success(request, 'Post deleted successfully!')
    else:
        messages.error(request, 'You are not authorized to delete this post!')


def post_like_dislike_function(request, post_id, action):
    post = get_object_or_404(Post, id=post_id)
    like_class = 'text-muted'
    dislike_class = 'text-muted'
    if action == 'like':
        if post.dislikes.filter(id=request.user.id).exists():
            post.dislikes.remove(request.user)
            dislike_class = 'text-muted'
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            like_class = 'text-muted'
        else:
            post.likes.add(request.user)
            like_class = 'text-primary'
    elif action == 'dislike':
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            like_class = 'text-muted'
        if post.dislikes.filter(id=request.user.id).exists():
            post.dislikes.remove(request.user)
            dislike_class = 'text-muted'
        else:
            post.dislikes.add(request.user)
            dislike_class = 'text-primary'
    data = {
        'likes': post.likes.count(),
        'dislikes': post.dislikes.count(),
        'like_class': like_class,
        'dislike_class': dislike_class
    }
    return JsonResponse(data)
######


class HomeView(View):
    @staticmethod
    def get(request):
        if request.user.is_authenticated:
            context = {
                'active': 'home',
                'search_form': SearchForm(),
                'post_form': PostForm(),
            }
            return render(request, 'home/index.html', context)
        else:
            context = {
                'login_form': LoginForm(),
                'signup_form': SignUpForm(),
            }
            return render(request, 'landing/index.html', context)

    @staticmethod
    def post(request):
        if 'login' in request.POST:
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                email = login_form.cleaned_data['email']
                password = login_form.cleaned_data['password']
                user = authenticate(username=email, password=password)
                if user is not None:
                    login(request, user)
                    context = {
                        'active': 'home',
                        'search_form': SearchForm(),
                        'post_form': PostForm()
                    }
                    return render(request, 'home/index.html', context)
                else:
                    context = {
                        'login_form': LoginForm(),
                        'signup_form': SignUpForm(),
                    }
                    return render(request, 'landing/index.html', context)
            else:
                return render(request, 'landing/index.html', {'login_form': login_form})
        elif 'new_post' in request.POST:
            return new_post_function(request)
        elif 'signup' in request.POST:
            signup_form = SignUpForm(request.POST)
            if signup_form.is_valid():
                # check if email is taken
                if User.objects.filter(email=signup_form.cleaned_data['email']).exists():
                    messages.error(request, 'Email already exists')
                    return render(request, 'landing/index.html', {'signup_form': signup_form})
                # check if username is taken
                if User.objects.filter(username=signup_form.cleaned_data['username']).exists():
                    messages.error(request, 'Username already exists')
                    return render(request, 'landing/index.html', {'signup_form': signup_form})
                # check if age is valid
                if signup_form.cleaned_data['birth_date'].year > datetime.now().year - 18:
                    messages.error(request, 'You must be at least 18 years old')
                    return render(request, 'landing/index.html', {'signup_form': signup_form})
                # create user
                user = User.objects.create_user(username=signup_form.cleaned_data['username'],
                                                email=signup_form.cleaned_data['email'],
                                                password=signup_form.cleaned_data['password'])
                user.first_name = signup_form.cleaned_data['first_name']
                user.last_name = signup_form.cleaned_data['last_name']
                user.save()
                # create profile
                new_profile_function(user, signup_form)
                # login user
                login(request, user)
                context = {
                    'active': 'home',
                    'search_form': SearchForm(),
                    'post_form': PostForm()
                }
                return render(request, 'home/index.html', context)
        elif 'post_delete_id' in request.POST:
            return post_delete_function(request, request.POST['post_delete_id'])
        elif 'post_like_dislike_id' in request.POST:
            return post_like_dislike_function(request, request.POST['post_like_dislike_id'], request.POST['action'])


class LoginView(auth_views.LoginView):
    template_name = 'landing/login.html'
    form_class = LoginForm
    extra_context = {'active': 'home'}
    redirect_authenticated_user = True

    def get_success_url(self):
        if 'next' in self.request.POST:
            return self.request.POST['next']
        else:
            return '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_form'] = LoginForm()
        return context


def logout_view(request):
    logout(request)
    return redirect('/')


class ProfileView(View):
    @staticmethod
    def get(request, user_name=None):
        if request.user.is_authenticated:
            if user_name is None:
                return redirect('userprofile', request.user.username)
            nav_active = 'profile'
            search_form = SearchForm()
            cover_form = ProfileCoverChangeForm()
            photo_form = ProfilePhotoChangeForm()
            post_form = PostForm()
            user = get_object_or_404(request.user.__class__, username=user_name)
            if user != request.user:
                nav_active = ''
            posts = user.post_set.all().order_by('-created_at')
            return render(request, 'profile/profile.html',
                          {'active': nav_active, 'search_form': search_form, 'user': user, 'cover_form': cover_form,
                           'photo_form': photo_form, 'post_form': post_form, 'posts': posts})
        else:
            return HttpResponseRedirect('/login/?next=/profile/')

    @staticmethod
    def post(request):
        if 'cover' in request.FILES:
            cover_form = ProfileCoverChangeForm(request.POST, request.FILES)
            if cover_form.is_valid():
                user = request.user
                user.profile.cover_pic = cover_form.cleaned_data['cover']
                user.profile.save()
                messages.success(request, 'Cover updated successfully')
                return HttpResponseRedirect('/profile/')
            else:
                messages.error(request, 'Something went wrong')
                return redirect('userprofile', request.user.username)
        elif 'photo' in request.FILES:
            photo_form = ProfilePhotoChangeForm(request.POST, request.FILES)
            if photo_form.is_valid():
                user = request.user
                user.profile.profile_pic = photo_form.cleaned_data['photo']
                user.profile.save()
                messages.success(request, 'Profile photo updated successfully')
                return HttpResponseRedirect('/profile/')
            else:
                messages.error(request, 'Something went wrong')
                return redirect('userprofile', request.user.username)
        elif 'new_post' in request.POST:
            return new_post_function(request)
        elif 'post_delete_id' in request.POST:
            return post_delete_function(request, request.POST['post_delete_id'])
        elif 'post_like_dislike_id' in request.POST:
            return post_like_dislike_function(request, request.POST['post_like_dislike_id'], request.POST['action'])

    def get_success_url(self):
        return reverse_lazy('userprofile', kwargs={'user_name': self.request.user.username})


class ProfileEditView(View):
    @staticmethod
    def get(request, user_name=None):
        if request.user.is_authenticated and (request.user == User.objects.get(username=user_name)):
            context = {
                'active': 'profile',
                'search_form': SearchForm(),
                'user_form': UserEditForm(instance=request.user),
                'profile_form': ProfileEditForm(instance=request.user.profile),
            }
            return render(request, 'profile/edit.html', context)
        else:
            return redirect('/')

    @staticmethod
    def post(request, user_name=None):
        if request.user.is_authenticated and (request.user == User.objects.get(username=user_name)):
            user_form = UserEditForm(request.POST, instance=request.user)
            profile_form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully')
                return HttpResponseRedirect('/profile/')
            else:
                messages.error(request, 'Something went wrong')
                return redirect('userprofile', request.user.username)
        return redirect('userprofile', request.user.username)


class SearchView(View):
    @staticmethod
    def get(request):
        if request.user.is_authenticated:
            search_form = SearchForm()
            search_query = request.GET.get('q')
            search_form.fields['q'].initial = search_query
            friend_requests = FriendRequests.objects.filter(receiver_user=request.user)
            friend_requests_usernames = [friend_request.sender_user.username for friend_request in friend_requests]
            if search_query is not None:
                results = User.objects.filter(Q(username__icontains=search_query) |
                                              Q(first_name__icontains=search_query) |
                                              Q(last_name__icontains=search_query))
                return render(request, 'home/search.html',
                              {'active': 'search', 'search_form': search_form, 'results': results,
                               'friend_requests_usernames': friend_requests_usernames})

            return render(request, 'home/search.html', {'search_form': search_form})
        else:
            return HttpResponseRedirect('/login/?next=/search/')

    @staticmethod
    def post(request):
        if 'search' in request.POST:
            return HttpResponse('search')
        elif 'remove_friend' in request.POST['action']:
            remove_user = User.objects.get(username=request.POST['username'])
            request.user.profile.remove_friend(remove_user.profile)
            data = {'status': 'success'}
            return JsonResponse(data)
        elif 'add_friend' in request.POST['action']:
            add_user = User.objects.get(username=request.POST['username'])
            request.user.profile.send_friend_request(add_user)
            data = {'status': 'success'}
            return JsonResponse(data)
        elif 'revoke_request' in request.POST['action']:
            revoke_user = User.objects.get(username=request.POST['username'])
            request.user.profile.revoke_friend_request(revoke_user)
            data = {'status': 'success'}
            return JsonResponse(data)
        elif 'accept_request' in request.POST['action']:
            FriendRequests.objects.get(receiver_user=request.user,
                                       sender_user=User.objects.get(username=request.POST['username'])).accept()
            data = {'status': 'success'}
            return JsonResponse(data)


class SignUpView(UserPassesTestMixin, generic.CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'landing/register.html'
    password_validation = True
    permission_denied_message = 'You are already registered'

    def form_valid(self, form):
        is_error = False
        # check if email is already registered
        if form.cleaned_data['email'] in [user.email for user in User.objects.all()]:
            form.add_error('email', 'Email already registered')
            is_error = True
        # check if username is already registered
        if form.cleaned_data['username'] in [user.username for user in User.objects.all()]:
            form.add_error('username', 'Username already registered')
            is_error = True
        # check if age is valid
        b_day = form.cleaned_data['birth_date']
        if b_day.year > datetime.now().year - 18:
            form.add_error('birth_date', 'You must be at least 18 years old')
            is_error = True
        if is_error:
            return super().form_invalid(form)
        user = form.save()
        new_profile_function(user, form)
        login(self.request, user)
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_authenticated:
            return False
        return True

    def handle_no_permission(self):
        return redirect('index')


class PostView(View):
    @staticmethod
    def get(request, post_id):
        if request.user.is_authenticated:
            context = {
                'search_form': SearchForm(),
                'comment_form': CommentForm(),
                'post': Post.objects.get(id=post_id),
            }
            return render(request, 'post/post_detail.html', context)
        else:
            return HttpResponseRedirect('/login/?next=/post/' + str(post_id))

    @staticmethod
    def post(request, post_id):
        if 'new_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.post = Post.objects.get(id=post_id)
                comment.save()
                messages.success(request, 'Comment added successfully.')
                return HttpResponseRedirect('/post/' + str(post_id))
            else:
                messages.error(request, 'Something went wrong.')
                return HttpResponseRedirect('/post/' + str(post_id))


class PostEditView(UserPassesTestMixin, generic.UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post/post_edit.html'
    success_url = reverse_lazy('index')
    permission_denied_message = 'You are not the author of this post'
    extra_context = {'search_form': SearchForm()}

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.id == self.get_object().user.id:
                return True
            return False
        return False

    def handle_no_permission(self):
        return redirect('index')

    def get_success_url(self):
        return reverse('post_detail', args=[self.object.id])

    def form_valid(self, form):
        messages.success(self.request, 'Post edited successfully.')
        return super().form_valid(form)


class FriendListView(View):
    @staticmethod
    def get(request):
        if request.user.is_authenticated:
            context = {
                'active': 'friends',
                'search_form': SearchForm(),
                'friends': request.user.profile.friends.all(),
                'friend_requests': FriendRequests.objects.filter(receiver_user=request.user),
            }
            return render(request, 'friends.html', context)
        else:
            return HttpResponseRedirect('/login/?next=/friends/')

    @staticmethod
    def post(request):
        if request.POST['action'] == 'accept':
            friend_request = FriendRequests.objects.get(id=request.POST['friend_request_id'])
            friend_request.accept()
            data = {
                'status': 'accepted',
            }
            return JsonResponse(data)
        elif request.POST['action'] == 'reject':
            friend_request = FriendRequests.objects.get(id=request.POST['friend_request_id'])
            friend_request.reject()
            data = {
                'status': 'rejected',
            }
            return JsonResponse(data)
        elif request.POST['action'] == 'unfriend':
            remove_user = User.objects.get(username=request.POST['username'])
            request.user.profile.remove_friend(remove_user.profile)
            data = {
                'status': 'unfriended',
            }
            return JsonResponse(data)


class MessageListView(UserPassesTestMixin, generic.ListView):
    model = Message
    template_name = 'message/message.html'
    paginate_by = 10
    extra_context = {
        'active': 'messages',
        'search_form': SearchForm()
    }

    def test_func(self):
        if self.request.user.is_authenticated:
            return True
        return False

    def handle_no_permission(self):
        return redirect('index')

    def get_queryset(self):
        return Message.objects.filter(Q(sender=self.request.user) | Q(receiver=self.request.user)).order_by(
            '-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active'] = 'messages'
        return context

    def post(self, request):
        if request.POST['action'] == 'mark_read':
            message = Message.objects.get(id=request.POST['message_id'])
            all_messages = MessageContent.objects.filter(message=message)
            for message in all_messages:
                message.is_read = True
                message.save()
            data = {
                'status': 'success',
            }
            return JsonResponse(data)
        elif request.POST['action'] == 'delete_message':
            message = Message.objects.get(id=request.POST['message_id']).delete()
            data = {
                'status': 'success',
            }
            return JsonResponse(data)


class MessageDetailView(UserPassesTestMixin, generic.DetailView):
    model = Message
    template_name = 'message/message_detail.html'
    extra_context = {
        'active': 'messages',
        'search_form': SearchForm(),
        'message_form': NewMessageForm(),
    }

    def test_func(self):
        if self.request.user.is_authenticated:
            return True
        return False

    def handle_no_permission(self):
        return redirect('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active'] = 'messages'
        return context

    def get(self, request, *args, **kwargs):
        message = self.get_object()
        last_message = MessageContent.objects.filter(message=message).order_by('-updated_at').first()
        if last_message == None:
            return super().get(request, *args, **kwargs)
        if last_message.is_read is False:
            if last_message.from_user == 'receiver':
                if message.sender == request.user:
                    last_message.is_read = True
            else:
                if message.receiver == request.user:
                    last_message.is_read = True
        last_message.save()
        return super().get(request, *args, **kwargs)

    def post(self, request, pk):
        if 'send_message' in request.POST:
            message = Message.objects.get(id=pk)
            from_user = ''
            if message.receiver == request.user:
                from_user = 'receiver'
            else:
                from_user = 'sender'
            new_message = MessageContent.objects.create(message=message, from_user=from_user,
                                                        content=request.POST['content'])
            new_message.save()
            return HttpResponseRedirect(reverse('message_detail', kwargs={'pk': pk}))
        elif request.POST['action'] == 'delete_message':
            Message.objects.get(id=request.POST['message_id']).delete()
            data = {
                'status': 'success',
            }
            return JsonResponse(data)


class NewMessageView(View):
    def get(self, request):
        if request.user.is_authenticated and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            data = {}
            user = User.objects.get(username=request.GET['new_message_username'])
            message = Message.objects.filter(
                Q(sender=user, receiver=request.user) | Q(receiver=user, sender=request.user))
            if message.exists():
                data['redirect_url'] = reverse('message_detail', kwargs={'pk': message.first().id})
                data['status'] = 'success'
            else:
                # Create new message
                new_message = Message.objects.create(sender=request.user, receiver=user)
                new_message.save()
                data['redirect_url'] = reverse('message_detail', kwargs={'pk': new_message.id})
                data['status'] = 'success'
            return JsonResponse(data)
        return HttpResponseRedirect(reverse('index'))

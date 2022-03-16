from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('', views.HomeView.as_view(), name='forgot'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('search', views.SearchView.as_view(), name='search'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/<str:user_name>', views.ProfileView.as_view(), name='userprofile'),
    path('profile/<str:user_name>/edit', views.ProfileEditView.as_view(), name='edit_profile'),
    path('logout/', views.logout_view, name='logout'),
    path('post/<int:post_id>/', views.PostView.as_view(), name='post_detail'),
    path('post/<int:pk>/edit/', views.PostEditView.as_view(), name='post_edit'),
    path('friends/', views.FriendListView.as_view(), name='friends'),
    path('messages/', views.MessageListView.as_view(), name='messages'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('newmessage/', views.NewMessageView.as_view(), name='new_message'),
]

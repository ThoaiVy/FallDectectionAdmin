from django.urls import path
import server.views as views

app_name = 'server'
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('request/', views.get_requests, name='request'),
    path('cancelRequest/', views.cancelRequest, name='cancel-request'),
    path('confirmRequest/', views.confirmRequest, name='confirm-request'),
]
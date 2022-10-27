from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('logout/', views.user_logout, name='user_logout'),
    path('login/', views.user_login, name='user_login'),
    path('signup/', views.user_signup, name='user_signup'),
    path('categories/',views.view_catigories, name='view_categories'),
    path('category/',views.new_category, name='new_category'),
    path('del_ctg/<int:ctg_id>', views.delete_category, name='delete_category'),
    path('edit_ctg/<int:ctg_id>', views.edit_category, name='edit_category'),
    path('transaction/<int:type_trans>', views.new_transaction, name='new_transaction'),
    path('edit_trans/<int:trans_id>', views.edit_transaction, name='edit_transaction'),
    path('del_trans/<int:trans_id>', views.del_transaction, name='del_transaction'),
    path('period_search/', views.period_search, name='period_search'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('update_sheet_1/', views.fetch_and_update_spreadsheet_1, name='update_spreadsheet_1'),
    path('update_sheet_2/', views.fetch_and_update_spreadsheet_2, name='update_spreadsheet_2'),
]

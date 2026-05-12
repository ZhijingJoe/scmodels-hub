from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload, name='analysis_upload'),
    path('result/<uuid:job_id>/', views.result, name='analysis_result'),
]

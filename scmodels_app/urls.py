from django.urls import path
from . import views
from .upload import upload_image

urlpatterns = [
    # Portal homepage
    path('', views.index, name='index'),

    # scModel section
    path('scmodels/', views.scmodel_list, name='scmodel_list'),
    path('scmodels/<slug:slug>/', views.scmodel_detail, name='scmodel_detail'),

    # Resource categories (catch-all: /resources/<slug>/)
    path('resources/<slug:slug>/', views.resource_category, name='resource_category'),

    # Image upload for Markdown editor
    path('api/upload-image/', upload_image, name='upload_image'),
]

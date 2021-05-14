from django.urls import path

from . import views


urlpatterns = [
    path('', views.new_template, name='new_template'),
    path('preview/<str:template_id>/<str:preview_id>/',
        views.preview_template, name='preview_template'),
    path('refresh/<str:template_id>/<str:preview_id>/',
        views.refresh_target, name='refresh_target'),
]

from django.urls import path, include
from . import views
from .views import DogCreateAPI
from .views import DogBulkCreateView
from .views import DogListAPIView

from django.contrib.auth import views as auth_views

from .views import register

from django.urls import path
from .views import (
    FosterHomeListView,
    FosterHomeDetailView,
    FosterHomeCreateView,
    FosterHomeUpdateView,
    FosterHomeDeleteView,
)

from django.conf import settings
from django.conf.urls.static import static
from .views import DogReadOnlyView

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dogs/', views.DogListView.as_view(), name='dog_list'),
    path('dogs/add/', views.DogCreateView.as_view(), name='dog_add'),
    path('dogs/edit/<int:pk>/', views.DogUpdateView.as_view(), name='dog_edit'),
    path('dogs/view/<int:pk>/', views.DogReadOnlyView.as_view(), name='dog_readonly'),
    path('dogs/delete/<int:pk>/', views.DogDeleteView.as_view(), name='dog_delete'),
    path('adopters/', views.AdopterListView.as_view(), name='adopter_list'),
    path('adopters/add/', views.AdopterCreateView.as_view(), name='adopter_add'),
    path('adopters/edit/<int:pk>/', views.AdopterUpdateView.as_view(), name='adopter_edit'),
    path('adopters/delete/<int:pk>/', views.AdopterDeleteView.as_view(), name='adopter_delete'),
    path('adoptions/', views.AdoptionListView.as_view(), name='adoption_list'),
    path('adoptions/add/', views.AdoptionCreateView.as_view(), name='adoption_add'),
    path('adoptions/edit/<int:pk>/', views.AdoptionUpdateView.as_view(), name='adoption_edit'),
    path('adoptions/delete/<int:pk>/', views.AdoptionDeleteView.as_view(), name='adoption_delete'),
    #path('login/', auth_views.LoginView.as_view(), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),  
    path('register/', register, name='register'),
]

urlpatterns += [
    path('api/dogs/add/', DogCreateAPI.as_view(), name='dog_api_add'),
    path('api/dogs/bulk/', DogBulkCreateView.as_view(), name='dog-bulk-create'),
    path('api/dogs/bulk-upsert/', views.bulk_upsert_dogs, name='bulk-upsert-dogs'),
    path('api/dogs/full-snapshot/', views.full_snapshot_dogs, name='full_snapshot_dogs'),
    path('api/dogs/', DogListAPIView.as_view(), name='dog-list'),
]

from django.urls import path
from . import views

urlpatterns += [
    path('dogs/<int:dog_id>/medical-records/', views.medical_record_list, name='medical_record_list'),
    path('dogs/<int:dog_id>/medical-records/new/', views.medical_record_create, name='medical_record_create'),
    path('dogs/<int:dog_id>/medical-records/<int:record_id>/edit/', views.medical_record_edit, name='medical_record_edit'),
]


urlpatterns += [
    path('fosterhomes/', FosterHomeListView.as_view(), name='fosterhome_list'),
    path('fosterhomes/create/', FosterHomeCreateView.as_view(), name='fosterhome_create'),
    path('fosterhomes/<int:pk>/', FosterHomeDetailView.as_view(), name='fosterhome_detail'),
    path('fosterhomes/<int:pk>/update/', FosterHomeUpdateView.as_view(), name='fosterhome_update'),
    path('fosterhomes/<int:pk>/delete/', FosterHomeDeleteView.as_view(), name='fosterhome_delete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from django.urls import path
from . import views

urlpatterns += [
    # DogWalker URLs
    path('walkers/', views.DogWalkerListView.as_view(), name='dogwalker_list'),
    path('walkers/add/', views.DogWalkerCreateView.as_view(), name='dogwalker_add'),
    path('walkers/<int:pk>/edit/', views.DogWalkerUpdateView.as_view(), name='dogwalker_edit'),
    path('walkers/<int:pk>/delete/', views.DogWalkerDeleteView.as_view(), name='dogwalker_delete'),

    # DogWalk URLs
    path('walks/', views.DogWalkListView.as_view(), name='dogwalk_list'),
    path('walks/add/', views.DogWalkCreateView.as_view(), name='dogwalk_add'),
    path('walks/<int:pk>/edit/', views.DogWalkUpdateView.as_view(), name='dogwalk_edit'),
    path('walks/<int:pk>/delete/', views.DogWalkDeleteView.as_view(), name='dogwalk_delete'),
]

from django.urls import path
from . import views

urlpatterns += [
    path('foster-assignments/add/', views.dog_foster_assignment_create, name='dog_foster_assignment_add'),
    path('foster-assignments/<int:pk>/edit/', views.dog_foster_assignment_update, name='dog_foster_assignment_edit'),
    path('foster-assignments/<int:pk>/delete/', views.dog_foster_assignment_delete, name='dog_foster_assignment_delete'),
    path('foster-assignments/', views.dog_foster_assignment_list, name='dog_foster_assignment_list'),
    path("dog-search/", views.dog_search, name="dog_search"),

]

# urls.py
from django.urls import path
from . import views

urlpatterns += [
    # existing patterns...
    path('dog-image/<int:image_id>/delete/', views.delete_dog_image, name='delete_dog_image'),
]

from django.urls import path
#from .views import dog_report

#urlpatterns += [
#    path("reports/dogs/", dog_report, name="dog_report"),
#]

from django.urls import path
from . import views

urlpatterns += [
    path("reports/dogs/", views.dog_report, name="dog_report"),
]


#from django.urls import path
from .views import public_dog_list

urlpatterns += [
    path("adopt/", public_dog_list, name="public_dog_list"),
]

# reports/urls.py
from django.urls import path
from . import views

urlpatterns += [
    path("dog-reports/movements", views.dog_movement_reports, name="dog_reports"),
]

urlpatterns += [
    path('dog-reports/walk_priority/', views.walk_priority_report, name='walk_priority_report'),
]




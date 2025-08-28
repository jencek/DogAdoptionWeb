# reports.py (or in views.py if you prefer)
import django_filters
import django_tables2 as tables
from django import forms
from django.db.models import Sum, Count
from .models import Dog, DogWalk


# Filter dogs by status, age range, etc.
# class DogReportFilter(django_filters.FilterSet):
#     #min_age = django_filters.NumberFilter(field_name="age", lookup_expr="gte")
#     #max_age = django_filters.NumberFilter(field_name="age", lookup_expr="lte")
#     status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
#     name = django_filters.CharFilter(
#         field_name="name",
#         lookup_expr="icontains",
#         label="Dog Name"
#     )

#      # Walk date range (start + end)
#     walk_date_after = django_filters.DateFilter(
#         field_name='dogwalk__walk_date',
#         lookup_expr='gte',
#         label='Walked After',
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#     )
#     walk_date_before = django_filters.DateFilter(
#         field_name='dogwalk__walk_date',
#         lookup_expr='lte',
#         label='Walked Before',
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#     )

#     class Meta:
#         model = Dog
#         fields = ["status",  "walk_date_after", 'walk_date_before']

# # Table for reporting
# class DogReportTable(tables.Table):
#     walk_count = tables.Column(verbose_name="Number of Walks")
#     walk_minutes = tables.Column(verbose_name="Total Walk Minutes")
#     walk_avg_minutes = tables.Column(verbose_name="Avg Walk Minutes") 
#     walk_avg_minutes_per_week = tables.Column(verbose_name="AVerage Minutes Walked per Week")
#     class Meta:
#         model = Dog
#         template_name = "django_tables2/bootstrap.html"
#         fields = ("name", "age", "status")  # Dog fields to display






import django_filters
from django import forms
import django_tables2 as tables
from .models import Dog

import django_filters
from django import forms
from .models import Dog

import django_filters
from django import forms
from .models import Dog

class DogReportFilter(django_filters.FilterSet):
    # Status
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    
    # Dog multi-select
    dogs = django_filters.ModelMultipleChoiceFilter(
        queryset=Dog.objects.all(),
        field_name="id",   # 🔑 filter on the dog ID
        to_field_name="id",
        widget=forms.SelectMultiple(attrs={"class": "form-control", "id": "dogs"})
    )

    # Walk date range (start + end)
    walk_date_after = django_filters.DateFilter(
        field_name="dogwalk__walk_date",
        lookup_expr="gte",
        label="Walked After",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    walk_date_before = django_filters.DateFilter(
        field_name="dogwalk__walk_date",
        lookup_expr="lte",
        label="Walked Before",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    class Meta:
        model = Dog
        fields = ["status", "dogs", "walk_date_after", "walk_date_before"]

class DogReportTable(tables.Table):
    walk_count = tables.Column(verbose_name="Walks")
    walk_minutes = tables.Column(verbose_name="Total Minutes")
    min_per_walk_avg = tables.Column(verbose_name="Avg Minutes / Walk")
    min_per_week_avg = tables.Column(verbose_name="Avg Minutes / Week")


    class Meta:
        model = Dog
        template_name = "django_tables2/bootstrap4.html"
        fields = ("name", "status", "age")
        sequence = ("name", "status", "age", "walk_count", "walk_minutes", "min_per_walk_avg", "min_per_week_avg")






from django.shortcuts import render
from django.views.generic import UpdateView, DeleteView

# Create your views here.
from django.views.generic import TemplateView, ListView, CreateView
from django.urls import reverse_lazy
from .models import Dog, Adopter, Adoption, DogURL


from django.urls import reverse_lazy
from django.views.generic import  UpdateView, DeleteView
from .models import FosterHome

from django.views.generic import  DetailView, UpdateView, DeleteView



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DogCreateSerializer


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Dog
from .models import DogURL
from django.db.models import Q

import datetime
from django.utils import timezone

from .forms import DogUpdateForm, DogReadonlyForm
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin

#class DashboardView(LoginRequiredMixin, TemplateView):
#    template_name = 'dashboard.html'


from datetime import timedelta

# views.py
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib import messages

from django.http import HttpResponseRedirect

from rest_framework import generics
from .serializers import DogSerializer

from django.db.models.functions import Lower


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})




class DogCreateAPI(APIView):
    def post(self, request, format=None):
        serializer = DogCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Dog created successfully', 'dog': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class DogBulkCreateView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Expected a list of objects"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DogCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)








@api_view(['POST'])
def bulk_upsert_dogs(request):
    if not isinstance(request.data, list):
        return Response({'error': 'Expected a list of dog objects.'}, status=status.HTTP_400_BAD_REQUEST)

    results = []
    errors = []

    for idx, dog_data in enumerate(request.data):
        nameext = dog_data.get('nameext')

        if not nameext:
            errors.append({'index': idx, 'error': 'Missing nameext'})
            continue

        try:
            dog = Dog.objects.get(nameext=nameext)
            serializer = DogCreateSerializer(dog, data=dog_data, partial=True)
        except Dog.DoesNotExist:
            serializer = DogCreateSerializer(data=dog_data)

        if serializer.is_valid():
            dog_instance = serializer.save()
            results.append(DogCreateSerializer(dog_instance).data)
        else:
            errors.append({'index': idx, 'error': serializer.errors})

    response = {'updated_or_created': results}
    if errors:
        response['errors'] = errors

    return Response(response, status=status.HTTP_207_MULTI_STATUS if errors else status.HTTP_200_OK)



def update_instance_fields(instance, data, fields):
    """
    Updates the instance fields only if values have changed.
    
    Args:
        instance: Django model instance
        data: dict of new field values
        fields: list of field names to check and update
    
    Returns:
        (bool, list): (was_updated, list_of_changed_fields)
    """
    was_updated = False
    changed_fields = []

    for field in fields:
        new_value = data.get(field)
        if getattr(instance, field) != new_value:
            setattr(instance, field, new_value)
            was_updated = True
            changed_fields.append(field)
    
    if was_updated:
    	setattr(instance, 'update_date', str(datetime.date.today()))
    	instance.save()
    
    return was_updated, changed_fields




@api_view(['POST'])
def full_snapshot_dogs(request):
    if not isinstance(request.data, list):
        return Response({'error': 'Expected a list of dog objects.'}, status=status.HTTP_400_BAD_REQUEST)

    incoming_ids = set()
    errors = []
    created = 0
    updated = 0

    for idx, dog_data in enumerate(request.data):
        nameext = dog_data.get('nameext')
        if not nameext:
            errors.append({'index': idx, 'error': 'Missing nameext'})
            continue

        incoming_ids.add(nameext)





        # Update or create
        # dog, created_flag = Dog.objects.update_or_create(
        #     nameext=nameext,
        #     defaults={
        #         'name': dog_data.get('name'),
        #         'breed': dog_data.get('breed'),
        #         'age': dog_data.get('age'),
        #         'status': dog_data.get('status', 'Available'),
        #     }
        # )
        # if created_flag:
        #     created += 1
        # else:
        #     updated += 1



		# new update create
        dog = Dog.objects.filter(nameext=nameext).first()
        if dog is None:
            dog = Dog.objects.create(
                nameext=nameext,
                name=dog_data.get('name'),
        	    breed=dog_data.get('breed'),
        	    age=dog_data.get('age'),
        	    sex=dog_data.get('sex'),
        	    url=dog_data.get('url'),
        	    colour=dog_data.get('colour'),
				size=dog_data.get('size'),
				notes=dog_data.get('notes'),
        	    status=dog_data.get('status', 'Available'),
        	    image = dog_data.get('image'),
    	        )
            created += 1

        else:
            was_updated, changed_fields = update_instance_fields(
                dog,
                {
                    'name': dog_data.get('name'),
                    'breed': dog_data.get('breed'),
                    'age': dog_data.get('age'),
                    'sex': dog_data.get('sex'),
           	    	'url': dog_data.get('url'),
        	    	'colour': dog_data.get('colour'),
					'size': dog_data.get('size'),
					'notes': dog_data.get('notes'),
                    'status': dog_data.get('status', 'Available'),
                    'image': dog_data.get('image')
                },
        		fields=['name', 'breed', 'age', 'sex','url', 'colour', 'size', 'notes','status','image']
            )
            if was_updated:
                updated += 1
                print(f"****************Updated dog {dog.nameext}, fields changed: {changed_fields} *************")


		# --- Handle additional URLs ---
        urls = dog_data.get('images', [])
        if isinstance(urls, list):
            DogURL.objects.filter(dog=dog).delete()  # clear previous
            dogurl_objs = [DogURL(dog=dog, url=u) for u in urls if u]
            DogURL.objects.bulk_create(dogurl_objs)



    # Deactivate dogs not in the incoming snapshot
    deactivated = Dog.objects.exclude( Q(nameext__in=incoming_ids) | Q(status__in=['Inactive','Adopted']) | Q(local_created_dog__in=[True])).update(status='Adopted', adoption_date = datetime.date.today(), update_date = datetime.date.today())

    return Response({
        'created': created,
        'updated': updated,
        'deactivated': deactivated,
        'errors': errors
    })








class HomeView(TemplateView):
    template_name = 'core/home.html'
    model = Dog
    #template_name = 'core/dog_list.html'
    context_object_name = 'dogs'
    paginate_by = 10



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cutoff_date = datetime.date.today() - timedelta(days=2)

        dogs = Dog.objects.filter(
            Q(creation_date__gte=cutoff_date) |
            Q(adoption_date__gte=cutoff_date)
        )
       
        # Print the SQL query
        print(dogs.query)  # 💡 Shows the raw SQL that will be executed

        context['dogs'] = dogs
        return context



# class DogListView(ListView):
#     model = Dog
#     template_name = 'core/dog_list.html'
#     context_object_name = 'dogs'
#     paginate_by = 10



# class DogListView(ListView):
#     model = Dog
#     template_name = 'core/dog_list.html'
#     context_object_name = 'dogs'
#     paginate_by = 10

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         q = self.request.GET.get('q')
#         if q:
#             #queryset = queryset.filter(name__icontains=q)
#             queryset = queryset.filter(
#                 Q(name__icontains=q) | Q(status__icontains=q) ) # ← OR filter
#         #return queryset
#         return queryset.order_by('name')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['search_query'] = self.request.GET.get('q', '')
#         return context

from django.views.generic import ListView
from django.db.models import Q
from .models import Dog

class DogListView(ListView):
    model = Dog
    template_name = 'core/dog_list.html'
    context_object_name = 'dogs'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.GET.get('name')
        status = self.request.GET.get('status')
        creation_date_from = self.request.GET.get('creation_date_from')
        creation_date_to = self.request.GET.get('creation_date_to')
        adoption_date_from = self.request.GET.get('adoption_date_from')
        adoption_date_to = self.request.GET.get('adoption_date_to')
        update_date_from = self.request.GET.get('update_date_from')
        update_date_to = self.request.GET.get('update_date_to')
        bonded_pair = self.request.GET.get('bonded_pair')

        if name:
            queryset = queryset.filter(name__icontains=name)

        if status:
            queryset = queryset.filter(status__icontains=status)

        if creation_date_from:
            queryset = queryset.filter(creation_date__gte=creation_date_from)
        if creation_date_to:
            queryset = queryset.filter(creation_date__lte=creation_date_to)

        if adoption_date_from:
            queryset = queryset.filter(adoption_date__gte=adoption_date_from)
        if adoption_date_to:
            queryset = queryset.filter(adoption_date__lte=adoption_date_to)

        if update_date_from:
            queryset = queryset.filter(update_date__gte=update_date_from)
        
        if update_date_to:
            queryset = queryset.filter(update_date__lte=update_date_to)

        if bonded_pair:
            queryset = queryset.filter(bonded_pair_dog__isnull=False)



        
        queryset = queryset.annotate(lower_name=Lower('name')).order_by('lower_name')
        print(queryset.query)
        return queryset






    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Copy and filter GET parameters
        querydict = self.request.GET.copy()
        querydict.pop('page', None)  # Remove existing 'page' param
        context['query_string'] = querydict.urlencode()


        context['name_query'] = self.request.GET.get('name', '')
        context['status_query'] = self.request.GET.get('status', '')
        context['creation_date_from'] = self.request.GET.get('creation_date_from', '')
        context['creation_date_to'] = self.request.GET.get('creation_date_to', '')
        context['adoption_date_from'] = self.request.GET.get('adoption_date_from', '')
        context['adoption_date_to'] = self.request.GET.get('adoption_date_to', '')
        context['update_date_from'] = self.request.GET.get('update_date_from', '')
        context['update_date_to'] = self.request.GET.get('update_date_to', '')
        context['bonded_pair'] = self.request.GET.get('bonded_pair', '')
        #context['query_string'] = self.request.GET.urlencode()  # For pagination links
        return context










class DogCreateView(CreateView):
    model = Dog
    fields = '__all__'
    template_name = 'core/form.html'
    success_url = reverse_lazy('dog_list')

# class DogUpdateView(UpdateView):
#     model = Dog
#     fields = '__all__'
#     template_name = 'core/form.html'
#     success_url = reverse_lazy('dog_list')


# class DogUpdateView(UpdateView):
#     model = Dog
#     form_class = DogUpdateForm
#     template_name = 'core/dog_edit_form.html'
#     success_url = reverse_lazy('dog_list')  # fallback

#     def get(self, request, *args, **kwargs):
#         referer = request.META.get('HTTP_REFERER')
#         if referer:
#             request.session['previous_page'] = referer
#         return super().get(request, *args, **kwargs)

#     def get_success_url(self):
#         return self.request.session.pop('previous_page', reverse_lazy('dog_list'))

# LoginRequiredMixin,

class DogUpdateView(LoginRequiredMixin,UpdateView):
    model = Dog
    form_class = DogUpdateForm
    template_name = 'core/dog_edit_form.html'
    #success_url = reverse_lazy('dog_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_urls = DogURL.objects.filter(dog=self.object)
        context['MEDIA_URL'] = settings.MEDIA_URL
        image_urls = [u for u in all_urls if u.url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        context['dogurls'] = image_urls
        return context

    def get(self, request, *args, **kwargs):
        referer = request.META.get('HTTP_REFERER')
        if referer:
            request.session['previous_page'] = referer
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.session.pop('previous_page', reverse_lazy('dog_list'))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        original = Dog.objects.get(pk=self.object.pk)

        # Fields to watch
        watched_fields = ['name', 'status',  'breed', 'age', 'sex','url', 'colour', 'size', 'notes',
        	'adoption_date','health_status','vaccinated','neutered','arrival_date', 'bonded_pair_dog']
        changed = any(
            field in form.changed_data and getattr(original, field) != form.cleaned_data[field]
            for field in watched_fields
        )

        if changed:
            self.object.update_date = datetime.date.today()

        new_bond = form.cleaned_data.get('bonded_pair_dog')
        old_bond = original.bonded_pair_dog

        # 1. Remove reverse link from old bonded pair if it no longer applies
        if old_bond and old_bond != new_bond:
            old_bond.bonded_pair_dog = None
            old_bond.save()

        # 2. Create or update reverse link on new bonded pair
        if new_bond and new_bond.bonded_pair_dog != self.object:
            new_bond.bonded_pair_dog = self.object
            new_bond.save()


        self.object.save()
        return super().form_valid(form)


 

from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from .models import Dog, DogURL
from django.conf import settings

class DogReadOnlyView( UpdateView):
    model = Dog
    form_class = DogReadonlyForm
    template_name = 'core/dog_readonly_form.html'
    context_object_name = 'dog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_urls = DogURL.objects.filter(dog=self.object)
        context['MEDIA_URL'] = settings.MEDIA_URL
        image_urls = [u for u in all_urls if u.url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        context['dogurls'] = image_urls
       
        # Add referrer to context for use in template
        context['back_url'] = self.request.session.get('previous_page', reverse_lazy('dog_list'))

        return context

    def get(self, request, *args, **kwargs):
        referer = request.META.get('HTTP_REFERER')
        if referer :
            request.session['previous_page'] = referer
        return super().get(request, *args, **kwargs)

class DogDeleteView(DeleteView):
    model = Dog
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('dog_list')


class AdopterListView(ListView):
    model = Adopter
    template_name = 'core/adopter_list.html'
    context_object_name = 'adopters'
    paginate_by = 10

class AdopterCreateView(CreateView):
    model = Adopter
    fields = '__all__'
    template_name = 'core/form.html'
    success_url = reverse_lazy('adopter_list')

class AdopterUpdateView(UpdateView):
    model = Adopter
    fields = '__all__'
    template_name = 'core/form.html'
    success_url = reverse_lazy('adopter_list')

class AdopterDeleteView(DeleteView):
    model = Adopter
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('adopter_list')


class AdoptionListView(ListView):
    model = Adoption
    template_name = 'core/adoption_list.html'
    context_object_name = 'adoptions'
    paginate_by = 10

class AdoptionCreateView(CreateView):
    model = Adoption
    fields = '__all__'
    template_name = 'core/form.html'
    success_url = reverse_lazy('adoption_list')

class AdoptionUpdateView(UpdateView):
    model = Adoption
    fields = '__all__'
    template_name = 'core/form.html'
    success_url = reverse_lazy('adoption_list')

class AdoptionDeleteView(DeleteView):
    model = Adoption
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('adoption_list')






class FosterHomeListView(ListView):
    model = FosterHome
    template_name = 'fosterhome/fosterhome_list.html'

class FosterHomeDetailView(DetailView):
    model = FosterHome
    template_name = 'fosterhome/fosterhome_detail.html'

class FosterHomeCreateView(CreateView):
    model = FosterHome
    fields = '__all__'
    template_name = 'fosterhome/fosterhome_form.html'
    success_url = reverse_lazy('fosterhome_list')

class FosterHomeUpdateView(UpdateView):
    model = FosterHome
    fields = '__all__'
    template_name = 'fosterhome/fosterhome_form.html'
    success_url = reverse_lazy('fosterhome_list')

class FosterHomeDeleteView(DeleteView):
    model = FosterHome
    template_name = 'fosterhome/fosterhome_confirm_delete.html'
    success_url = reverse_lazy('fosterhome_list')




from django.shortcuts import render, get_object_or_404, redirect
from .models import Dog, MedicalRecord
from .forms import MedicalRecordForm

# View list of medical records for a specific dog
def medical_record_list(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id)
    records = MedicalRecord.objects.filter(dog=dog).order_by('-checkup_date')
    return render(request, 'medical_records/list.html', {'dog': dog, 'records': records})

# Create a new medical record for a dog
# def medical_record_create(request, dog_id):
#     dog = get_object_or_404(Dog, id=dog_id)
#     if request.method == 'POST':
#         form = MedicalRecordForm(request.POST)
#         if form.is_valid():
#             record = form.save(commit=False)
#             record.dog = dog
#             record.save()
#             return redirect('medical_record_list', dog_id=dog.id)
#     else:
#         form = MedicalRecordForm()
#     return render(request, 'medical_records/form.html', {'form': form, 'dog': dog})




def medical_record_create(request, dog_id):
    dog = get_object_or_404(Dog, id=dog_id)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.dog = dog
            record.last_update_date = timezone.now().date()  # set current date
            record.save()
            return redirect('medical_record_list', dog_id=dog.id)
    else:
        form = MedicalRecordForm()
    return render(request, 'medical_records/form.html', {'form': form, 'dog': dog})



def medical_record_edit(request, dog_id, record_id):
    dog = get_object_or_404(Dog, id=dog_id)
    record = get_object_or_404(MedicalRecord, id=record_id, dog=dog)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            updated_record = form.save(commit=False)
            updated_record.last_update_date = timezone.now().date()  # update date
            updated_record.save()
            return redirect('medical_record_list', dog_id=dog.id)
    else:
        form = MedicalRecordForm(instance=record)
    return render(request, 'medical_records/form.html', {'form': form, 'dog': dog})




# Edit an existing medical record
# def medical_record_edit(request, dog_id, record_id):
#     dog = get_object_or_404(Dog, id=dog_id)
#     record = get_object_or_404(MedicalRecord, id=record_id, dog=dog)
#     if request.method == 'POST':
#         form = MedicalRecordForm(request.POST, instance=record)
#         if form.is_valid():
#             form.save()
#             return redirect('medical_record_list', dog_id=dog.id)
#     else:
#         form = MedicalRecordForm(instance=record)
#     return render(request, 'medical_records/form.html', {'form': form, 'dog': dog})






# adoptions/views.py


class DogListAPIView(generics.ListAPIView):
    queryset = Dog.objects.all()
    serializer_class = DogSerializer






from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import DogWalker, DogWalk
from .forms import DogWalkerForm, DogWalkForm
from django.db.models import Q

# --- DogWalker Views ---

class DogWalkerListView(ListView):
    model = DogWalker
    template_name = 'dogwalker_list.html'
    context_object_name = 'walkers'

    def get_queryset(self):
        query = self.request.GET.get('q')
        qs = super().get_queryset()
        if query:
            qs = qs.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
        return qs

class DogWalkerCreateView(CreateView):
    model = DogWalker
    form_class = DogWalkerForm
    template_name = 'dogwalker_form.html'
    success_url = reverse_lazy('dogwalker_list')

class DogWalkerUpdateView(UpdateView):
    model = DogWalker
    form_class = DogWalkerForm
    template_name = 'dogwalker_form.html'
    success_url = reverse_lazy('dogwalker_list')

class DogWalkerDeleteView(DeleteView):
    model = DogWalker
    template_name = 'dogwalker_confirm_delete.html'
    success_url = reverse_lazy('dogwalker_list')


# --- DogWalk Views ---

class DogWalkListView(ListView):
    model = DogWalk
    template_name = 'dogwalk_list.html'
    context_object_name = 'walks'

class DogWalkCreateView(CreateView):
    model = DogWalk
    form_class = DogWalkForm
    template_name = 'dogwalk_form.html'
    success_url = reverse_lazy('dogwalk_list')

class DogWalkUpdateView(UpdateView):
    model = DogWalk
    form_class = DogWalkForm
    template_name = 'dogwalk_form.html'
    success_url = reverse_lazy('dogwalk_list')

class DogWalkDeleteView(DeleteView):
    model = DogWalk
    template_name = 'dogwalk_confirm_delete.html'
    success_url = reverse_lazy('dogwalk_list')



    from django.shortcuts import render, get_object_or_404, redirect
from .models import DogFosterAssignment
from .forms import DogFosterAssignmentForm

# Create
def dog_foster_assignment_create(request):
    if request.method == 'POST':
        form = DogFosterAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dog_foster_assignment_list')
    else:
        form = DogFosterAssignmentForm()
    return render(request, 'core/dog_foster_assignment_form.html', {'form': form, 'action': 'Create'})

# Update
def dog_foster_assignment_update(request, pk):
    assignment = get_object_or_404(DogFosterAssignment, pk=pk)
    if request.method == 'POST':
        form = DogFosterAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            return redirect('dog_foster_assignment_list')
    else:
        form = DogFosterAssignmentForm(instance=assignment)
    return render(request, 'core/dog_foster_assignment_form.html', {'form': form, 'action': 'Update'})

# Delete
def dog_foster_assignment_delete(request, pk):
    assignment = get_object_or_404(DogFosterAssignment, pk=pk)
    if request.method == 'POST':
        assignment.delete()
        return redirect('dog_foster_assignment_list')
    return render(request, 'core/dog_foster_assignment_confirm_delete.html', {'assignment': assignment})


from .models import DogFosterAssignment

def dog_foster_assignment_list(request):
    assignments = DogFosterAssignment.objects.select_related('dog', 'foster').order_by('-start_date')
    return render(request, 'core/dog_foster_assignment_list.html', {'assignments': assignments})


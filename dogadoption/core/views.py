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

from .models import DogSnapshotLog
import socket



import paho.mqtt.client as mqtt
# MQTT broker settings
BROKER = "192.168.1.146"   # replace with broker IP/hostname
PORT = 1883                           # 8883 if using TLS
TOPIC = "dogs/adoption/updates"
CLIENT_ID = "dogrescue_publisher"

# Authentication
USERNAME = "wombat"
PASSWORD = "wombat"

def publish_message(message: str):
    # Create client
    client = mqtt.Client(client_id=CLIENT_ID)

    # Set username and password
    client.username_pw_set(USERNAME, PASSWORD)

    # Connect to broker
    client.connect(BROKER, PORT, 60)

    # Publish message
    result = client.publish(TOPIC, message)

    # Check if publish was successful
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✅ Message sent to {TOPIC}: {message}")
    else:
        print("❌ Failed to publish message")

    # Disconnect
    client.disconnect()




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
    	setattr(instance, 'update_date', str(datetime.today().date())) 
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
    action_log = ""
    add_remove_log = ""

    for idx, dog_data in enumerate(request.data):
        nameext = dog_data.get('nameext')
        if not nameext:
            errors.append({'index': idx, 'error': 'Missing nameext'})
            continue

        incoming_ids.add(nameext)


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
            action_log += f"created dog: name: { dog_data.get('name') }, breed: { dog_data.get('breed') } \n"

            add_remove_log += f"created dog: name: { dog_data.get('name') }, breed: { dog_data.get('breed') } \n"

        else:
            # handle an incoming record where the existing dog's status is one of the following:
            #     Adopted -> new status is Adopted-Returned
            #     Fostered -> leave as fostered
            #     other -> set tho Active
            cur_status = dog.status
            if cur_status in ['Adopted', 'Adopted-Ret']:
                new_status = 'Adopted-Ret'
            elif cur_status == 'Fostered':
                new_status = 'Fostered'
            elif cur_status == 'Deceased':
                new_status = 'Deceased'
            else:
                new_status = 'Available'

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
                    'status': new_status, #dog_data.get('status', 'Available'),
                    'image': dog_data.get('image')
                },
        		fields=['name', 'breed', 'age', 'sex','url', 'colour', 'size', 'notes','status','image']
            )
            if was_updated:
                updated += 1
                print(f"****************Updated dog {dog.nameext}, fields changed: {changed_fields} *************")
                action_log += f"Updated dog {dog.name}, fields changed: {changed_fields} \n"


		# --- Handle additional URLs ---
        urls = dog_data.get('images', [])
        if isinstance(urls, list):
            DogURL.objects.filter(dog=dog).delete()  # clear previous
            dogurl_objs = [DogURL(dog=dog, image=u) for u in urls if u]
            DogURL.objects.bulk_create(dogurl_objs)



    # Deactivate dogs not in the incoming snapshot
    deactivated = Dog.objects.exclude( Q(nameext__in=incoming_ids) | Q(status__in=['Inactive','Adopted','Deceased']) | Q(local_created_dog__in=[True]))
    print("Deactivated dogs:")
    print(deactivated)
    for y in deactivated:
        action_log += f"Deactivating: {y.name}\n"
        add_remove_log += f"Deactivating: {y.name}\n"

        #remove friend dog references to the dog being deactivated

        #remove bonded dog references the dog being deactivated


    deactivated = Dog.objects.exclude( Q(nameext__in=incoming_ids) | Q(status__in=['Inactive','Adopted','Deceased']) | Q(local_created_dog__in=[True])).update(status='Adopted', adoption_date = datetime.today().date(), update_date = datetime.today().date())


  # 🔹 Save to database log
    DogSnapshotLog.objects.create(
        created=created,
        updated=updated,
        deactivated=deactivated,
        errors=errors,
        details=action_log
    )


    if add_remove_log != "":
        try:
            publish_message(add_remove_log)
    
        except (ConnectionRefusedError, socket.gaierror, OSError) as e:
            print(f"❌ Network/connection error: {e}")
        except ssl.SSLError as e:
            print(f"❌ SSL/TLS error: {e}")
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


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

        cutoff_date = datetime.today() - timedelta(days=2)
        #cutoff_date = datetime.date.today() - timedelta(days=2)

        dogs = Dog.objects.filter(
            Q(creation_date__gte=cutoff_date) |
            Q(adoption_date__gte=cutoff_date)
        )
       
        # Print the SQL query
        print(dogs.query)  # 💡 Shows the raw SQL that will be executed

        recent_snapshots = DogSnapshotLog.objects.order_by('-timestamp')[:3]
   
        context['dogs'] = dogs
        context['logs']  = recent_snapshots
        
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

# views.py
from django.forms import modelformset_factory
from django.shortcuts import redirect
#from .forms import DogUpdateForm, DogURLFormSet
from .models import Dog, DogURL
import datetime

class DogUpdateView(LoginRequiredMixin, UpdateView):
    model = Dog
    form_class = DogUpdateForm
    template_name = 'core/dog_edit_form.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #all_urls = DogURL.objects.filter(dog=self.object)
        context['MEDIA_URL'] = settings.MEDIA_URL
        context['dogurls'] = DogURL.objects.filter(dog=self.object)
        return context

    def get(self, request, *args, **kwargs):
        referer = request.META.get('HTTP_REFERER')
        if referer:
            request.session['previous_page'] = referer
        
        return super().get(request, *args, **kwargs)


    def form_invalid(self, form):
        print("Form is invalid:", form.errors)
        return super().form_invalid(form)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        print("processing post")
        form = self.form_class(request.POST, request.FILES, instance=self.object)
        form2 = self.get_form()
        print(f"is valid form: {form.is_valid()}")
        print(f"is valid form2: {form2.is_valid()}")
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)



        


    def form_valid(self, form):
        self.object = form.save(commit=False)
        original = Dog.objects.get(pk=self.object.pk)
        print("in form_valid()*****")
        watched_fields = [
            'name', 'status', 'breed', 'age', 'sex', 'url', 'colour', 'size', 'notes',
            'adoption_date', 'health_status', 'vaccinated', 'neutered',
            'arrival_date', 'bonded_pair_dog'
        ]
        changed = any(
            field in form.changed_data and getattr(original, field) != form.cleaned_data[field]
            for field in watched_fields
        )

        if changed:
            self.object.update_date = datetime.today().date()


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



        # Save Dog
        self.object.save()

        # Handle new image uploads
        #print("iterate through new image files")
        #print(self.request.FILES)

        for file in self.request.FILES.getlist('new_images'):
            print(file)
            DogURL.objects.create(dog=self.object, image=file)


        return super().form_valid(form)


    def get_success_url(self):
        return self.request.session.pop('previous_page', reverse_lazy('dog_list'))

 
# views.py
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import DogURL

@login_required
@require_POST
def delete_dog_image(request, image_id):
    image = get_object_or_404(DogURL, id=image_id)
    # Optional: Add extra permission check if needed
    image.delete()
    return JsonResponse({'success': True})



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
        #print("all_urls")
        #print(all_urls)
        context['MEDIA_URL'] = settings.MEDIA_URL
        #image_urls = [u for u in all_urls if u.image.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        image_urls = [u for u in all_urls]
        #print("image_urls")
        #print(image_urls)
        #for url in image_urls:
            #print(url.image)

        context['dogurls'] = image_urls
       
        # Add referrer to context for use in template
        context['back_url'] = self.request.session.get('previous_page', reverse_lazy('dog_list'))


        # If fostered, find the foster person
        if self.object.status == 'Fostered':
            foster_assignment = (
                DogFosterAssignment.objects
                .filter(dog=self.object)
                .order_by('-start_date')  # assuming you have a start_date
                .first()
            )
            if foster_assignment and foster_assignment.foster:
                context['foster_person'] = foster_assignment.foster
            else:
                context['foster_person'] = "Missing foster family details"

       # If Adoppted, find the adopter person
        if self.object.status == 'Adopted':
            adoption = (
                Adoption.objects
                .filter(dog=self.object)
                .order_by('-adoption_date')  # assuming you have a start_date
                .first()
            )
            if adoption and adoption.adopter:
                context['adopter_person'] = adoption.adopter
            else:
                context['adopter_person'] = "Missing adoption family details"



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





from django.db.models import Q, Value
from django.db.models.functions import Concat

class AdopterListView(ListView):
    model = Adopter
    template_name = 'core/adopter_list.html'
    context_object_name = 'adopters'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')  # The search term from the form

        if query:
            # Annotate with full_name = first_name + ' ' + last_name
            queryset = queryset.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(full_name__icontains=query)
            )

        return queryset






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


from django.db.models import Q, Value
from django.db.models.functions import Concat

class AdoptionListView(ListView):
    model = Adoption
    template_name = 'core/adoption_list.html'
    context_object_name = 'adoptions'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')

        if query:
            queryset = queryset.annotate(
                adopter_full_name=Concat(
                    'adopter__first_name',
                    Value(' '),
                    'adopter__last_name'
                )
            ).filter(
                Q(dog__name__icontains=query) |
                Q(adopter__first_name__icontains=query) |
                Q(adopter__last_name__icontains=query) |
                Q(adopter_full_name__icontains=query)
            )#.distinct()

        return queryset






class AdoptionCreateView(CreateView):
    model = Adoption
    fields = '__all__'
    template_name = 'core/form.html'
    success_url = reverse_lazy('adoption_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Update dog's status
        adoption = self.object  # the newly created adoption instance
        if adoption.dog:
            adoption.dog.status = 'Adopted'
            adoption.dog.save(update_fields=['status'])

        return response




from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .models import Adoption

# class AdoptionUpdateView(UpdateView):
#     model = Adoption
#     fields = '__all__'
#     template_name = 'core/form.html'
#     success_url = reverse_lazy('adoption_list')

#     def form_valid(self, form):
#         # Fetch the original object directly from DB to get the *old* dog
#         old_instance = Adoption.objects.get(pk=self.object.pk)
#         old_dog = old_instance.dog
#         print(f"old dog: {old_dog}")

#         # Save normally
#         response = super().form_valid(form)

#         # Now get the new dog after saving
#         new_dog = self.object.dog
#         print(f"new dog: {new_dog}")

#         # If the dog has changed
#         if old_dog and old_dog != new_dog:
#             print("dogs different")
#             old_dog.status = 'Available'
#             old_dog.save(update_fields=['status'])

#         # Set the new dog's status to Adopted
#         if new_dog:
#             new_dog.status = 'Adopted'
#             new_dog.save(update_fields=['status'])

#         return response



class AdoptionUpdateView(UpdateView):
    model = Adoption
    fields = '__all__'
    template_name = 'core/form.html'
    success_url = reverse_lazy('adoption_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Make the dog field read-only
        if 'dog' in form.fields:
            form.fields['dog'].disabled = True
        return form

    def form_valid(self, form):
        # Fetch the original object directly from DB to get the *old* dog
        old_instance = Adoption.objects.get(pk=self.object.pk)
        old_dog = old_instance.dog
        print(f"old dog: {old_dog}")

        # Save normally
        response = super().form_valid(form)

        # Now get the new dog after saving
        new_dog = self.object.dog
        print(f"new dog: {new_dog}")

        # If the dog has changed
        if old_dog and old_dog != new_dog:
            print("dogs different")
            old_dog.status = 'Available'
            old_dog.save(update_fields=['status'])

        # Set the new dog's status to Adopted
        if new_dog:
            new_dog.status = 'Adopted'
            new_dog.save(update_fields=['status'])

        return response







class AdoptionDeleteView(DeleteView):
    model = Adoption
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('adoption_list')

    def post(self, request, *args, **kwargs):
        # Get the object before deletion
        self.object = self.get_object()

        print("POST method called for delete")

        # Update dog's status before deleting
        if self.object.dog:
            print(f"Dog {self.object.dog.name} exists — setting status to Available")
            self.object.dog.status = 'Available'
            self.object.dog.save(update_fields=['status'])

        # Now proceed with normal deletion
        return super().post(request, *args, **kwargs)




# class FosterHomeListView(ListView):
#     model = FosterHome
#     template_name = 'fosterhome/fosterhome_list.html'
#     context_object_name = 'fosterhome'
#     paginate_by = 4


#from django.db.models import Q

class FosterHomeListView(ListView):
    model = FosterHome
    template_name = 'fosterhome/fosterhome_list.html'
    context_object_name = 'fosterhome'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')  # The search term from the form

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(email__icontains=query)
            )

        return queryset





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

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')

        if query:
            queryset = queryset.annotate(
                walker_full_name=Concat(
                    'walker__first_name',
                    Value(' '),
                    'walker__last_name'
                )
            ).filter(
                Q(dog__name__icontains=query) |
                Q(walker__first_name__icontains=query) |
                Q(walker__last_name__icontains=query) |
                Q(walker_full_name__icontains=query)
            )#.distinct()

        return queryset




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
            assignment = form.save(commit=True)
            #form.save()

            # Update the dog's status
            dog = assignment.dog  # assuming DogFosterAssignment has a FK to Dog named 'dog'
            dog.status = 'Fostered'  # or whatever value you want
            dog.save(update_fields=['status'])
            return redirect('dog_foster_assignment_list')
    else:
        form = DogFosterAssignmentForm()
    return render(request, 'core/dog_foster_assignment_form.html', {'form': form, 'action': 'Create'})

# Update
def dog_foster_assignment_update(request, pk):
    assignment = get_object_or_404(DogFosterAssignment, pk=pk)
    old_dog = assignment.dog  # store the current dog before updating

    if request.method == 'POST':
        form = DogFosterAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            updated_assignment = form.save(commit=False)

            # If the dog has changed, update both statuses
            if updated_assignment.dog != old_dog:
                # Old dog back to "Available"
                old_dog.status = 'Available'
                old_dog.save(update_fields=['status'])

                # New dog to "Fostered"
                updated_assignment.dog.status = 'Fostered'
                updated_assignment.dog.save(update_fields=['status'])
            else:
                # If same dog, ensure it stays as "Fostered"
                updated_assignment.dog.status = 'Fostered'
                updated_assignment.dog.save(update_fields=['status'])

            updated_assignment.save()            
            return redirect('dog_foster_assignment_list')
    else:
        form = DogFosterAssignmentForm(instance=assignment)
    return render(request, 'core/dog_foster_assignment_form.html', {'form': form, 'action': 'Update'})

# Delete
def dog_foster_assignment_delete(request, pk):
    assignment = get_object_or_404(DogFosterAssignment, pk=pk)
    if request.method == 'POST':
        # Update the dog's status
        dog = assignment.dog  # assuming DogFosterAssignment has a FK to Dog named 'dog'
        dog.status = 'Available'  # or whatever value you want
        dog.save(update_fields=['status'])

        assignment.delete()
        return redirect('dog_foster_assignment_list')
    return render(request, 'core/dog_foster_assignment_confirm_delete.html', {'assignment': assignment})


from .models import DogFosterAssignment

# def dog_foster_assignment_list(request):
#     assignments = DogFosterAssignment.objects.select_related('dog', 'foster').order_by('-start_date')
#     return render(request, 'core/dog_foster_assignment_list.html', {'assignments': assignments})

from django.db.models import Q, Value
from django.db.models.functions import Concat

def dog_foster_assignment_list(request):
    query = request.GET.get('q', '').strip()

    assignments = DogFosterAssignment.objects.select_related('dog', 'foster').order_by('-start_date')

    if query:
        assignments = assignments.filter(
            Q(dog__name__icontains=query) |
            Q(foster__name__icontains=query) 
        )#.distinct()

    return render(
        request,
        'core/dog_foster_assignment_list.html',
        {'assignments': assignments, 'search_term': query}
    )



from django.http import JsonResponse
from .models import Dog

def dog_search(request):
    q = request.GET.get("q", "")
    dogs = Dog.objects.filter(name__icontains=q)[:10]
    return JsonResponse([{"id": d.id, "name": d.name} for d in dogs], safe=False)





# views.py


from django.shortcuts import render
from django_tables2 import RequestConfig
from django.db.models import Count, Sum  # ✅ import aggregation functions
from .models import Dog
from .reports import DogReportFilter, DogReportTable

# def dog_report(request):
#     # Annotate dogs with walk counts + total minutes
#     qs = Dog.objects.all().annotate(
#         walk_count=Count("dogwalk"),
#         walk_minutes=Sum("dogwalk__duration_minutes"),
#     )

#     # Apply filters
#     f = DogReportFilter(request.GET, queryset=qs)
#     print("dog_report:qs")
#     print(f.qs.query)
#     #print(qs)

#     # Build table
#     table = DogReportTable(f.qs)
#     RequestConfig(request, paginate={"per_page": 20}).configure(table)

#     return render(request, "core/dog_report.html", {"filter": f, "table": table})

from django.db.models import ExpressionWrapper, F, FloatField, IntegerField
from django.db.models import F, ExpressionWrapper, FloatField, Value
from django.db.models.functions import Coalesce

# def dog_report(request):
#     # Base queryset of Dogs
#     qs = Dog.objects.all()

#     # Apply filters (without annotation yet)
#     f = DogReportFilter(request.GET, queryset=qs)

#     # Now annotate AFTER filtering
#     qs = f.qs.annotate(
#         walk_count=Count("dogwalk", distinct=True),
#         walk_minutes=Coalesce(Sum("dogwalk__duration_minutes"), 0),
#         ).annotate(
#             walk_avg_minutes=ExpressionWrapper(
#                 F("walk_minutes") * 1.0 / Coalesce(F("walk_count"), 1),
#                 output_field=IntegerField()
#         )
#     )
  
#     print("final report query:")
#     print(qs.query)

#     # Build table
#     table = DogReportTable(qs)
#     RequestConfig(request, paginate={"per_page": 20}).configure(table)

#     return render(request, "core/dog_report.html", {"filter": f, "table": table})




from django.db.models import (
    Count, Sum, F, ExpressionWrapper, FloatField, Value
)
from django.db.models.functions import Coalesce, TruncWeek

# def dog_report(request):
#     # Base queryset of Dogs
#     qs = Dog.objects.all()

#     # Apply filters (without annotation yet)
#     f = DogReportFilter(request.GET, queryset=qs)

#     # Annotate total walks + total minutes
#     qs = f.qs.annotate(
#         walk_count=Count("dogwalk", distinct=True),
#         walk_minutes=Coalesce(Sum("dogwalk__duration_minutes"), 0),
#     )

#     # Count DISTINCT weeks where the dog had at least one walk
#     qs = qs.annotate(
#         walk_week_count=Count(TruncWeek("dogwalk__walk_date"), distinct=True)
#     )

#     # Average minutes per week = total_minutes / weeks
#     qs = qs.annotate(
#         walk_avg_minutes_per_week=ExpressionWrapper(
#             F("walk_minutes") * 1.0 / Coalesce(F("walk_week_count"), 1),
#             output_field=FloatField()
#         )

#         )
#     qs = qs.annotate(
#             walk_avg_minutes=ExpressionWrapper(
#                 F("walk_minutes") * 1.0 / Coalesce(F("walk_count"), 1),
#                 output_field=IntegerField()
#         )
#     )
#     print("final report query:")
#     print(qs.query)

#     # Build table
#     table = DogReportTable(qs)
#     RequestConfig(request, paginate={"per_page": 20}).configure(table)

#     return render(request, "core/dog_report.html", {"filter": f, "table": table})






from django.shortcuts import render
from django.db.models import Count, Sum, F, ExpressionWrapper, IntegerField, DurationField
from django.db.models.functions import ExtractWeek, ExtractYear
from django_tables2 import RequestConfig
from .models import Dog
from .reports import DogReportFilter, DogReportTable


from django.db.models import Count, Sum, F, ExpressionWrapper, IntegerField
from django.db.models.functions import TruncWeek

from django.db.models import Count, Sum
from django.db.models.functions import ExtractWeek
from collections import defaultdict
import json

from django.shortcuts import render
from django.db.models import Count, Sum, F, IntegerField, ExpressionWrapper
from django_tables2 import RequestConfig
from .models import Dog, DogWalk
from .reports import DogReportFilter, DogReportTable
from collections import defaultdict
from datetime import datetime, timedelta
import itertools

from django.shortcuts import render
from django.db.models import Count, Sum, F, ExpressionWrapper, IntegerField
from django.db.models.functions import TruncWeek
from django_tables2 import RequestConfig

from .models import Dog, DogWalk

from .reports import DogReportTable


from django.db.models import Count
from django.db.models.functions import ExtractWeek, ExtractYear
from django.db.models import F, Sum, Count, ExpressionWrapper, IntegerField, Case, When

import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Count
from .models import Dog, DogWalk
from .reports import DogReportFilter, DogReportTable
from django_tables2 import RequestConfig

from datetime import date, timedelta
from django.db.models import Count, Avg
from django.db.models.functions import ExtractWeek, ExtractYear
from django.shortcuts import render
from .models import Dog, DogWalk
from .reports import DogReportFilter
from .reports import DogReportTable
from django_tables2 import RequestConfig

def generate_weeks(start_date, end_date):
    """Return list of (year, week_number) tuples between start_date and end_date."""
    weeks = []
    current = start_date
    while current <= end_date:
        y, w, _ = current.isocalendar()
        if (y, w) not in weeks:
            weeks.append((y, w))
        current += timedelta(days=7)
    return weeks


from django.db.models import Subquery, OuterRef, Count, Sum, Avg, FloatField, ExpressionWrapper
from django.db.models.functions import ExtractWeek, ExtractYear
from datetime import date, timedelta

def dog_report(request):
    qs = Dog.objects.all()
    f = DogReportFilter(request.GET, queryset=qs)
    filtered_dogs = f.qs

    print("filtered_dogs:")
    print(filtered_dogs.query)

    # --- Subqueries for aggregates ---
 
    # --- Date range ---
    walk_date_after = request.GET.get("walk_date_after")
    walk_date_before = request.GET.get("walk_date_before")

    if walk_date_after:
        start_date = date.fromisoformat(walk_date_after)
    else:
        start_date = date.today() - timedelta(weeks=12)

    if walk_date_before:
        end_date = date.fromisoformat(walk_date_before)
    else:
        end_date = date.today()

    week_range = generate_weeks(start_date, end_date)

 # --- Subqueries with date range ---
    dogwalks = DogWalk.objects.filter(
        dog=OuterRef("pk"),
        walk_date__gte=start_date,
        walk_date__lte=end_date
    )

    walk_count_subq = (
        dogwalks.values("dog")
        .annotate(c=Count("id"))
        .values("c")
    )

    walk_minutes_subq = (
        dogwalks.values("dog")
        .annotate(s=Sum("duration_minutes"))
        .values("s")
    )
    qs = filtered_dogs.annotate(
        walk_count=Subquery(walk_count_subq, output_field=FloatField()),
        walk_minutes=Subquery(walk_minutes_subq, output_field=FloatField())
    )

    qs = qs.annotate(
        min_per_walk_avg=ExpressionWrapper(
            F("walk_minutes") * 1.0 / F("walk_count"),
            output_field=FloatField()
        )
    )


    # --- Walk counts by week ---
    walk_counts = (
        DogWalk.objects.filter(
            dog__in=filtered_dogs,
            walk_date__gte=start_date,
            walk_date__lte=end_date,
        )
        .annotate(year=ExtractYear("walk_date"), week=ExtractWeek("walk_date"))
        .values("dog_id", "year", "week")
        .annotate(
            walk_count=Count("id"),
            avg_minutes=Avg("duration_minutes"),
        )
    )

    # Init dicts
    dog_week_counts = {
        dog.name: {(y, w): 0 for (y, w) in week_range} for dog in filtered_dogs
    }
    dog_week_minutes = {
        dog.name: {(y, w): 0 for (y, w) in week_range} for dog in filtered_dogs
    }

    for row in walk_counts:
        dog = filtered_dogs.get(id=row["dog_id"])
        dog_week_counts[dog.name][(row["year"], row["week"])] = row["walk_count"]
        dog_week_minutes[dog.name][(row["year"], row["week"])] = (
            row["avg_minutes"] or 0
        )

    # --- Chart datasets ---
    labels = [f"{y}-W{w}" for (y, w) in week_range]
    colors = ["red", "blue", "green", "orange", "purple", "cyan", "magenta"]

    datasets_counts = []
    datasets_minutes = []
    for i, dog in enumerate(filtered_dogs):
        datasets_counts.append(
            {
                "label": dog.name,
                "data": [dog_week_counts[dog.name][(y, w)] for (y, w) in week_range],
                "borderColor": colors[i % len(colors)],
                "backgroundColor": colors[i % len(colors)],
                "fill": False,
            }
        )
        datasets_minutes.append(
            {
                "label": dog.name,
                "data": [dog_week_minutes[dog.name][(y, w)] for (y, w) in week_range],
                "borderColor": colors[i % len(colors)],
                "backgroundColor": colors[i % len(colors)],
                "fill": False,
            }
        )

    # --- Per-week average ---
    qs = qs.annotate(
        min_per_week_avg=ExpressionWrapper(
            F("walk_minutes") * 1.0 / len(week_range), output_field=FloatField()
        )
    )

    # Table
    table = DogReportTable(qs)
    RequestConfig(request, paginate={"per_page": 20}).configure(table)

    return render(
        request,
        "core/dog_report.html",
        {
            "filter": f,
            "table": table,
            "chart_labels": json.dumps(labels),
            "chart_datasets_counts": json.dumps(datasets_counts),
            "chart_datasets_minutes": json.dumps(datasets_minutes),
        },
    )



from django.shortcuts import render
from .models import Dog

from django.db.models import Q

def public_dog_list(request):
    query = request.GET.get("q", "")
    breed = request.GET.get("breed", "")
    size = request.GET.get("size", "")

    dogs = Dog.objects.filter(status="Available")

    if query:
        dogs = dogs.filter(name__icontains=query)
    if breed:
        dogs = dogs.filter(breed=breed)
    if size:
        dogs = dogs.filter(size=size)

    breeds = Dog.objects.values_list("breed", flat=True).distinct().order_by("breed")
    sizes = Dog.objects.values_list("size", flat=True).distinct().order_by("size")

    # Prefetch related DogURL images
    dogs = dogs.prefetch_related("dogurl_set")

    return render(request, "public_dog_list.html", {
        "dogs": dogs,
        "query": query,
        "breed": breed,
        "size": size,
        "breeds": breeds,
        "sizes": sizes,
    })







# reports/views.py
from django.shortcuts import render
from django.db.models.functions import TruncWeek
from django.db.models import Count
from .forms import ReportForm
from core.models import Dog  # adjust if your Dog model is in another app
from django.utils.timezone import make_aware

def dog_movement_reports(request):
    form = ReportForm(request.GET or None)
    starting_population = 0
    if form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]

        additions = (
            Dog.objects.filter(creation_date__range=[start_date, end_date])
            .annotate(week=TruncWeek("creation_date"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )

        deactivations = (
            Dog.objects.filter(adoption_date__range=[start_date, end_date])
            .annotate(week=TruncWeek("adoption_date"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )

        additions_data = {a["week"].strftime("%Y-%m-%d"): a["count"] for a in additions}
        deactivations_data = {d["week"].strftime("%Y-%m-%d"): d["count"] for d in deactivations}



        # ---- NEW: compute starting population ----
        # Find earliest week in our data
        all_weeks = sorted(set(additions_data.keys()) | set(deactivations_data.keys()))
        starting_population = 0
        if all_weeks:
            print("in all weeks")
            first_week = all_weeks[0]

            parts = first_week.split('-')
            year = int(parts[0])
            week = int(parts[1])

            # Get first day of that ISO week
            #start_date = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w")
            #start_date = make_aware(start_date)
            print(f"start date: { start_date }")

            # Count dogs active before the reporting period
            starting_population = Dog.objects.filter(
                creation_date__lt=start_date,
            ).exclude(status__in=['Adopted', 'Deceased']).count()



            print(Dog.objects.filter(
                creation_date__lt=start_date,
            ).exclude(status__in=['Adopted', 'Deceased']).query)

            print(f"starting pop { starting_population }")



    else:
        additions_data, deactivations_data = {}, {}

    context = {
        "form": form,
        "additions_data": additions_data,
        "deactivations_data": deactivations_data,
        "starting_population": starting_population,  # pass to template
    }
    return render(request, "dog_movement_report.html", context)





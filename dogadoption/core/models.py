
# Create your models here.
from django.db import models
import datetime

class Dog(models.Model):
    SEX_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    SIZE_CHOICES = [('Toy', 'Toy'),('Small', 'Small'), ('Medium', 'Medium'), ('Large', 'Large')]
    STATUS_CHOICES = [('Available', 'Available'), ('Adopted', 'Adopted'),  ('Adopted-Ret', 'Adopted-Ret'),('Fostered', 'Fostered'), ('Pending', 'Pending'), ('Unavailable', 'Unavailable'), ('Inactive', 'Inactive')]

    WALKER_CAPABILITY_CHOICES = [('Beginner <10', 'Beginner <10'),('General','General'), ('Experienced','Experienced'), ('KH','KH'), ('Dog Buddy','Dog Buddy')]
    WALK_GUIDANCE_CHOICES = [('Bed rest','Bed rest'), ('Less than 20 mins','Less than 20 mins'), ('Greater Than 20 mins', 'Greater Than 20 mins'), ('Unlimited', 'Unlimited')]

    name = models.CharField(max_length=100)
    nameext = models.CharField(max_length=100, unique=True)
    url = models.CharField(max_length=200)
    breed = models.CharField(max_length=100, blank=True, null=True)
    age = models.CharField(max_length=100)
    sex = models.CharField(max_length=6, choices=SEX_CHOICES)
    size = models.CharField(max_length=6, choices=SIZE_CHOICES)
    colour = models.CharField(max_length=50, blank=True, null=True)
    health_status = models.TextField(blank=True, null=True)
    vaccinated = models.BooleanField(default=False)
    neutered = models.BooleanField(default=False)
    arrival_date = models.DateField(blank=True, null=True)
    adoption_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Available')
    notes = models.TextField(blank=True, null=True)
    creation_date = models.DateField(default=datetime.date.today)
    update_date = models.DateField(blank=True, null=True)
    local_created_dog = models.BooleanField(default=False)
    image = models.ImageField(upload_to='dog_images/', null=True, blank=True)
    bonded_pair_dog = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='bonded_pair_dog_rel')

    # Walking requirements
    walker_capability = models.CharField(max_length=25, choices=WALKER_CAPABILITY_CHOICES, default='General')
    walk_guidance = models.CharField(max_length=30, choices=WALK_GUIDANCE_CHOICES, default='Greater Than 20 mins')
    requires_companion_dog = models.BooleanField(default=False)
    friend_dog1 = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='friend1')
    friend_dog2 = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='friend2')
    friend_dog3 = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='friend3')
    #friend_dog4 = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='friend4')
    #friend_dog5 = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='friend5')
    #friend_dog6 = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='friend6')


    def __str__(self):
        return self.name


       
class DogURL(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='dog_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.dog.name} - {self.image.url if self.image else 'No Image'}"



class DogWalker(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]
    WALKER_CAPABILITY_CHOICES = [('Beginner <10 walks', 'Beginner <10 walks'),('General','General'), ('Experienced','Experienced'), ('KH','KH'), ('Dog Buddy', 'Dog Buddy')]
 

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    onboard_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    experience = models.CharField(max_length=25, choices=WALKER_CAPABILITY_CHOICES, default='General')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DogWalk(models.Model):
    WALKING_STYLE_CHOICES = [('Calm/loose leash','Calm/loose leash'), ('Didn''t walk','Didn''t walk') , ('Pulled strongly','Pulled strongly')]
    DOG_FRIENDLINESS_CHOICES = [('Aloof','Aloof'), ('Allowed patting','Allowed patting'), ('Cuddly','Cuddly')]

    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    walker = models.ForeignKey(DogWalker, on_delete=models.CASCADE)
    walk_date = models.DateField()
    duration_minutes = models.IntegerField()
    notes = models.TextField(blank=True, null=True)
    buddy_dog = models.ForeignKey(Dog, on_delete=models.SET_NULL, blank=True, null=True, related_name='walkbuddy')
    walking_style = models.CharField(max_length=30, choices=WALKING_STYLE_CHOICES)
    friendliness = models.CharField(max_length=30, choices=DOG_FRIENDLINESS_CHOICES) 


class Adopter(models.Model):
    STATUS_CHOICES = [('Approved', 'Approved'), ('Pending', 'Pending'), ('Rejected', 'Rejected')]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    application_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Adoption(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE)
    adoption_date = models.DateField()
    fee_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

class FosterHome(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    max_dogs = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class DogFosterAssignment(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    foster = models.ForeignKey(FosterHome, on_delete=models.CASCADE)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

class Staff(models.Model):
    ROLE_CHOICES = [('Admin', 'Admin'), ('Volunteer', 'Volunteer'), ('Coordinator', 'Coordinator'), ('Vet', 'Vet')]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Volunteer')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class MedicalRecord(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Ongoing', 'Ongoing'), ('Resolved', 'Resolved'), ('Investigating', 'Investigating')]
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    checkup_date = models.DateField()
    vet_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    medication = models.TextField(blank=True, null=True)
    vaccinations = models.TextField(blank=True, null=True)
    follow_up_required = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Open')
    notes = models.TextField(blank=True, null=True)
    last_update_date = models.DateField(blank=True, null=True)

class Application(models.Model):
    STATUS_CHOICES = [('Submitted', 'Submitted'), ('Reviewed', 'Reviewed'), ('Approved', 'Approved'), ('Rejected', 'Rejected')]

    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE)
    application_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Submitted')
    notes = models.TextField(blank=True, null=True)


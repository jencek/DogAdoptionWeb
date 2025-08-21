from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import *

admin.site.register(Dog)
admin.site.register(Adopter)
admin.site.register(Adoption)
admin.site.register(FosterHome)
admin.site.register(DogFosterAssignment)
admin.site.register(Staff)
admin.site.register(MedicalRecord)
admin.site.register(Application)



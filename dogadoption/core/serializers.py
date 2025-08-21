from rest_framework import serializers
from .models import Dog

class DogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dog
        fields = ['name', 'nameext','url','breed', 'age', 'sex', 'size', 'colour', 'status', 'notes']

# adoptions/serializers.py
class DogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dog
        fields = '__all__'

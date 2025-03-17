from rest_framework import serializers
from .models import Task, Tag
from django.contrib.auth.models import User
from django.utils import timezone

# Define the TagSerializer before using it in TaskSerializer
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class TaskSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)  # Serialize tags
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)  # Assign users

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'due_date', 'created_at', 'updated_at', 'tags', 'assigned_to']

    def validate_due_date(self, value):
        """
        Ensure the due date is in the future.
        """
        if value and value < timezone.now():
            raise serializers.ValidationError("The due date must be in the future.")
        return value

    def create(self, validated_data):
        # Handle tags - check if each tag exists, or create a new one
        tags_data = validated_data.pop('tags', [])
        task = Task.objects.create(**validated_data)  # Create the Task object

        # If there are tags, create them and associate them with the task
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(**tag_data)  # Get or create the tag
            task.tags.add(tag)  # Add the tag to the task

        return task

    def update(self, instance, validated_data):
        # Extract tags data separately
        tags_data = validated_data.pop('tags', [])

        # Update other fields normally
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.due_date = validated_data.get('due_date', instance.due_date)
        instance.save()

        # Update tags manually
        instance.tags.clear()  # Remove existing tags
        for tag_data in tags_data:
            tag_obj, _ = Tag.objects.get_or_create(name=tag_data['name'])
            instance.tags.add(tag_obj)

        return instance



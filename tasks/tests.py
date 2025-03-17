from django.test import TestCase
from tasks.models import Task, Tag
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
import json

class TaskModelTest(TestCase):
    
    def setUp(self):
        # Creating sample tags
        self.tag1 = Tag.objects.create(name="Urgent")
        self.tag2 = Tag.objects.create(name="Work")
        
        # Create a sample task
        self.task = Task.objects.create(
            title="Test Task",
            description="This is a test task",
            status="TODO",
            priority="Medium",
            due_date=timezone.now() + timedelta(days=5)  # due in 5 days
        )
        self.task.tags.add(self.tag1, self.tag2)  # Add tags to the task

    def test_task_creation(self):
        """Test if task is created correctly"""
        task = self.task
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, "TODO")
        self.assertEqual(task.priority, "Medium")
        self.assertIsInstance(task.due_date, timezone.datetime)

    def test_task_tags(self):
        """Test if task has the correct tags"""
        task = self.task
        self.assertEqual(task.tags.count(), 2)  # Should have 2 tags
        self.assertIn(self.tag1, task.tags.all())
        self.assertIn(self.tag2, task.tags.all())

    def test_task_due_date(self):
        """Test if the due_date is properly set"""
        task = self.task
        self.assertTrue(task.due_date > timezone.now())  # Due date should be in the future

    def test_task_str_method(self):
        """Test the __str__ method of the Task model"""
        task = self.task
        self.assertEqual(str(task), "Test Task")


class TagModelTest(TestCase):

    def setUp(self):
        # Create a sample tag
        self.tag = Tag.objects.create(name="Important")

    def test_tag_creation(self):
        """Test if the tag is created correctly"""
        tag = self.tag
        self.assertEqual(tag.name, "Important")

    def test_tag_str_method(self):
        """Test the __str__ method of the Tag model"""
        tag = self.tag
        self.assertEqual(str(tag), "Important")
class TaskAPITestCase(APITestCase):

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username='testuser', password='password')
        
        # Create sample tags
        self.tag1 = Tag.objects.create(name="Urgent")
        self.tag2 = Tag.objects.create(name="Work")
        
        # Create sample task
        self.task = Task.objects.create(
            title="Test Task",
            description="This is a test task",
            status="TODO",
            priority="Medium",
            due_date=timezone.now() + timedelta(days=5)  # due in 5 days
        )
        self.task.tags.add(self.tag1, self.tag2)  # Add tags to the task

        # URL for the task API
        self.url = reverse('task-list')

    def test_create_task(self):
        """Test creating a new task via the API"""
        due_date = (timezone.now() + timedelta(days=3)).isoformat()

        data = {
            'title': "New Task",
            'description': "Description for new task",
            'status': "TODO",
            'priority': "HIGH",
            'due_date': due_date,  # Use the correctly formatted due date
            'tags': [{'id': self.tag1.id, 'name': "hehe"}]  # Correct format for the tags
        }
        
        self.client.force_authenticate(user=self.user)  # Authenticate the user
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)  # We should have 2 tasks now

    def test_get_task_list(self):
        """Test getting the list of tasks"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # We should only have 1 task in the database

    def test_update_task(self):
        """Test updating an existing task"""
        # Prepare the updated data
        data = {
            'title': "Updated Task",
            'status': "IN_PROGRESS",
            'priority': "LOW",
            'due_date': (timezone.now() + timedelta(days=2)).isoformat(),
        }
        
        task_url = reverse('task-detail', args=[self.task.id])  # URL for the task detail
        self.client.force_authenticate(user=self.user)
        
        # Perform the PUT request to update the task
        response = self.client.patch(task_url, data, format='json')
        print(response.data)
        
        # Assert that the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh the task from the database and assert the updated values
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Task")
        self.assertEqual(self.task.status, "IN_PROGRESS")
        self.assertEqual(self.task.priority, "LOW")

    def test_delete_task(self):
        """Test deleting a task"""
        task_url = reverse('task-detail', args=[self.task.id])  # URL for the task
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(task_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)  # Task should be deleted

    def test_filter_tasks_by_status(self):
        """Test filtering tasks by status"""
        response = self.client.get(self.url, {'status': 'TODO'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_invalid_due_date(self):
        """Test that providing an invalid due date format gives an error"""
        data = {
            'title': "Invalid Task",
            'description': "This is an invalid task",
            'status': "TODO",
            'priority': "LOW",
            'due_date': 'invalid-date',  # Invalid due date
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check if the error message contains 'due_date' and its specific error
        self.assertIn('due_date', response.data['detail'])
        self.assertIn('Datetime has wrong format', response.data['detail'])

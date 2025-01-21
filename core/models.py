from django.db import models
from django.utils import timezone
from django.db import models
SERVICES = (
    ('instagram', 'Instagram'),
    ('attendance','attendance'),
    ('twitter','twitter'),
    ('tiktok','tiktok'),
    ('cleaner','cleaner'),
    ('data_enricher','Data Enricher'),
    ('openai','OpenAI'),
    ('audience','Audience')
)
class Task(models.Model):
    uuid=models.UUIDField(blank=False,null=False,unique=True)

    def __str__(self):
        return str(self.uuid)
class Campaign(models.Model):
    
    uuid=models.UUIDField(blank=False,null=False,unique=True)
    # ... other campaign fields ...

class Audience(models.Model):
    uuid=models.UUIDField(blank=False,null=False,unique=True)
    Profiles = models.ManyToManyField('Profile', related_name='audiences')
    campaigns = models.ManyToManyField(Campaign, related_name='audiences')
    tasks=models.ManyToManyField(Task)

class Bot(models.Model):
    uuid=models.UUIDField(blank=False,null=False,unique=True)
    campaign=models.ForeignKey(Campaign,blank=True,null=True,on_delete=models.SET_NULL)
class Profile(models.Model):
    username=models.CharField(blank=False,null=False,max_length=100)
    info=models.JSONField(default={},blank=False,null=True)
    profile_picture = models.CharField(blank=True,null=True,max_length=100)
    service=models.CharField(blank=False,null=False,choices=SERVICES,max_length=50)
    tasks=models.ManyToManyField(Task)

    def __str__(self):
        return self.username
    class Meta:
        unique_together = ('username', 'service') 
from django.db import models

class Location(models.Model):
    service=models.CharField(blank=False,null=False,choices=SERVICES,max_length=50)
    info=models.JSONField(default={},blank=True,null=True)
    rest_id= models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6,blank=True,null=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6,blank=True,null=True)
    name = models.CharField(max_length=255)
    class Meta:
        unique_together = ('rest_id', 'service') 
    def __str__(self):
        return self.name
class Post(models.Model):
    service=models.CharField(blank=False,null=False,choices=SERVICES,max_length=50,default='instagram')
    code=models.CharField(blank=False,null=False,unique=True,max_length=500)
    location=models.ForeignKey(Location,blank=True,null=True,on_delete=models.SET_NULL)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    info = models.JSONField(default={},blank=False,null=False)
    tasks=models.ManyToManyField(Task)
    def __str__(self):
        return f"{self.profile.username} "

from django.utils.crypto import get_random_string

class PostMedia(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='medias')
    file_type = models.CharField(max_length=50, choices=[('image', 'Image'), ('video', 'Video')], default='image')
    
    file_path = models.CharField(max_length=255) 
    tasks=models.ManyToManyField(Task)
    def __str__(self):
        return f"Media for Post {self.post.id}" 

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    Profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tasks=models.ManyToManyField(Task)

class Follow(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='following') 
    following = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    tasks=models.ManyToManyField(Task)

    class Meta:
        unique_together = ('profile', 'following') 

from django.utils.crypto import get_random_string

class ProfileText(models.Model):
    
    
    uuid = models.CharField(max_length=36, unique=True, default=get_random_string, editable=False)
    content = models.TextField()
    Profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='profile_text')
    tasks=models.ManyToManyField(Task)

class PostText(models.Model):
    uuid = models.CharField(max_length=36, unique=True, default=get_random_string, editable=False)
    content = models.TextField()
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='text') 
    tasks=models.ManyToManyField(Task)

class CommentText(models.Model):
    uuid = models.CharField(max_length=36, unique=True, default=get_random_string, editable=False)
    content = models.TextField()
    comment = models.OneToOneField(Comment, on_delete=models.CASCADE, related_name='text') 
    tasks=models.ManyToManyField(Task)
class LeadAssignment(models.Model):
    Profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.SET_NULL, null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    last_interaction_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('processed', 'Processed'), ('failed', 'Failed')], default='pending')

class Log(models.Model):
    """
    Represents a log entry associated with a task. 
    Each log entry can be associated with only one output.
    """
    type = models.CharField(max_length=50)
    bot_username = models.CharField(max_length=255,blank=True,null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs') 
    datetime = models.DateTimeField(default=timezone.now)
    service = models.CharField(max_length=50)
    run_id =models.CharField(max_length=36, blank=True,null=True, editable=False)
     

    def __str__(self):
        return f"{self.type} for {self.bot_username} - {self.task}" 

class Output(models.Model):
    """
    Represents an output associated with a task. 
    A task can have multiple outputs.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='outputs') 
    run_id=models.CharField(max_length=36, unique=True, blank=False,null=False, editable=False)
    # Add other output related fields here (e.g., output_data, output_type, created_at)
    output_data = models.JSONField(blank=False, null=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    consumed_by=models.ManyToManyField(Task)

    def __str__(self):
        return f"Output for Task: {self.task.name}" 
    
from django.db import models
from django.utils import timezone

class RequestLog(models.Model):
    datetime = models.DateTimeField(blank=False,null=False) # Store timestamp in milliseconds
    request_record_type = models.CharField(max_length=50)
    service = models.CharField(max_length=100)
    end_point = models.CharField(max_length=255)
    data_point = models.CharField(max_length=255)
    url = models.URLField()
    r_type = models.CharField(max_length=10, choices=[('get', 'GET'), ('post', 'POST'), ('put', 'PUT'), ('delete', 'DELETE')])  # Limit choices for r_type
    bot_username = models.CharField(max_length=100, blank=True)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='request_logs') 
    logged_in = models.BooleanField(default=False)
    params = models.JSONField(default=dict)
    data = models.JSONField(default=dict) 
    data_text = models.TextField(blank=True, null=True) 
    status_code = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)  # Track when the log was created

    def __str__(self):
        return f"RequestLog for task {self.task}"
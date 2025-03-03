from django.contrib import admin
from .models import Profile,Post,PostMedia,PostText,Follow,Task,Location,Log,RequestLog,BulkCampaign,Audience,Output,Server,ChildBot
admin.site.register(Post)
admin.site.register(PostText)
admin.site.register(PostMedia)
admin.site.register(Follow)
admin.site.register(Task)
admin.site.register(Location)
admin.site.register(RequestLog)
admin.site.register(BulkCampaign)
admin.site.register(Audience)
admin.site.register(Output)
admin.site.register(ChildBot)
admin.site.register(Server)
@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('type', 'run_id', 'datetime')
    list_filter = ('task', 'bot_username', 'run_id','type') 
    search_fields = ('type', 'bot_username', 'run_id') 
# Register your models here.
from django.conf import settings
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username',  'profile_picture_url')
    search_fields = ('username') 
    def profile_picture_url(self, obj):
        if obj.profile_picture:
            # Construct the full URL by combining MEDIA_URL and the file path
            full_url = f"{settings.STORAGE_HOUSE_URL}{obj.profile_picture}" 
            return full_url
        return ''
    profile_picture_url.allow_tags = True 

admin.site.register(Profile,ProfileAdmin)
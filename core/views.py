from django.shortcuts import render
import json
from django.views.decorators.csrf import csrf_exempt
from core.models import Profile,Task
from django.http import JsonResponse
from rest_framework import status
# Create your views here.
@csrf_exempt
@csrf_exempt
def consume(request):
    if request.method == 'POST':
        from django.forms import model_to_dict
        
        data = json.loads(request.body)   
        
        method=data.get('method')

        for row in data.get('data'):
            
            task=Task.objects.all().filter(uuid=data['task_uuid'])
            if task:
                task=task[0]
            else:
                task=Task(uuid=data['task_uuid'])
                task.save()
            if row.get('service'):
                service=row.get('service')
                object_type=row.get('object_type')
                print(object_type)
                row['task_uuid']=data['task_uuid']
                print(object_type)
                if service == 'instagram':
                    if object_type=='profile' or object_type=='user_followers' or object_type=='user':
                        
                        from core.handlers.profile import handle_instagram_profile
                        print(row)
                        handle_instagram_profile(row,task)
                    elif object_type=='post':
                        from core.handlers.post import handle_instagram_post
                        handle_instagram_post(row,task)
                    elif object_type =='log':
                        from core.handlers.log import handle_log
                        handle_log(row,task)
                    elif object_type =='request_record':
                        from core.handlers.request_record import create_request_log
                        create_request_log(row)
                else:
                    if object_type =='log':
                        from core.handlers.log import handle_log
                        handle_log(row,task)
                    elif object_type =='request_record':
                        from core.handlers.request_record import create_request_log
                        create_request_log(row)
        return JsonResponse(data={'status':'success'} ,status=status.HTTP_200_OK)
                
            
            

            
                

            
                
                
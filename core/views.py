import uuid
import json
from datetime import datetime

from django.apps import apps
from django.db import transaction
from django.shortcuts import get_object_or_404 # if you use it
from django.http import JsonResponse, HttpResponse # if you use it
from django.http.request import HttpRequest # if you use it
from django.utils import timezone # if you use it
from django.views.decorators.csrf import csrf_exempt # if you use it
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # if you use it
from django.views.decorators.http import require_http_methods # if you use it
import psutil # if you use it

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import CursorPagination # if you use it
from rest_framework import viewsets # if you use it

from django.db import models
from core.models import ChildBot, Device, Interaction, Proxy, Task # if you use it
#from crawl.external_party_communication_facilitator import create_workflow_from_payload, queue_vivid_mind_payload, get_logs, handle_automation_task_creation # if you use it
import ast # if you use it


# ... rest of your code (the sync view and other functions) ...
# Create your views here.
import json
@csrf_exempt
def consume(request):
    if request.method == 'POST':
        from django.forms import model_to_dict
      
        data = json.loads(request.body) 
       
        
        for row in data['data']:
          
            if not type(row)==dict:
                try:
                    row=json.loads(row)##add logging here
                except Exception as e:
                    continue
            task=Task.objects.all().filter(uuid=row['task_uuid'])
            if task:
                task=task[0]
            else:
                task=Task(uuid=row['task_uuid'])
                task.save()
            if row.get('service'):
                service=row.get('service')
                object_type=row.get('object_type')

                if service == 'instagram':
                    if object_type=='profile' or object_type=='user_followers' or object_type=='user':
                        
                        from core.handlers.profile import handle_instagram_profile
                        
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
                    elif object_type=='output':
                        from core.handlers.output import handle_output
                        handle_output(row)
        return JsonResponse(data={'status':'success'} ,status=status.HTTP_200_OK)
@csrf_exempt             
@api_view(['POST'])
def sync(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        all_successful_sync_ids = {}
        errors = []  # List to store errors for failed rows
        print(data)
        for row in data.get('data'):
            payload = row
            object_id = payload.get("uuid")
            operation = payload.get("operation")
            object_body = payload.get("object_body")
            object_type = payload.get("object_type")
            sync_id = payload.get("sync_id")

            if not all([object_id, operation, object_type, sync_id]):
                error_message = "Each payload must contain uuid, operation, object_type, and sync_id"
                errors.append({"sync_id": sync_id, "error": error_message}) # Add error with sync_id
                continue  # Continue to the next row

            try:
                model_class = apps.get_model('core', object_type)
            except LookupError:
                error_message = f"Model {object_type} not found"
                errors.append({"sync_id": sync_id, "error": error_message})
                continue
            valid_fields = {field.name for field in model_class._meta.fields}
            with transaction.atomic():
                try:
                    if operation == "CREATE":
                        if object_body:
                            for key, value in object_body.items():
                                if not key in valid_fields:
                                    continue
                                field = model_class._meta.get_field(key)
                                if isinstance(field, models.DateTimeField) and value:
                                    object_body[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                elif isinstance(field, models.UUIDField) and value:
                                    object_body[key] = uuid.UUID(value)
                                elif isinstance(field, models.BooleanField) and isinstance(value, str):
                                    object_body[key] = value.lower() == 'true'
                                elif isinstance(field, models.Model) and value:
                                    try:
                                        fk_model = field.related_model
                                        object_body[key] = fk_model.objects.get(uuid=value)
                                    except fk_model.DoesNotExist:
                                        error_message = f"{field.name} with UUID {value} not found"
                                        errors.append({"sync_id": sync_id, "error": error_message})
                                        continue # skip to next row since FK is invalid
                            model_instance = model_class(**object_body)
                            model_instance.save()
                            all_successful_sync_ids.setdefault(object_type, []).append(sync_id)

                        else:
                            error_message = "Object body is required for CREATE"
                            errors.append({"sync_id": sync_id, "error": error_message})
                            continue

                    elif operation == "UPDATE":
                        
                        if object_body:
                            try:
                                model_instance = model_class.objects.get(uuid=object_id)
                            except model_class.DoesNotExist:
                                model_instance = model_class()
                                if 'uuid' in valid_fields:

                                    setattr(model_instance, 'uuid', object_id)
                                for key, value in object_body.items():
                                    if not key in valid_fields:
                                        continue
                                    field = model_class._meta.get_field(key)
                                    if isinstance(field, models.DateTimeField) and value:
                                        setattr(model_instance, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                                    elif isinstance(field, models.UUIDField) and value:
                                        setattr(model_instance, key, uuid.UUID(value))
                                    elif isinstance(field, models.BooleanField) and isinstance(value, str):
                                        setattr(model_instance, key, value.lower() == 'true')
                                    elif isinstance(field, models.Model) and value:
                                        try:
                                            fk_model = field.related_model
                                            setattr(model_instance, key, fk_model.objects.get(uuid=value))
                                        except fk_model.DoesNotExist:
                                            error_message = f"{field.name} with UUID {value} not found"
                                            errors.append({"sync_id": sync_id, "error": error_message})
                                            continue # skip to next row since FK is invalid
                                    else:
                                        setattr(model_instance, key, value)
                                model_instance.save()
                                all_successful_sync_ids.setdefault(object_type, []).append(sync_id)
                                continue # Object created, move to the next row

                            for key, value in object_body.items():
                                if not key in valid_fields:
                                    continue
                                field = model_class._meta.get_field(key)
                                if isinstance(field, models.DateTimeField) and value:
                                    setattr(model_instance, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                                elif isinstance(field, models.UUIDField) and value:
                                    setattr(model_instance, key, uuid.UUID(value))
                                elif isinstance(field, models.BooleanField) and isinstance(value, str):
                                    setattr(model_instance, key, value.lower() == 'true')
                                elif isinstance(field, models.Model) and value:
                                    try:
                                        fk_model = field.related_model
                                        setattr(model_instance, key, fk_model.objects.get(uuid=value))
                                    except fk_model.DoesNotExist:
                                        error_message = f"{field.name} with UUID {value} not found"
                                        errors.append({"sync_id": sync_id, "error": error_message})
                                        continue # skip to next row since FK is invalid
                                else:
                                    setattr(model_instance, key, value)
                            model_instance.save()
                            all_successful_sync_ids.setdefault(object_type, []).append(sync_id)

                        else:
                            error_message = "Object body is required for UPDATE"
                            errors.append({"sync_id": sync_id, "error": error_message})
                            continue

                    elif operation == "DELETE":
                        try:
                            model_instance = model_class.objects.get(uuid=object_id)
                            model_instance.delete()
                            all_successful_sync_ids.setdefault(object_type, []).append(sync_id)
                        except model_class.DoesNotExist:
                            pass

                    else:
                        error_message = f"Invalid operation: {operation}"
                        errors.append({"sync_id": sync_id, "error": error_message})
                        continue

                except Exception as e:
                    error_message = f"Error in data house sync: {e}"
                    errors.append({"sync_id": sync_id, "error": str(e)})
                    continue  # Continue to the next row

        response_data = {"message": "Sync request processed", "successful_sync_ids": all_successful_sync_ids}
        print(response_data)
        if errors:
            print(errors)
            response_data["errors"] = errors # Add errors to the response
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS) # 207 for partial success
        else:
            return Response(response_data, status=status.HTTP_200_OK)

@csrf_exempt 
def provide(request):
    if request.method == 'POST':
        from django.forms import model_to_dict
        from django.db.models import Q
        from core.models import BulkCampaign,Profile,Task,ScrapeTask,Audience
        
        data = json.loads(request.body)   
        
        method=data.get('method')

        print(data)

        task=Task.objects.all().filter(uuid=data['uuid'])
        print(task)
        if not task:
            return JsonResponse(status=500,data={'authorized':False})
        else:
            task=task[0]
        filters=data.get('filters')
        print(data)
        try:
            filters = data.get('filters')
            object_type = data.get('object_type')
            required_fields = data.get('required_fields')

            # Dynamically retrieve the model:
            try:
                model = apps.get_model('core', object_type)  # Replace 'your_app_name'
            except LookupError:  # Handle invalid app/model name
                return JsonResponse({"error": f"Model '{object_type}' not found in 'your_app_name'"}, status=400)

            queryset = model.objects.all()

            if filters:
                q, _, _ = json_to_django_q(filters, model)
                if q is None:
                    return JsonResponse({"error": "Invalid filter payload"}, status=400)
                queryset = queryset.filter(q)

          
        
            if data.get('lock_results'):
                from core.models import Lock
                lock_type=data.get('lock_type')
                exclude_ids=[]
                if lock_type=='data_point':
                    exclude_ids = Lock.objects.filter(
                            Q(model_name='profile',lock_type='service', locked_by_task__service=data.get('service')) |
                            Q(model_name='profile',lock_type='end_point', locked_by_task__end_point=data.get('end_point')) |
                            Q(model_name='profile',lock_type='data_point', locked_by_task__data_point=data.get('data_point'))
                        ).distinct().values_list('object_id', flat=True)
                elif lock_type=='service':
                    exclude_ids = Lock.objects.filter(model_name='profile',lock_type='service', locked_by_task__service=data.get('service')).distinct().values_list('object_id', flat=True)
                elif lock_type=='end_point':
                            exclude_ids = Lock.objects.filter(
                            Q(model_name='profile',lock_type='service', locked_by_task__service=data.get('service')) |
                            Q(model_name='profile',lock_type='end_point', locked_by_task__end_point=data.get('end_point')) ).distinct().values_list('object_id', flat=True)
                print(exclude_ids)
                queryset=queryset.exclude(id__in=exclude_ids)
                if lock_type:
                    for obj in queryset:
                       
                        obj.acquire_lock(task=task,lock_type=lock_type)
               
            results = []
            
            if data.get('count'):
                return JsonResponse(data={'data':[],'count':len(queryset)},status=200)
            if data.get('provide_for_profile_analysis'):
                results=[]
               
                from core.models import Post
                from django.db.models import Q
                profiles_list=queryset.filter(info__is_private=False).filter(info__profile_analysis__isnull=True).annotate(count=Count('username')).values_list('username',flat=True)
                if data.get('size'):
                    size=data.get('size')
                    profiles_list=profiles_list[0:size]
                for username in set(profiles_list):
                    posts=[]
                    profile=Profile.objects.all().filter(username=username)[0]
                    profile_info=model_to_dict(profile)
                    info=profile_info.pop('info',{})
                    profile_info
                    profile_info.pop('tasks')
                    from django.conf import settings
                    print('pp')
                    print(profile_info)
                    pict=False if type (profile_info['profile_picture'])==dict  or not profile_info['profile_picture']else settings.STORAGE_HOUSE_URL+profile_info['profile_picture']
                    print('passed')
                    profile_info['profile_picture']=pict
                    profile_posts=profile.posts.all()
                    
                    for i, post in enumerate(profile_posts):
                        post_text=''
                        post_medias=[]
                        try:
                            post_text=post.text
                            print(post_text)
                            if post_text:
                                post_text=post_text.content
                            
                        except Exception as e:
                            pass

                        post_media=post.medias.all()
                        for media in post_media:
                            if media.file_type=='vidoe':
                                continue
                            print('here')
                            post_medias.append(settings.STORAGE_HOUSE_URL+media.file_path)
                        

                        out={'text':post_text,'medias':post_medias}
                        posts.append(out)
                    results.append({'profile_info':profile_info,'posts':posts})
                return JsonResponse(data={'data':results},status=200)
            if data.get('size'):
                size=data.get('size')
                queryset=queryset[0:size]
            if data.get('delete'):
                if object_type=='lock':
                    count=len(queryset)
                    queryset.delete()
                    return JsonResponse(data={'data':[],'count':count,'deleted':True},status=200)
            print(len(queryset))
            print(required_fields)
            for obj in queryset:
                data_dict = {}
       
                if required_fields:
                    for field in required_fields:
                        try:
                            if "__" in field:  # Check if it's a JSONField lookup
                                field_parts = field.split("__")
                                json_field_name = field_parts[0]
                                nested_keys = field_parts[1:]
                                json_data = getattr(obj, json_field_name)

                                if json_data: # check if json data is not empty
                                    current_level = json_data
                                    for key in nested_keys:
                                        if isinstance(current_level, dict) and key in current_level:
                                            current_level = current_level[key]
                                        elif isinstance(current_level, list): # handle list in json field
                                            values = []
                                            for item in current_level:
                                                if isinstance(item, dict) and key in item:
                                                    values.append(item[key])
                                            current_level = values # update the current level
                                        else:
                                            current_level = None # handle missing keys in nested json field
                                            break
                                    if current_level is not None:
                                        data_dict[field] = current_level
                                    else:
                                        data_dict[field] = None # if nested key is missing in json field
                                else:
                                    data_dict[field] = getattr(obj, field)  # Regular field
                            else:
                                data_dict[field] = getattr(obj, field) # Regular field
                        except AttributeError:
                            continue
                            
                           
                        
                            

                
                                #return JsonResponse({"error": f"Field '{field}' not found on model '{model._meta.model_name}'"}, status=400) # added model name to error message
                else:  # Default behavior (include all fields)
                  
                    for field in [f.name for f in obj._meta.fields]:
                     
                        if type(getattr(obj, field))==dict:
                            pass
                            data_dict[field]=getattr(obj, field)
                        else:
                            data_dict[field] = getattr(obj, field)
                
                results.append(data_dict)

            #print(results)

            return JsonResponse({"data": results}, status=200)

        except Exception as e:
            print(f"An error occurred: {e}")
            return JsonResponse({"error": "An error occurred"}, status=500)  
        
from django.db import models

def serialize_related_fields(queryset, required_fields=None):
    """Serializes model instances, handling FK and M2M relationships."""
    results = []
    for obj in queryset:
        data_dict = {}

        if required_fields:
            for field in required_fields:
                try:
                    if "__" in field:  # JSONField or related field lookup
                        field_parts = field.split("__")
                        first_part = field_parts[0]  # Check if it is a related field
                        if "." in field: # Check if it is a related field
                            related_field_parts = field.split(".")
                            related_model_field = related_field_parts[-1] # the field to get from related model
                            related_field_path = "__".join(related_field_parts[:-1]) # the path to related model
                            related_obj = getattr(obj, related_field_path)

                            if related_obj: # if related object exists
                                if isinstance(related_obj, models.Model): # foreign key
                                    data_dict[field] = getattr(related_obj, related_model_field)
                                elif isinstance(related_obj.all(), models.QuerySet): # many to many
                                    related_data = []
                                    for related_item in related_obj.all():
                                        related_data.append(getattr(related_item, related_model_field))
                                    data_dict[field] = related_data
                                else:
                                    data_dict[field] = None # if not foreign key or m2m
                            else:
                                data_dict[field] = None # if related object does not exist
                        elif "." not in field and hasattr(obj, first_part): # Regular field
                            data_dict[field] = getattr(obj, field)
                        else: # JSONField lookup
                            json_field_name = field_parts[0]
                            nested_keys = field_parts[1:]
                            json_data = getattr(obj, json_field_name)

                            if json_data:  # Check if JSON data is not empty
                                current_level = json_data
                                for key in nested_keys:
                                    if isinstance(current_level, dict) and key in current_level:
                                        current_level = current_level[key]
                                    elif isinstance(current_level, list):  # Handle list in JSON field
                                        values = []
                                        for item in current_level:
                                            if isinstance(item, dict) and key in item:
                                                values.append(item[key])
                                        current_level = values  # Update the current level
                                    else:
                                        current_level = None  # Handle missing keys in nested JSON field
                                        break
                                if current_level is not None:
                                    data_dict[field] = current_level
                                else:
                                    data_dict[field] = None  # If nested key is missing in JSON field
                            else:
                                data_dict[field] = getattr(obj, field)  # Regular field
                    else:  # Default behavior (include all fields)
                        for field in [f.name for f in obj._meta.fields]:
                            data_dict[field] = getattr(obj, field)

                        for related_field in obj._meta.related_objects:  # Handle related fields
                            related_name = related_field.name
                            related_objs = getattr(obj, related_name)

                            if isinstance(related_objs, models.Manager):  # Many-to-Many
                                related_data = []
                                for related_obj in related_objs.all():
                                    related_data.append({f.name: getattr(related_obj, f.name) for f in related_obj._meta.fields})
                                data_dict[related_name] = related_data
                            elif isinstance(related_objs, models.Model):  # Foreign Key
                                data_dict[related_name] = {f.name: getattr(related_objs, f.name) for f in related_objs._meta.fields}

                except AttributeError:
                    if field in required_fields: # Only remove if the field is in required_fields
                        required_fields.remove(field)

        elif not required_fields: # if required fields is None
            print('not requ')
            for field in [f.name for f in obj._meta.fields]:
               
                if type(getattr(obj, field))==dict:
                    data_dict.update(**getattr(obj, field))
                else:
                    data_dict[field] = getattr(obj, field)

            for related_field in obj._meta.related_objects:  # Handle related fields
                related_name = related_field.name
                related_objs = getattr(obj, related_name)

                if isinstance(related_objs, models.Manager):  # Many-to-Many
                    related_data = []
                    for related_obj in related_objs.all():
                        related_data.append({f.name: getattr(related_obj, f.name) for f in related_obj._meta.fields})
                    data_dict[related_name] = related_data
                elif isinstance(related_objs, models.Model):  # Foreign Key
                    data_dict[related_name] = {f.name: getattr(related_objs, f.name) for f in related_objs._meta.fields}

        results.append(data_dict)
    return results             
""" def provide(request):
    print(request)
    if request.method == 'POST':
        from django.forms import model_to_dict
        from django.db.models import Q
        from core.models import BulkCampaign,Profile,Task,ScrapeTask,Audience
        
        data = json.loads(request.body)   
        
        method=data.get('method')

        data=data.get('data')

        

        print(data)
        filters=data.get('filters')

        object_type=data.get('object_type')

        if object_type=='profile':
            print(filters)
            external_key_filters=filters['external_key_filters']
            profiles=Profile.objects.all()
            for filter in external_key_filters:
                print(filter)
                if filter['name'] == 'campaign':
                    campaign=BulkCampaign.objects.all().filter(uuid=filter['uuid'])
                    print(campaign)
                    if campaign:
                        campaign_uuid=campaign[0].uuid
                        campaign_tasks=Task.objects.all().filter(ref_id=campaign_uuid)
                        profiles=profiles.filter(tasks__in=campaign_tasks)
                        print(profiles)
                elif filter['name'] =='scrape_task':
                    scrape_task=ScrapeTask.objects.all().filter(uuid=filter['uuid'])
                    if scrape_task:
                        scrape_task_uuid=scrape_task[0].uuid
                        scrape_task_tasks=Task.objects.all().filter(uuid=scrape_task_uuid)
                        profiles=profiles.filter(tasks__in=scrape_task_tasks)
                        print('profiles')
                elif filter['name'] =='audience':
                    audience=Audience.objects.all().filter(uuid=filter['uuid'])
                    print(audience)
                    if audience:
                        audience_uuid=audience[0].uuid
                        audience_tasks=Task.objects.all().filter(ref_id=audience_uuid)
                        profiles=profiles.filter(tasks__in=audience_tasks)
                        print(profiles)
                elif filter['name'] =='task':
                    if not type(filter['uuid'])==list:
                        uuids=[(filter['uuid'])]
                    else:
                        uuids=filter['uuid']
                    print(uuids)
                    task=Task.objects.all().filter(uuid__in=uuids)
                    print(task)
                    if task:
                        

                         profiles=profiles.filter(tasks__in=task)
                         print('**********************')
                         print(profiles)


            internal_key_filters=filters.get('internal_key_filters')
            if internal_key_filters:
                internal_key_filters=internal_key_filters[0]
                print(internal_key_filters)
            

                query = Q()
                query=json_to_django_q(internal_key_filters,Profile)
                for filter in internal_key_filters:
                    

            # Iterate over the filters and build the query dynamically
                    print(filter)
                    for field, value in filter.items():
                        # Handle special cases (e.g., range queries, boolean fields)
                        if field.endswith('__gt'):
                            query &= Q(**{field: value})
                        elif field.endswith('__lt'):
                            query &= Q(**{field: value})
                        elif field.endswith('__icontains'):
                            query &= Q(**{field: value})
                        elif isinstance(value, bool):  # Handle boolean fields
                            query &= Q(**{field: value})
                        else:
                            # Default to exact match
                            query &= Q(**{field: value})
                print(query) 
                print(query)
                profiles=profiles.filter(query)
                print(profiles)
            return JsonResponse(status=200,data={'data':list(profiles.values())})
from django.db import models """
from django.db.models import Q, Sum, F, Count, Avg, Max, Min  # Add other aggregations as needed

from django.db import models
from django.db.models import Q, Sum, F, Count, Avg, Max, Min  # Add other aggregations as needed

def json_to_django_q(payload, model):
    """Converts a JSON payload to a Django Q object for filtering.

    Handles nested conditions (OR, AND, EXCLUDE), dot notation for lookups,
    lists of values, and various aggregation functions.  Includes robust
    error handling and input validation.

    Args:
        payload (dict): The JSON payload containing filter conditions.
        model (Model): The Django model to query.

    Returns:
        tuple: (Q object, order_by fields, annotations) or (None, None, None) on error.
    """

    q_object = Q()
    order_by_fields = None
    annotations = None

    if not payload or not isinstance(payload, dict):
        return None, None, None  # Handle invalid payload
   
    try:
        for key, value in payload.items():
            if key in ("or_conditions", "and_conditions", "exclude"):
                if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
                    raise ValueError(f"'{key}' must be a list of dictionaries.")

                sub_q = Q()
                for condition in value:
                    condition_q = Q()
                    for k, v in condition.items():
                        field, lookup = k.split(".") if "." in k else (k, "exact")
                        lookup_operator = "__" + lookup 
                        filter_kwargs = {field + lookup_operator: v}
                        condition_q &= Q(**filter_kwargs)  # Combine within the condition

                    if key == "or_conditions":
                        sub_q |= condition_q
                    elif key == "and_conditions":
                        sub_q &= condition_q
                    elif key == "exclude":
                        sub_q |= condition_q
                        print(sub_q)

                if key == "or_conditions":
                    q_object |= sub_q
                elif key == "and_conditions":
                    q_object &= sub_q
                elif key == "exclude":
                    q_object &= ~sub_q
                    print(q_object)

            elif key == "order_by":
                if not isinstance(value, list):
                    raise ValueError("'order_by' must be a list.")

                order_by_fields = []
                for field_str in value:
                    prefix = "-" if field_str.startswith("-") else ""
                    field_name = field_str[1:] if field_str.startswith("-") else field_str

                    try:
                        model._meta.get_field(field_name)  # More robust field check
                    except models.FieldDoesNotExist:
                        raise ValueError(f"Invalid order_by field '{field_str}' for model '{model.__name__}'.")
                    else:
                        order_by_fields.append(f"{prefix}{field_name}")


            elif key == "annotations":
                if not isinstance(value, dict):
                    raise ValueError("'annotations' must be a dictionary.")

                annotations = {}
                for annotation_name, aggregation in value.items():
                    aggregation=eval(aggregation)
                    if not isinstance(aggregation, (Sum, Count, Avg, Max, Min, F)): # check if aggregation is valid
                        raise ValueError(f"Invalid aggregation function '{aggregation}' for annotation '{annotation_name}'.")
                    annotations[annotation_name] = aggregation
                q_object &= Q(**{f"{annotation_name}__isnull": False})

               

            else:  # Regular field lookups
                if "__" in key:
                    field, lookup =key.split(".") if "." in key else (key, "exact")
                else:
                    field, lookup = key.split(".") if "." in key else (key, "exact")
                if lookup == "equal":  # Add this check
                    lookup = "exact" 
                lookup_operator = "__" + lookup 
                #
                print(lookup_operator)
                print(field)
                if '__' in field:
                    field_name=field.split('__')[0]
                else:
                    field_name=field
                try:
                    model._meta.get_field(field_name)  # More robust field check
                except Exception as e:
                    continue
                print(lookup)
                print(value)
                if isinstance(value, list) and lookup != "in":  # List of values without 'in'
                    for v in value:
                        print(v)
                        filter_kwargs = {field + lookup_operator: v}
                        q_object &= Q(**filter_kwargs)
                else:
                    filter_kwargs = {field + lookup_operator: value}
                    q_object &= Q(**filter_kwargs)
        print(q_object)
        return q_object, order_by_fields, annotations

    except (ValueError, TypeError, AttributeError) as e:  # Catch potential errors
        print(f"Error processing payload: {e}")  # Log the error
        return None, None, None  # Return None on error
    """Converts a JSON payload to a Django Q object for filtering.

    Handles nested conditions (OR, AND, EXCLUDE), dot notation for lookups,
    lists of values, and various aggregation functions.  Includes robust
    error handling and input validation.

    Args:
        payload (dict): The JSON payload containing filter conditions.
        model (Model): The Django model to query.

    Returns:
        tuple: (Q object, order_by fields, annotations) or (None, None, None) on error.
    """

    q_object = Q()
    order_by_fields = None
    annotations = None

    if not payload or not isinstance(payload, dict):
        return None, None, None  # Handle invalid payload

    try:
        for key, value in payload.items():
            if key in ("or_conditions", "and_conditions", "exclude"):
                if not isinstance(value, list) or not all(isinstance(x, dict) for x in value):
                    raise ValueError(f"'{key}' must be a list of dictionaries.")

                sub_q = Q()
                for condition in value:
                    condition_q = Q()
                    for k, v in condition.items():
                        field, lookup = k.split(".") if "." in k else (k, "exact")
                        lookup_operator = "__" + lookup if lookup != "exact" and lookup != "isnull" else ""
                        filter_kwargs = {field + lookup_operator: v}
                        condition_q &= Q(**filter_kwargs)  # Combine within the condition

                    if key == "or_conditions":
                        sub_q |= condition_q
                    elif key == "and_conditions":
                        sub_q &= condition_q
                    elif key == "exclude":
                        sub_q &= ~condition_q

                if key == "or_conditions":
                    q_object |= sub_q
                elif key == "and_conditions":
                    q_object &= sub_q
                elif key == "exclude":
                    q_object &= ~sub_q

            elif key == "order_by":
                if not isinstance(value, list):
                    raise ValueError("'order_by' must be a list.")

                order_by_fields = []
                for field_str in value:
                    prefix = "-" if field_str.startswith("-") else ""
                    field_name = field_str[1:] if field_str.startswith("-") else field_str

                    try:
                        model._meta.get_field(field_name)  # More robust field check
                    except models.FieldDoesNotExist:
                        raise ValueError(f"Invalid order_by field '{field_str}' for model '{model.__name__}'.")

                    order_by_fields.append(f"{prefix}{field_name}")


            elif key == "annotations":
                if not isinstance(value, dict):
                    raise ValueError("'annotations' must be a dictionary.")

                annotations = {}
                for annotation_name, aggregation in value.items():
                    if not isinstance(aggregation, (Sum, Count, Avg, Max, Min, F)): # check if aggregation is valid
                        raise ValueError(f"Invalid aggregation function '{aggregation}' for annotation '{annotation_name}'.")
                    annotations[annotation_name] = aggregation

            elif "__" in key and key.startswith("json_field__"):
                json_field_name, lookup = key.split("__")[0], "__".join(key.split("__")[1:])
                try:
                    json_field = model._meta.get_field(json_field_name) # More robust field check
                except models.FieldDoesNotExist:
                    raise ValueError(f"Invalid JSONField '{json_field_name}' for model '{model.__name__}'.")
                # ... (JSONField handling - same logic as before)

            else:  # Regular field lookups
                field, lookup = key.split(".") if "." in key else (key, "exact")
                lookup_operator = "__" + lookup if lookup != "exact" and lookup != "isnull" else ""

                try:
                    model._meta.get_field(field)  # More robust field check
                except models.FieldDoesNotExist:
                    raise ValueError(f"Invalid field '{field}' for model '{model.__name__}'.")

                if isinstance(value, list) and lookup != "in":  # List of values without 'in'
                    for v in value:
                        filter_kwargs = {field + lookup_operator: v}
                        q_object &= Q(**filter_kwargs)
                else:
                    filter_kwargs = {field + lookup_operator: value}
                    q_object &= Q(**filter_kwargs)

        return q_object, order_by_fields, annotations

    except (ValueError, TypeError, AttributeError) as e:  # Catch potential errors
        print(f"Error processing payload: {e}")  # Log the error
        return None, None, None  # Return None on error
                        
""" def json_to_django_q(payload,model):
    from django.db.models import Q
    q_object = Q()
   
    for key, value in payload.items():
        if key == "or_conditions":
            or_conditions = [json_to_django_q(cond, model) for cond in value]
            q_object |= Q(*or_conditions)
        elif key == "and_conditions":
            and_conditions = [json_to_django_q(cond, model) for cond in value]
            q_object &= Q(*and_conditions)
        elif key == "exclude":
            exclude_conditions = [json_to_django_q(cond, model) for cond in value]
            q_object &= ~Q(*exclude_conditions)
        elif key == "order_by":
            order_by_fields = []
            for field_str in value:
                if field_str.startswith("-"):
                    order_by_fields.append(f"-{getattr(model, field_str[1:])}")
                else:
                    order_by_fields.append(getattr(model, field_str))
            continue  # Don't create Q objects for order_by
        elif key == "annotations":
        # Handle annotations (e.g., aggregations)
        # Example: {"total_amount": Sum("amount")}
            continue  # Don't create Q objects for annotations
        elif "__" in key and key.startswith("json_field__"):
        # Handle filtering within JSONField
            json_field_name, lookup = key.split("__")[0], "__".join(key.split("__")[1:])
            try:
                json_field = getattr(model, json_field_name)
            except AttributeError:
                raise ValueError(f"Invalid JSONField '{json_field_name}' for model '{model.__name__}'")

            if lookup == "exact":
                q_object &= Q(**{json_field.key(key.split("__")[1]): value})
            elif lookup == "in":
                q_object &= Q(**{json_field.key(key.split("__")[1]).in_bulk(value)})
            # Add more supported lookups for JSONField as needed
            else:
                raise ValueError(f"Unsupported lookup type for JSONField: '{lookup}'") 
        else:
            print(key)
            field, lookup = key.split(".") if "." in key else (key, "exact")
        
            if lookup == "exact":
                q_object &= Q(**{field: value})
            elif lookup == "in":
                q_object &= Q(**{field__in: value})
            elif lookup == "gt":
                q_object &= Q(**{field__gt: value})
            elif lookup == "gte":
                q_object &= Q(**{field__gte: value})
            elif lookup == "lt":
                q_object &= Q(**{field__lt: value})
            elif lookup == "lte":
                q_object &= Q(**{field__lte: value})
            elif lookup == "startswith":
                q_object &= Q(**{field__startswith: value})
            elif lookup == "endswith":
                q_object &= Q(**{field__endswith: value})
            elif lookup == "contains":
                q_object &= Q(**{field__contains: value})
            elif lookup == "icontains":
                q_object &= Q(**{field__icontains: value})
            elif lookup == "isnull":
                q_object &= Q(**{key.split('.')[0]+'__isnull': value}) 
            else:
                  q_object &= Q(**{field: value})

    return q_object
 """
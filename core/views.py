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

@csrf_exempt
def consume(request):
    if request.method == 'POST':
        from django.forms import model_to_dict
        
        data = json.loads(request.body)   
        
        method=data.get('method')
        print(data)
        for row in data.get('data'):
            print(row)
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
                """ for filter in internal_key_filters:
                    

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
                print(query) """
                print(query)
                profiles=profiles.filter(query)
                print(profiles)
            return JsonResponse(status=200,data={'data':list(profiles.values())})
                        
def json_to_django_q(payload,model):
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

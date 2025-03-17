import json
from datetime import timedelta
from django.core.management.base import BaseCommand


# ... (your other imports and the analysis/chart functions)

class Command(BaseCommand):
    help = 'Generates chart data from request logs and saves it to a PNG image file.'

    def handle(self, *args, **options):
        from core.models import Profile,Follow
        from django.conf import settings
        profiles=Profile.objects.all()
        for p in profiles:
            row=p.info
            update_fields=[ "gender",
            "country","city",
            "interests",
            "profile_analysis",
            "keywords",
            "phone_number",
            "email",
            "external_accounts",
            "type",
            "age",
            "bio",
            "category_name"
            "possible_buying_interests",
            "interests_and_lifestyle_patterns",
            "possible_buying_intent",
            "financial_and_economic_status",
            "religion",'is_private','account_type','show_account_transparency_details','id','rest_id','fbid_v2','is_unpublished','full_name','followers_count','followings_count','post_count','profile_pic','profile_picture']
            for key in list(row.keys()):
                print(key)
                print(row[key])
                if key =='id':
                    p.rest_id=row[key]
                    continue
                if key=='name' and len(row[key])>1:
                    
                    p.name=row[key]
                if key in update_fields:
                
                    if key=='profile_picture' or key=='profile_pic':
                        if row[key].get('storage_house_file_path'):
                            p.profile_picture=row[key]['storage_house_file_path']

                    elif type(row[key])==bool:
                        p.__setattr__(key,row[key])
                        
                    else:
                        if len(str(row[key]))>1:
                            p.__setattr__(key,row[key])
                            
                    

            from django.forms import model_to_dict
            print(model_to_dict(p))

            p.save()
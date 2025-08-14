def handle_instagram_profile(row,task):
    from core.models import Profile,Follow
    from django.conf import settings
    p=Profile.objects.all().filter(username=row.get('username'),service=row['service'])
    if len(p)>0:
        p=p[0]
    else:
        p=Profile(username=row.get('username'),service=row['service'])
    print(row)
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
    "religion",'is_private','account_type','show_account_transparency_details','rest_id','fbid_v2','is_unpublished','full_name','followers_count','followings_count','post_count','profile_pic','profile_picture']
    for key in list(row.keys()):
        if key =='id':
            p.rest_id=row[key]
            p.info[key]=row[key]
            continue
        
        
        if key =='followers_count':
            f_count=False
            if row.get('followers_count'):
                f_count=row.get('followers_count')
            elif row.get('follower_count'):
                f_count=row.get('follower_count')
            if f_count:
                p.followers_count=f_count
            continue
        if key =='followings_count':
            f_count=False
            if row.get('followings_count'):
                f_count=row.get('followings_count')
            elif row.get('following_count'):
                f_count=row.get('following_count')
            if f_count:
                p.followings_count=f_count
            
            continue
        if key =='post_count':
            f_count=False
            if row.get('media_count'):
                f_count=row.get('media_count')
            elif row.get('post_count'):
                f_count=row.get('post_count')
            if f_count:
                p.post_count=f_count
            continue
        
        if key=='name' and len(str(row[key]))>1:
            
            p.name=row[key]
            p.info[key]=row[key]
            continue
        if key in update_fields:
           
            if key=='profile_picture' :
                if row.get(key,{}):
                    import ast
                    if type(row.get(key))==str:
                        profile_picture=ast.literal_eval(row.get(key))
                    else: 
                        profile_picture=row.get(key)
                    if profile_picture.get('storage_house_file_path'):
                        p.profile_picture=profile_picture['storage_house_file_path']
                        p.info[key]=profile_picture['storage_house_file_path']

            elif type(row[key])==bool:
                p.__setattr__(key,row[key])
                p.info[key]=row[key]
                
            else:
                if len(str(row[key]))>1:
                    p.__setattr__(key,row[key])
                    p.info[key]=row[key]
                    
             

    from django.forms import model_to_dict
    print(model_to_dict(p))
    p.save()
    p.tasks.add(task)
    p.save()
    print(p.tasks.all())
    if row.get('follower_of'):
        follower_of=Profile.objects.all().filter(username=row['follower_of'])

        if follower_of:
            follower_of=follower_of[0]
        else:
            follower_of=Profile(username=row.get('follower_of'))
            follower_of.save()
       
        if not Follow.objects.filter(profile=p,following=follower_of):
            f=Follow(profile=p,following=follower_of)
            f.save()
            f.tasks.add(task)
            f.save()
    return p
                
        

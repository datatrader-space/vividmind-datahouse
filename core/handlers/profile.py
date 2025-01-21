def handle_instagram_profile(row,task):
    from core.models import Profile,Follow
    from django.conf import settings
    p=Profile.objects.all().filter(username=row.get('username'),service=row['service'])
    if len(p)>0:
        p=p[0]
    else:
        p=Profile(username=row.get('username'),service=row['service'])
    update_fields=['gender','country','type','is_private','account_type','show_account_transparency_details','id','fbid_v2','is_unpublished','full_name','follwowers_count','following_count','post_count','profile_pic','profile_picture']
    for key in list(row.keys()):
        if key in update_fields:
            print(type(row[key]))
            if key=='profile_picture' or key=='profile_pic':
                if row[key].get('storage_house_file_path'):
                    p.profile_picture=row[key]['storage_house_file_path']
                else:
                    p.info[key]=row[key]
            elif type(row[key])==bool:
                p.info[key]=row[key]
            else:
                if len(str(row[key]))>1:

                    p.info[key]=row[key]
             

       

    print(p.info)
    p.save()
    p.tasks.add(task)
    p.save()
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
                
        

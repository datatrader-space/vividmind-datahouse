def handle_instagram_post(row,task):
    from core.models import Profile,Post,PostMedia,PostText
    from django.conf import settings
    if not row.get('shortcode'):
        if not row.get('code'):
            return False
        else:
            pass
    else:
        row['code']=row['shortcode']
    p=Post.objects.all().filter(code=row.get('code'),service=row['service'])
    if len(p)>0:
        p=p[0]
    else:
        p=Post(code=row.get('code'),service=row['service'])
        
    update_fields=['id','code','fbid_v2','downloaded_medias','pk','like_and_view_counts_disabled','is_post_live_clips_media','commerciality_status',
                   'ntegrity_review_decision','filter_type','caption','coauthor_producers','music_metadata','b_aggregated_like_count','fb_aggregated_comment_count',
                   'has_high_risk_gen_ai_inform_treatment','comment_count','like_count','media_type','location'
                   ]
    
    for key in ['owner','user']:
        if row.get(key):
            from core.handlers.profile import handle_instagram_profile
            row[key].update({'service':row['service']})
            owner=handle_instagram_profile(row[key],task)
            if owner:
                p.profile=owner
                p.save()
                break
            else:
                print('ownr nopt created')
    else:
        print('Owner not found')
    l=False
    if row.get('location'):
        data={'info':{}}
        fields=['pk','lat','lng','name']
        location=row['location']
        for  key in location.keys():

            if key in fields:
               
                   data[key]=location[key]

            else:
                data['info'][key]=location[key]
        if data.get('pk'):
            data['rest_id']=data.get('pk')
            data['service']='instagram'
            data.pop('pk')
            from core.models import Location
            l=Location.objects.all().filter(rest_id=data['rest_id'])
            if not l:
                l=Location(**data)
                l.save()
            else:
                l=l[0]
            
        else:
           l=False

    for key in list(row.keys()):
        if key =='shortcode':
            row['code']=row['shortcode']
        if key in update_fields:
            
                

            if key=='downloaded_medias':
                if  p.medias.all():
                    print('post has already medias')
                    print(p.medias.all())
                    continue
                for media in row[key]:
                    print(media)
                    if media.get('storage_house_file_path'):
                        
                        pm=PostMedia(post=p,file_path=media['storage_house_file_path'],file_type=media['media_type'])
                        pm.save()
        
            elif key=='caption':
                if row.get('caption'):
                    
                    print(p)
                    if PostText.objects.all().filter(post=p):
                        continue
                    cap=PostText()
                    cap.content=row['caption']['text']
                    cap.post=p
                    cap.save()
                    cap.tasks.add(task)
            elif type(row[key])==bool:
                p.info[key]=row[key]
            else:
                if len(str(row[key]))>=1:

                    p.info[key]=row[key]
        else:
            row.pop(key)
    if l:
        p.location=l
    p.tasks.add(task)
    p.save()
   
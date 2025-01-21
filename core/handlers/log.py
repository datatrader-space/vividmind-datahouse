from core.models import Log,Task
def handle_log(log,task):
    required_fields = ['type',  'task', 'service']

    # Check for missing or empty required fields
    for field in required_fields:
        if field not in log or not log.get(field):
            raise ValueError(f"Missing or empty required field: {field}")

    # Get or create Task object 
    try:
        task = Task.objects.get(uuid=log.get('task'))
    except Task.DoesNotExist:
        task = Task.objects.create(uuid=log.get('task'), name=f"Task {log.get('task')}") 

    # Extract relevant fields
    log_fields = {
        'type': log.get('type'),
        'bot_username': log.get('bot_username'),
        'task': task, 
        'service': log.get('service'),
        'run_id': log.get('run_id'),
        'datetime':log.get('datetime')
    }

    # Create Log object
    try:
        log_obj = Log(**log_fields)
        log_obj.save()
        return log_obj
    except Exception as e:
        raise ValueError(f"Error creating Log object: {e}") 
    
from core.models import Task,RequestLog
import json
def create_request_log(payload):
    """
    Creates a RequestLog object from the given payload.

    Args:
        payload (dict): The payload containing the request log data.

    Returns:
        RequestLog: The created RequestLog object.

    Raises:
        ValueError: If any of the required fields are missing in the payload.
    """

    required_fields = ['datetime', 'request_record_type', 'service', 
                      'end_point', 'url', 'r_type', 'status_code']

    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    # Fetch or create the associated Task
    task_id = payload.get('task') 
    if task_id:
        try:
            task = Task.objects.get(uuid=task_id)
        except Task.DoesNotExist:
            
    
            task = Task.objects.create(uuid=task_id) 

    try:
        # Attempt to load the data as JSON
        data = json.loads(payload.get('data', '{}')) 
    except json.JSONDecodeError:
        # If JSON decoding fails, store the raw data in the text field
        data = {}
        data_text = payload.get('data', '') 
    else:
        data_text = None  # Clear the text field if JSON parsing succeeds

    # Create the RequestLog object
    request_log = RequestLog(
        datetime=payload['datetime'],
        request_record_type=payload['request_record_type'],
        service=payload['service'],
        end_point=payload['end_point'],
        data_point=payload.get('data_point', ''), 
        url=payload['url'],
        r_type=payload['r_type'],
        bot_username=payload.get('bot_username', ''),
        task=task,
        logged_in=payload.get('logged_in', False),
        params=payload.get('params', {}),
        data=data, 
        data_text=data_text, 
        status_code=payload['status_code'],
    )
    request_log.save()

    return request_log
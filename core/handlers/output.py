from core.models import Task,RequestLog,Output
import json
def handle_output(payload):
    if payload.get('method')=='create':
        return create_output(payload)
    if payload.get('method')=='update':
        return update_output(payload)
def create_output(payload):
    """
    Creates a RequestLog object from the given payload.

    Args:
        payload (dict): The payload containing the request log data.

    Returns:
        RequestLog: The created RequestLog object.

    Raises:
        ValueError: If any of the required fields are missing in the payload.
    """

    required_fields = ['task', 'output_data']

    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    # Fetch or create the associated Task
    task_id = payload.get('task') 
    if task_id:
        try:
            task = Task.objects.get(uuid=task_id)
        except Task.DoesNotExist:
            raise ValueError(f"Task with ID {task_id} not found.")
    else:
        task = Task.objects.create() 

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
    output=Output.objects.all().filter(task)
    output= Output(
        output_data=payload.get('data'),
        run_id=payload.get('run_id'),
        task=task,
    )
    output.save()
    

    return output

def update_output(payload):
    if payload.get('output_uuid'):
        output=Output.objects.all().filter(uuid=payload.get('uuid'))
        if output:
            if payload.get('consumed_by'):
                task=Task.objects.all().filter(uuid=payload.get('task'))
                if task:
                    output.consumed_by.add(Task)
                    return True
    return False
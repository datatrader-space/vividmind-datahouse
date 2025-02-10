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

    required_fields = ['task_uuid', 'output_data']
    print('i was ')
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    # Fetch or create the associated Task
    task_id = payload.get('task_uuid') 
    if task_id:
        try:
            task = Task.objects.get(uuid=task_id)
        except Task.DoesNotExist:
            raise ValueError(f"Task with ID {task_id} not found.")
    else:
        task = Task.objects.create(uuid=task_id)
        task.save() 

  


    output= Output(
        output_data=payload.get('output_data'),
        run_id=payload.get('run_id'),
        block_name=payload.get('block_name',''),
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
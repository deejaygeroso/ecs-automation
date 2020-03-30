import boto3
import pprint
import os

region = 'us-west-1'
clusterName = 'mail'
client = boto3.client('ecs', region_name=region)

def lambda_handler(event, context):
    # Get all the list of currently RUNNING task. Only 1 expected task is expected.
    response = client.list_tasks(
        cluster=clusterName,
        desiredStatus='RUNNING',
        family=clusterName,
    )
    # Get the Amazon Resource Name (ARN) for the current RUNNING task to be deleted.
    if response['taskArns']:
        currentRunningTaskARN = response['taskArns'][0]

        # Stop currently running task.
        response = client.stop_task(
            cluster=clusterName,
            reason='Will be replaced with a new updated task.',
            task=currentRunningTaskARN,
        )

        print 'Current running task is now closed for revision.'

    # Create a new task revision.
    response = client.register_task_definition(
        containerDefinitions=[
            {
                'cpu': 256,
                'essential': True,
                'image': '330345832654.dkr.ecr.us-west-1.amazonaws.com/mail-app',
                'name': 'mail-app',
                'memory': 256,
            },
            {
                'cpu': 256,
                'essential': True,
                'image': '330345832654.dkr.ecr.us-west-1.amazonaws.com/mail-nginx',
                'links': [
                    'mail-app'
                ],
                'memory': 256,
                'name': 'mail-nginx',
                'portMappings': [
                    {
                        'containerPort': 80,
                        'hostPort': 80,
                        'protocol': 'tcp'
                    },
                ]
            },
        ],
        family=clusterName,
        networkMode='bridge',
    )

    # Get the lastest task definition revision (e.g.: mail:15).
    taskDefinitionRev = response['taskDefinition']['family'] + ':' + str(response['taskDefinition']['revision'])

    # run newly revisioned task.
    response = client.run_task(
        cluster=clusterName,
        taskDefinition=taskDefinitionRev,
    )

    print 'New task revision is now running.'

    # Note: There has to be a current running service for this to work.
    # Update current running service.
    response = client.update_service(
        cluster=clusterName,
        deploymentConfiguration={
            'maximumPercent': 200,
            'minimumHealthyPercent': 50
        },
        desiredCount=1,
        service=clusterName,
        taskDefinition=taskDefinitionRev,
    )

    print 'Service updated.'

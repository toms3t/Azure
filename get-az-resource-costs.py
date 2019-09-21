import os
import json
from datetime import datetime
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient

WEST_US = "westus"
GROUP_NAME = "Training"


# Manage resources and resource groups - create, update and delete a resource group,
# deploy a solution into a resource group, export an ARM template. Create, read, update
# and delete a resource
#
# This script expects that the following environment vars are set:
#
# AZURE_TENANT_ID: with your Azure Active Directory tenant id or domain
# AZURE_CLIENT_ID: with your Azure Active Directory Application Client ID
# AZURE_CLIENT_SECRET: with your Azure Active Directory Application Secret
# AZURE_SUBSCRIPTION_ID: with your Azure Subscription Id
#


def run_example():
    """Resource Group management example."""
    #
    # Create the Resource Manager Client with an Application (service principal) token provider
    #
    subscription_id = ""  # your Azure Subscription Id

    credentials = ServicePrincipalCredentials(
        client_id='',
        secret='',
        tenant='',
    )

    client = ResourceManagementClient(credentials, subscription_id)

    #
    # Managing resource groups
    #
    resource_group_params = {"location": "westus"}

    # List Resource Groups
    print("List Resource Groups")
    for item in client.resource_groups.list():
        print_item(item)

    # List Resources within the group
    print("List all of the resources within the group")
    for item in client.resources.list_by_resource_group(GROUP_NAME):
        print_item(item)

    print("\n\n")
    
    login = os.popen('az login')
    consumption_raw = os.popen('az consumption budget show --budget-name standard').read()
    consumption_clean = json.loads(consumption_raw)
    current_spend = consumption_clean['currentSpend']['amount']
    print('Current Spend: ', current_spend)



def print_item(group):
    """Print a ResourceGroup instance."""
    print("\tName: {}".format(group.name))
    print("\tId: {}".format(group.id))
    print("\tLocation: {}".format(group.location))
    print("\tTags: {}".format(group.tags))
    print_properties(group.properties)


def print_properties(props):
    """Print a ResourceGroup properties instance."""
    if props and props.provisioning_state:
        print("\tProperties:")
        print("\t\tProvisioning State: {}".format(props.provisioning_state))
    print("\n\n")


if __name__ == "__main__":
    run_example()

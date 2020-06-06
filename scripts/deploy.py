import boto3
import json
import os
import re
import copy

#DEBUG
os.environ['Bucket']         = 'sssn-5007'
os.environ['KeyPrefix']      = 'sssn'
os.environ['TrackingTable']  = 'TrackingTable'
os.environ['Environment']    = 'dev'
#DEBUG END

s3client = boto3.client('s3')
orgclient = boto3.client('organizations')
cfnclient = boto3.client('cloudformation')

def handler ( event, context ):
  config     = read_json_object( os.environ['Bucket'], f"{os.environ['KeyPrefix']}/config.json" )
  template   = build_template( config )
  stack_name = f"ServiceCatalog-Networks-{os.environ['Environment']}"
  try:
    response = cfnclient.describe_stacks( StackName=stack_name )
  except:
    """Nothing Happens"""
  existing = response['Stacks'][0]
  if existing:
    cfnclient.update_stack(
      StackName    = stack_name,
      TemplateBody = json.dumps(template, indent=2),
      OnFailure    = 'ROLLBACK'
    )
  else:
    cfnclient.create_stack(
      StackName    = stack_name,
      TemplateBody = json.dumps(template, indent=2),
      OnFailure    = 'DELETE'
    )

def build_template ( config ):
  snippets     = read_json_object( os.environ['Bucket'], f"{os.environ['KeyPrefix']}/templates/snippets.json" )
  portfolios   = {}
  networks     = {}
  base_template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {}
  }
  for network in config['networks']:
    accounts = enumerate_deployment_targets( network['deployment'] )
    base_template['Resources'].update( factor_snippet( 'Product', snippets, network, None) )
    for account in accounts:
      if account not in portfolios:
        portfolios[account] = []
        base_template['Resources'].update( factor_snippet( 'Portfolio', snippets, network,  account) )
        base_template['Resources'].update( factor_snippet( 'PortfolioShare', snippets, network, account ) )
      if network['id'] not in portfolios[account]:
        portfolios[account].append(network['id'])
        base_template['Resources'].update( factor_snippet( 'ProductAssociation', snippets, network, account ) )
        base_template['Resources'].update( factor_snippet( 'StackSetConstraint', snippets, network, account ) )
  return base_template

def factor_snippet ( resourcetype, snippets, network, account ):
  snip = {}
  if resourcetype == "Product":
    resource_name = f"NewVPC{network['id']}"
    template_url = f"https://{os.environ['Bucket']}.s3.amazonaws.com/{network['vpc_template_path']}"
    snip[resource_name] = copy.deepcopy( snippets[resourcetype] )
    snip[resource_name]['Properties']['Name'] = resource_name
    snip[resource_name]['Properties']['ProvisioningArtifactParameters'][0]['Info']['LoadTemplateFromURL'] = template_url
  if resourcetype == "ProductAssociation":
    resource_name = f"ProductAssociation{network['id']}{account}"
    snip[resource_name] = copy.deepcopy( snippets[resourcetype] )
    snip[resource_name]["Properties"]["PortfolioId"]["Ref"] = f"NetworkPortfolio{account}"
    snip[resource_name]["Properties"]["ProductId"]["Ref"]   = f"NewVPC{network['id']}"
  if resourcetype == "Portfolio":
    resource_name = f"NetworkPortfolio{account}"
    snip[resource_name] = copy.deepcopy( snippets[resourcetype] )
    snip[resource_name]["Properties"]["DisplayName"] = resource_name
  if resourcetype == "PortfolioShare":
    resource_name = f"PortfolioShare{account}"
    snip[resource_name] = copy.deepcopy( snippets[resourcetype] )
    snip[resource_name]["Properties"]["AccountId"]          = account
    snip[resource_name]["Properties"]["PortfolioId"]["Ref"] = f"NetworkPortfolio{account}"
  if resourcetype == "StackSetConstraint":
    resource_name = f"StackSetConstraint{network['id']}{account}"
    snip[resource_name] = copy.deepcopy( snippets[resourcetype] )
    snip[resource_name]["DependsOn"] = f"ProductAssociation{network['id']}{account}"
    snip[resource_name]["Properties"]["PortfolioId"]["Ref"] = f"NetworkPortfolio{account}"
    snip[resource_name]["Properties"]["ProductId"]          = { "Ref": f"NewVPC{network['id']}" }
    snip[resource_name]["Properties"]["RegionList"]         = network['deployment']['available_regions']
    snip[resource_name]["Properties"]["AdminRole"]          = { "Sub": "arn:aws:iam::${AWS::AccountId}:role/service-role/AWSControlTowerStackSetRole"}
    snip[resource_name]["Properties"]["ExecutionRole"]      = { "Sub": "arn:aws:iam::${AWS::AccountId}:role/service-role/AWSControlTowerExecution"}
    snip[resource_name]["Properties"]["AccountList"].append(account)
  return snip

def read_json_object ( bucket, key ):
  result = s3client.get_object(Bucket=bucket, Key=key)
  text = result['Body'].read().decode()
  return json.loads(text)

def enumerate_deployment_targets ( deployment ):
  target_accounts = []
  if deployment['organization']:
      org_accounts = [a['Id'] for a in orgclient.list_accounts()['Accounts']]
      for account in org_accounts:
        if account not in target_accounts:
          target_accounts.append(account)
  for ou in deployment['ou_list']:
    ou_accounts = orgclient.list_accounts_for_parent(ParentId=ou)
    for account in ou_accounts['Accounts']:
      if account['Id'] not in target_accounts:
        target_accounts.append(account['Id'])
  for account in deployment['account_list']:
    if account not in target_accounts:
        target_accounts.append(account)
  return target_accounts

#DEBUG
handler ( None, None)
#DEBUG END
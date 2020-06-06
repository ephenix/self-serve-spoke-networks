import os
import zipfile

bucket_name = "sssn-5007"
base_dir = os.path.dirname(__file__)

if os.path.exists(  os.path.join( base_dir, "scripts/deploy.zip" ) ):
  os.remove(os.path.join( base_dir, "scripts/deploy.zip") )
deployzip = zipfile.ZipFile( os.path.join( base_dir, "scripts/deploy.zip" ), "w" )
deployzip.write( os.path.join( base_dir, "scripts/deploy.py" ), "deploy.py" )
deployzip.close()

if os.path.exists(  os.path.join( base_dir, "scripts/dynamic_cidr.zip" ) ):
  os.remove(  os.path.join( base_dir, "scripts/dynamic_cidr.zip" ) )
cidrzip = zipfile.ZipFile( os.path.join( base_dir, "scripts/dynamic_cidr.zip" ), "w" )
cidrzip.write( os.path.join( base_dir, "scripts/dynamic_cidr.py" ), "dynamic_cidr.py" )
cidrzip.write( os.path.join( base_dir, "scripts/cfnresponse.py" ), "cfnresponse.py" )
cidrzip.close()

os.system(f"aws s3 sync {base_dir}/ s3://{bucket_name}/sssn/ --delete")

main_url = f"https://{bucket_name}.s3.amazonaws.com/sssn/templates/self-serve-spoke-networks.json"

print(f"https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL={main_url}")
os.system(f'explorer "https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL={main_url}"')
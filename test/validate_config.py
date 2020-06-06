import json
import os
from jsonschema import validate

def handler ( event, context ):
  config = event['config']
  schema = event['schema']
  validate( instance=config, schema=schema )
  return True


def local_test():
  workingdir = os.path.dirname(__file__)
  configpath = os.path.join(workingdir, "../config.json")
  schemapath = os.path.join(workingdir, "./schema.json")

  with open(configpath) as f:
    config = json.load(f)
  with open(schemapath) as f:
    schema = json.load(f)

  event = {
    "config": config,
    "schema": schema
  }

  handler( event, None)

local_test()
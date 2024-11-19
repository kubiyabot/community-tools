import os
import pytest

def test_environment_variables():
    os.environ['APPROVAL_SLACK_CHANNEL'] = "C123456"
    os.environ['MAX_TTL'] = "30d"
    os.environ['GRACE_PERIOD'] = "5h"
    os.environ['TF_MODULES_URLS'] = "https://github.com/terraform-aws-modules/terraform-aws-vpc"

    assert os.getenv('APPROVAL_SLACK_CHANNEL') == "C123456"
    assert os.getenv('MAX_TTL') == "30d"
    assert os.getenv('GRACE_PERIOD') == "5h"
    assert os.getenv('TF_MODULES_URLS') == "https://github.com/terraform-aws-modules/terraform-aws-vpc"

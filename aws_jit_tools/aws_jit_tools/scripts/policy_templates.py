def s3_read_only_policy(buckets):
    """Generate S3 read-only policy for specified buckets."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket}" for bucket in buckets
                ] + [
                    f"arn:aws:s3:::{bucket}/*" for bucket in buckets
                ]
            }
        ]
    }

def s3_full_access_policy(buckets):
    """Generate S3 full access policy for specified buckets."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket}" for bucket in buckets
                ] + [
                    f"arn:aws:s3:::{bucket}/*" for bucket in buckets
                ]
            }
        ]
    } 
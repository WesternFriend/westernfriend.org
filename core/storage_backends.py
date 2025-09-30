from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage  # type: ignore


class StaticStorage(S3StaticStorage):
    location = "static"
    default_acl = "public-read"
    file_overwrite = True


class MediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = "public-read"
    file_overwrite = False

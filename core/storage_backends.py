from storages.backends.s3boto3 import S3ManifestStaticStorage


class StaticStorage(S3ManifestStaticStorage):
    location = "static"
    default_acl = "public-read"
    file_overwrite = True


class MediaStorage(S3ManifestStaticStorage):
    location = "media"
    default_acl = "public-read"
    file_overwrite = False

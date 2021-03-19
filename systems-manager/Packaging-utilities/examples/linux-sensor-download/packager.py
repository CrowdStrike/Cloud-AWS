import argparse
import hashlib
import json
import logging
import os
import sys
import time
import zipfile
from functools import cached_property
from logging.handlers import RotatingFileHandler
from os.path import basename

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
# handler = logging.StreamHandler()
handler = RotatingFileHandler("./s3-bucket/packager.log", maxBytes=20971520, backupCount=5)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

PATH_TO_BUCKET_FOLDER = './s3-bucket/'
PACKAGE_DESCRIPTION = 'CrowdStrike custom Install Package'
INSTALLER_VERSION = '1.0'
OS_LIST = ['windows','linux']



class SSMPackageUpdater:
    def __init__(self, region_name):
        self.region = region_name

    def update(self, package_name, file_to_upload):

        with open(file_to_upload) as openFile:
            documentContent = openFile.read()
        self._doc_update_or_create(Content=documentContent,
                                   Attachments=[
                                       {
                                           'Key': 'SourceUrl',
                                           'Values': [
                                               'https://' + s3bucket + '.s3-' + self.region + '.amazonaws.com/falcon',
                                           ]
                                       },
                                   ],
                                   Name=package_name,
                                   DocumentType='Package',
                                   DocumentFormat='JSON')

        print('Created ssm package {}:'.format(package_name))

    def _doc_update_or_create(self, **kwargs):
        if self._doc_exists(kwargs['Name']):
            self._doc_update(**kwargs)
        else:
            self._client.create_document(**kwargs)

    def _doc_exists(self, package_name):
        try:
            current_doc = self._client.get_document(Name=package_name)
        except self._client.exceptions.InvalidDocument:
            current_doc = {}
        return current_doc

    def _doc_update(self, **kwargs):
        del kwargs['DocumentType']
        kwargs['DocumentVersion'] = '$LATEST'
        try:
            updated = self._client.update_document(**kwargs)
        except self._client.exceptions.DuplicateDocumentContent:
            print("AWS SSM Package is already up to date with the latest version")
            return
        except self._client.exceptions.DocumentVersionLimitExceeded:
            self._doc_cleanup_versions(kwargs['Name'])
            updated = self._client.update_document(**kwargs)

        self._client.update_document_default_version(Name=kwargs['Name'],
                                                     DocumentVersion=updated['DocumentDescription']['DocumentVersion'])

    def _doc_cleanup_versions(self, package_name):
        for version in self._client.list_document_versions(Name=package_name)['DocumentVersions']:
            if version['IsDefaultVersion']:
                continue
            self._client.delete_document(Name=package_name, DocumentVersion=version['DocumentVersion'])

    @cached_property
    def _client(self):
        return boto3.client('ssm', region_name=self.region)


class S3BucketUpdater:
    def __init__(self, region_name):
        self.region = region_name

    def update(self, bucket_name, files):
        if not self._bucket_exists(bucket_name):
            self._create_bucket(bucket_name)
        for f in files:
            file_path = PATH_TO_BUCKET_FOLDER + f
            self._upload_file(file_path, bucket_name, "falcon/" + f)

    def _bucket_exists(self, bucket_name):
        """
        Checks that the S3 bucket exists in the region
        :param bucket_name: The name of the S3 bucket
        :return: True or False
        """
        try:
            response = self._client.list_buckets()
        except ClientError as e:
            print('Error listing buckets {}'.format(e))

        # Output True if bucket exists

        for bucket in response['Buckets']:
            if bucket_name == bucket["Name"]:
                print('Bucket already exists:')
                return True
        return False

    def _create_bucket(self, bucket_name):
        """Create an S3 bucket

        :param bucket_name: Bucket to create
        :return: True if bucket created, else False
        """

        print('Creating bucket:')
        location = {'LocationConstraint': self.region}
        self._client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)

    def _upload_file(self, file_name, bucket, object_name=None):
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        try:
            start_time = time.time()
            print('Uploading file {}:'.format(file_name))
            content = open(file_name, 'rb')
            self._client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=content
            )
            print("Successfully finished uploading files to s3 bucket. Took {}s".format(
                time.time() - start_time))
        except Exception as e:
            print('Upload error {}'.format(e))
            return False
        return True

    @cached_property
    def _client(self):
        return boto3.client('s3', region_name=self.region)


class DistributorPackager:
    def build(self, mappings_file):
        dirs = set()
        files = set()
        arch = set()

        installer_list = self._parse_mappings(mappings_file)
        dir_list = os.listdir()

        for os_type in OS_LIST:
            for installer in installer_list[os_type]:
                dirs.add(installer['dir'])
                files.add(installer['file'])

        folders_exist = all(item in dir_list for item in dirs)
        if not folders_exist:
            print('Check agent list file - Required directories do not exist')
            sys.exit(1)
        for dir in dirs:
            self._create_zip_files(dir)
        hashes_list = self._get_digest(files)
        self._generate_manifest(installer_list, hashes_list)
        files.add('manifest.json')
        return files

    @classmethod
    def _parse_mappings(cls, filename):
        """
        :param filename: Name of the file
        :return: Returns a dictionary containing required configuration data
        """
        with open(filename, 'rb') as fh:
            json_data = json.loads(fh.read())
        return json_data

    def _generate_manifest(self, zip_distros_meta_list, hashes):
        """
        Generates the manifest.json file required to create the ssm document
        :param installer_list: List containing key value pairs required to construct the file
        :param hashes: list of dictionary items {filename : sha256hash}
        :return:
        """
        manifest_dict = {}
        manifest_packages_meta = {}
        manifest_dict = {"schemaVersion": "2.0", "publisher": "Crowdstrike Inc.", "description": PACKAGE_DESCRIPTION,
                         "version": INSTALLER_VERSION}
        manifest_files_meta = {}
        for os_type in OS_LIST:
            for each_zip_distro_meta in zip_distros_meta_list[os_type]:
                name = each_zip_distro_meta['name']
                arch_type = each_zip_distro_meta['arch_type']
                version = each_zip_distro_meta['major_version']
                if not len(each_zip_distro_meta['minor_version']) == 0:
                    version = version + "." + each_zip_distro_meta['minor_version']

                if name in manifest_packages_meta:
                    pass
                else:
                    manifest_packages_meta[name] = {}

                if version in manifest_packages_meta[name]:
                    pass
                else:
                    manifest_packages_meta[name][version] = {}

                if arch_type in manifest_packages_meta[name][version]:
                    pass
                else:
                    manifest_packages_meta[name][version][arch_type] = {}

                manifest_packages_meta[name][version][arch_type] = {'file': each_zip_distro_meta['file']}

                # manifest_files_meta[each_zip_distro_meta['zip_name']] = {
                #     'checksums': {'sha256': each_zip_distro_meta['sha256']}}

        try:
            manifest_dict["packages"] = manifest_packages_meta
            obj = {}
            for hash in hashes:
                for k, v in hash.items():
                    obj.update({k: {'checksums': {"sha256": v}}})
            print(obj)
            file_list = {"files": obj}
            manifest_dict.update(file_list)
        except Exception as e:
            print('Exception {}'.format(e))
        try:
            with open((PATH_TO_BUCKET_FOLDER + 'manifest.json'), 'w') as file:
                file.write(json.dumps(manifest_dict))
        except Exception as e:
            print(e)

    def _create_zip_files(self, dir):
        zipf = zipfile.ZipFile(PATH_TO_BUCKET_FOLDER + dir + '.zip', 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk(dir + '/'):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, basename(file_path))
        zipf.close()

    def _get_digest(self, files):
        """
        Generate sha256 of hash
        :param files:
        :return:
        """
        hashes = []
        for file in files:
            file_path = PATH_TO_BUCKET_FOLDER + file
            with open(file_path, 'rb') as f:
                bytes = f.read()  # read entire file as bytes
                readable_hash = hashlib.sha256(bytes).hexdigest()
                hashes.append({file: readable_hash})
        return hashes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create and upload Distributor packages to the AWS SSM')
    parser.add_argument('-r', '--aws_region', help='AWS Region')
    parser.add_argument('-p', '--package_name', help='Package Name')
    parser.add_argument('-b', '--s3bucket', help='Package Name')

    args = parser.parse_args()

    region = args.aws_region
    package_name = args.package_name
    s3bucket = args.s3bucket

    files = DistributorPackager().build('agent_list.json')

    if region is None or s3bucket is None:
        print(
            "Skipping AWS upload: please provide --aws_region, --ssm_automation_doc_name, and --s3bucket command-line "
            "options for upload")
        print("Package has been built successfully.")
    elif region and s3bucket and package_name is None:
        S3BucketUpdater(region).update(s3bucket, files)
    elif region and s3bucket and package_name:
        S3BucketUpdater(region).update(s3bucket, files)
        SSMPackageUpdater(region).update(package_name, PATH_TO_BUCKET_FOLDER + "manifest.json")
    else:
        print("Nothing to do ... specify region + bucket or region + bucket + package_name")

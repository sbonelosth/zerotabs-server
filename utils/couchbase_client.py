import os
from dotenv import load_dotenv
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.exceptions import CouchbaseException
from datetime import timedelta

load_dotenv()

class CouchbaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CouchbaseClient, cls).__new__(cls)
            cls._instance.init_connection()
        return cls._instance

    def init_connection(self):
        try:
            conn_str = os.getenv("COUCHBASE_CONN_STRING")
            username = os.getenv("COUCHBASE_USERNAME")
            password = os.getenv("COUCHBASE_PASSWORD")
            bucket_name = os.getenv("COUCHBASE_BUCKET", "b0")

            auth = PasswordAuthenticator(username, password)
            self.cluster = Cluster(conn_str, ClusterOptions(auth))
            self.cluster.wait_until_ready(timedelta(seconds=10))

            self.bucket = self.cluster.bucket(bucket_name)

            print(f"✅ Connected to Couchbase, bucket: {bucket_name}")
        except CouchbaseException as e:
            print(f"❌ Couchbase connection failed: {e}")
            raise

    def get_collection(self, scope_name, collection_name):
        scope = self.bucket.scope(scope_name)
        return scope.collection(collection_name)

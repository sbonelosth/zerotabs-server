import os
from dotenv import load_dotenv
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from datetime import timedelta

def test_couchbase_connection():
    try:
        print("🔄 Connecting to Couchbase...")

        # Load .env variables
        load_dotenv()
        conn_str = os.getenv("COUCHBASE_CONN_STRING")
        username = os.getenv("COUCHBASE_USERNAME")
        password = os.getenv("COUCHBASE_PASSWORD")
        bucket_name = os.getenv("COUCHBASE_BUCKET", "b0")

        if not conn_str or not username or not password:
            raise ValueError("❌ Missing Couchbase connection details in .env")

        # Connect to the cluster
        auth = PasswordAuthenticator(username, password)
        cluster = Cluster(conn_str, ClusterOptions(auth))
        cluster.wait_until_ready(timedelta(seconds=20))
        print("✅ Connected to Couchbase Cluster")

        # Open the bucket
        bucket = cluster.bucket(bucket_name)
        print(f"✅ Bucket opened: {bucket_name}")

        # List scopes & collections
        cm = bucket.collections()
        scopes = cm.get_all_scopes()
        print("\n📂 Scopes & Collections:")
        for scope in scopes:
            print(f"  - Scope: {scope.name}")
            for collection in scope.collections:
                print(f"    • Collection: {collection.name}")

        print("\n🎉 Couchbase connection test successful!")

    except Exception as e:
        print(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    test_couchbase_connection()

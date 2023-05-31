import os
import argparse
import pandas as pd
from azure.identity import AzureDeveloperCliCredential
from azure.storage.blob import BlobServiceClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.search.documents import SearchClient

CSV_DIR = './csvloader'

parser = argparse.ArgumentParser(
    description="Load each CSV file into a single entry in Cognitive Search, uploading to blob storage, and indexing in a search index.",
    epilog="Example: loadcsv.py '..\*.csv' --storageaccount myaccount --container mycontainer --searchservice mysearch --index myindex -v"
    )
parser.add_argument("files", help="Files to be processed")
parser.add_argument("--storageaccount", help="Azure Blob Storage account name")
parser.add_argument("--container", help="Azure Blob Storage container name")
parser.add_argument("--tenantid", required=False, help="Optional. Use this to define the Azure directory where to authenticate)")
parser.add_argument("--searchservice", help="Name of the Azure Cognitive Search service where content should be indexed (must exist already)")
parser.add_argument("--index", help="Name of the Azure Cognitive Search index where content should be indexed (will be created if it doesn't exist)")
parser.add_argument("--deleteindex", action="store_true", help="Delete the search index and the storage container")
parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
args = parser.parse_args()


# Helper function to create a search index if it doesn't exist
def create_search_index():
    if args.verbose: print(f"Ensuring search index {args.index} exists...")
    index_client = SearchIndexClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                     credential=azd_credential)
    if args.index not in index_client.list_index_names():
        index = SearchIndex(
            name=args.index,
            fields=[
                SimpleField(name="id", type="Edm.String", key=True),
                SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
                SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcepage", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True)
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='default',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        )
        if args.verbose: print(f"\tCreating {args.index} search index")
        index_client.create_index(index)
    else:
        if args.verbose: print(f"\tSearch index {args.index} already exists")


# Helper function to upload the CSV to blob storage
def upload_blob(filename):
    print(f"Ensuring blob container {args.container} exists...")
    blob_service = BlobServiceClient(account_url=f"https://{args.storageaccount}.blob.core.windows.net", credential=azd_credential)
    blob_container = blob_service.get_container_client(args.container)
    if not blob_container.exists():
        print(f"\tCreating {args.container} blob container")
        blob_container.create_container()
    else:
        print(f"\tBlob container {args.container} already exists")

    print("Uploading blob for" + os.path.dirname(filename) + '/' + os.path.basename(filename))

    with open(CSV_DIR + '/' + filename,"rb") as data:
        blob_container.upload_blob(filename, data, overwrite=True)



# Helper function loads CSV and indexes
def index_csv(filename):

    # Load CSV into a Pandas dataframe to check it's valid
    df = pd.read_csv(CSV_DIR + '/' + filename)
    print(f"Successfully parsed {filename}")

    # Convert to string. index=False removes the index column which causes a leading comma in the CSV
    csv_string = df.to_csv(index=False)
    
    search_client = SearchClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                    index_name=args.index,
                                    credential=azd_credential)

    newrecord = {
        "id": filename.replace('.', '_'), 
        "content": csv_string, 
        "category": None, 
        "sourcepage": filename, 
        "sourcefile": filename
    }

    # print("\n\n===DEBUG=== upload_documents:\n" + str(newrecord));

    results = search_client.upload_documents(documents=newrecord)
    
    succeeded = sum([1 for r in results if r.succeeded])
    print(f"\tIndexed {len(results)} files, {succeeded} succeeded")


# Helper function to delete the search index and the storage container
def delete_index():
    print(f"Deleting search index {args.index}")
    index_client = SearchIndexClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                     credential=azd_credential)
    index_client.delete_index(args.index)

    print(f"Deleting blob container {args.container}")
    blob_service = BlobServiceClient(account_url=f"https://{args.storageaccount}.blob.core.windows.net", credential=azd_credential)
    blob_container = blob_service.get_container_client(args.container)
    blob_container.delete_container()


###############
# Main program starts here

print('\n\n=== LOADCSV.PY Starting ===\n\n')

# Use the current user identity to connect to Azure services unless a key is explicitly set for any of them
azd_credential = AzureDeveloperCliCredential() if args.tenantid == None else AzureDeveloperCliCredential(tenant_id=args.tenantid, process_timeout=60)

# If the deleteindex flag is set, delete the search index and the storage container
if args.deleteindex:
    print(f"Deleting search index {args.index} and blob container {args.container} ...")
    delete_index()
    exit()

# Load any CSVs in the current folder
csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]

# If there are no CSVs, exit
if len(csv_files) == 0:
    print(f"No CSV files found in {CSV_DIR} folder")
    exit()

# Create the search index if it doesn't exist
create_search_index()

print(f"Processing files...")

for filename in csv_files:
    print("\t" + CSV_DIR + '/' + filename)

    upload_blob(filename)

    index_csv(os.path.basename(filename))

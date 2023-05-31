#!/bin/sh

echo ""
echo "Loading azd .env file from current environment"
echo ""

while IFS='=' read -r key value; do
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    export "$key=$value"
done <<EOF
$(azd env get-values)
EOF

# test that the csvloader folder exists as a subdirectory
if [ ! -d "./csvloader" ]; then
    echo "Error: ./csvloader folder not found.\n NOTE: You need to be in the parent folder and run ./csvloader/loadcsv.sh"
    exit 1
fi

echo 'Creating python virtual environment "csvloader/.venv"'
python -m venv csvloader/.venv

echo 'Installing dependencies from "requirements.txt" into virtual environment'
./csvloader/.venv/bin/python -m pip install -r csvloader/requirements.txt

# Check for --deleteindex flag
if echo "$@" | grep -q -- --deleteindex; then
    echo '\n\nRunning "loadcsv.py" with --deleteindex flag'
    ./csvloader/.venv/bin/python ./csvloader/loadcsv.py './*.csv' --deleteindex --storageaccount "$AZURE_STORAGE_ACCOUNT" --container "$AZURE_STORAGE_CONTAINER" --searchservice "$AZURE_SEARCH_SERVICE" --index "$AZURE_SEARCH_INDEX" --tenantid "$AZURE_TENANT_ID" -v
else
    echo '\n\nRunning "loadcsv.py"'
    ./csvloader/.venv/bin/python ./csvloader/loadcsv.py './*.csv' --storageaccount "$AZURE_STORAGE_ACCOUNT" --container "$AZURE_STORAGE_CONTAINER" --searchservice "$AZURE_SEARCH_SERVICE" --index "$AZURE_SEARCH_INDEX" --tenantid "$AZURE_TENANT_ID" -v
fi
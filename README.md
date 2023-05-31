# CSV Loader for Azure-Search-OpenAI-Demo
## Why
The [Azure Search OpenAI Demo](https://github.com/Azure-Samples/azure-search-openai-demo) is an excellent and useful base demo for showing how to search **unstructured** data. That said, it's not really designed to support analysis of structured (tabular) datasets which are best solved using other forms of database. Regardless, the usability, quality and popularity of this demo mean that there is a desire for a quick way to load **small amounts** of structured data into Cognitive Search to demonstrate reasoning over it with GPT.

## How
This is a fork of the original PDF loader (`prepdocs.py`) modified for loading CSVs into CogSearch.  
It's incredibly simplistic and (right now) **loads each CSV as a single document** in CogSearch.  

> Do not load CSVs that are more than a few hundred cells (rows x columns) as they will be too big (too many tokens) for the default GPT model (`gpt-35-turbo`) to process (4k tokens limit)

## Steps
1. Download this repository
 -- https://github.com/leongj/azure-search-demo-csv-loader/zipball/main
   
2. Copy the `csvloader` directory into your working `azure-search-openai-demo` directory (so it becomes `azure-search-openai-demo/csvloader`).
   
3. Copy your `.csv` file(s) into the `csvloader` folder.
   
4. Open a PowerShell (or bash) Terminal in the base folder (`azure-search-openai-demo`).
   
5. (optional) Delete the existing index (e.g. if it has the default sample content in it), run `./csvloader/loadcsv.ps1 --deleteindex` (replace with `loadcsv.sh` on Linux/Bash)
   
6. Load your CSV files by running `./csvloader/loadcsv.ps1` (replace with `loadcsv.sh` on Linux/Bash)

If it is successful, you should be able to search in the index immediately.
  
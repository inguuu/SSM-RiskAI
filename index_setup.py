#! pip install azure-search-documents==11.6.0b12 --quiet
#! pip install azure-identity --quiet
#! pip install python-dotenv --quiet

# python index_setup.py
from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    ComplexField,
    SearchIndex
)

# .env file 참조
load_dotenv()

# 환경변수에서 가져오기
search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
search_api_key = os.getenv('AZURE_SEARCH_API_KEY')
index_name = "risk-assessment-index"

credential = AzureKeyCredential(search_api_key)
index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

# 인덱스 필드 정의
fields = [
    SimpleField(name="PageId", type=SearchFieldDataType.String, key=True),
    SearchableField(name="DocumentName", type=SearchFieldDataType.String, sortable=True),
    SearchableField(name="Content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
    SearchableField(name="RiskCategory", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
    SearchableField(name="Tags", collection=True, type=SearchFieldDataType.String, facetable=True, filterable=True)
]

# Suggesters (자동완성용)
suggester = [{'name': 'sg', 'source_fields': ['Tags', 'DocumentName']}]

# Scoring profiles (기본 비워둠)
scoring_profiles = []

# 인덱스 생성
index = SearchIndex(
    name=index_name,
    fields=fields,
    suggesters=suggester,
    scoring_profiles=scoring_profiles
)

result = index_client.create_or_update_index(index)
print(f'Index "{result.name}" created successfully.')
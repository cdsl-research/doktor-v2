# openapi_client.DefaultApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_paper_handler_paper_post**](DefaultApi.md#create_paper_handler_paper_post) | **POST** /paper | Create Paper Handler
[**download_paper_handler_paper_paper_uuid_download_get**](DefaultApi.md#download_paper_handler_paper_paper_uuid_download_get) | **GET** /paper/{paper_uuid}/download | Download Paper Handler
[**healthz_handler_healthz_get**](DefaultApi.md#healthz_handler_healthz_get) | **GET** /healthz | Healthz Handler
[**read_paper_handler_paper_paper_uuid_get**](DefaultApi.md#read_paper_handler_paper_paper_uuid_get) | **GET** /paper/{paper_uuid} | Read Paper Handler
[**read_papers_handler_paper_get**](DefaultApi.md#read_papers_handler_paper_get) | **GET** /paper | Read Papers Handler
[**root_handler_get**](DefaultApi.md#root_handler_get) | **GET** / | Root Handler
[**topz_handler_topz_get**](DefaultApi.md#topz_handler_topz_get) | **GET** /topz | Topz Handler
[**update_paper_handler_paper_paper_uuid_put**](DefaultApi.md#update_paper_handler_paper_paper_uuid_put) | **PUT** /paper/{paper_uuid} | Update Paper Handler
[**upload_paper_file_handler_paper_paper_uuid_upload_post**](DefaultApi.md#upload_paper_file_handler_paper_paper_uuid_upload_post) | **POST** /paper/{paper_uuid}/upload | Upload Paper File Handler


# **create_paper_handler_paper_post**
> bool, date, datetime, dict, float, int, list, str, none_type create_paper_handler_paper_post(paper_create_update)

Create Paper Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.paper_create_update import PaperCreateUpdate
from openapi_client.model.http_validation_error import HTTPValidationError
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    paper_create_update = PaperCreateUpdate(
        author_uuid=[
            "author_uuid_example",
        ],
        title="title_example",
        keywords=[
            "keywords_example",
        ],
        label="label_example",
        categories_id=[
            1,
        ],
        abstract="abstract_example",
        url="url_example",
        thumbnail_url="thumbnail_url_example",
        is_public=True,
    ) # PaperCreateUpdate | 

    # example passing only required values which don't have defaults set
    try:
        # Create Paper Handler
        api_response = api_instance.create_paper_handler_paper_post(paper_create_update)
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->create_paper_handler_paper_post: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **paper_create_update** | [**PaperCreateUpdate**](PaperCreateUpdate.md)|  |

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **download_paper_handler_paper_paper_uuid_download_get**
> bool, date, datetime, dict, float, int, list, str, none_type download_paper_handler_paper_paper_uuid_download_get(paper_uuid)

Download Paper Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.http_validation_error import HTTPValidationError
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    paper_uuid = "paper_uuid_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        # Download Paper Handler
        api_response = api_instance.download_paper_handler_paper_paper_uuid_download_get(paper_uuid)
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->download_paper_handler_paper_paper_uuid_download_get: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **paper_uuid** | **str**|  |

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **healthz_handler_healthz_get**
> bool, date, datetime, dict, float, int, list, str, none_type healthz_handler_healthz_get()

Healthz Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Healthz Handler
        api_response = api_instance.healthz_handler_healthz_get()
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->healthz_handler_healthz_get: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_paper_handler_paper_paper_uuid_get**
> bool, date, datetime, dict, float, int, list, str, none_type read_paper_handler_paper_paper_uuid_get(paper_uuid)

Read Paper Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.http_validation_error import HTTPValidationError
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    paper_uuid = "paper_uuid_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        # Read Paper Handler
        api_response = api_instance.read_paper_handler_paper_paper_uuid_get(paper_uuid)
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->read_paper_handler_paper_paper_uuid_get: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **paper_uuid** | **str**|  |

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_papers_handler_paper_get**
> bool, date, datetime, dict, float, int, list, str, none_type read_papers_handler_paper_get()

Read Papers Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.http_validation_error import HTTPValidationError
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    private = False # bool |  (optional) if omitted the server will use the default value of False

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        # Read Papers Handler
        api_response = api_instance.read_papers_handler_paper_get(private=private)
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->read_papers_handler_paper_get: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **private** | **bool**|  | [optional] if omitted the server will use the default value of False

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **root_handler_get**
> bool, date, datetime, dict, float, int, list, str, none_type root_handler_get()

Root Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Root Handler
        api_response = api_instance.root_handler_get()
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->root_handler_get: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **topz_handler_topz_get**
> bool, date, datetime, dict, float, int, list, str, none_type topz_handler_topz_get()

Topz Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Topz Handler
        api_response = api_instance.topz_handler_topz_get()
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->topz_handler_topz_get: %s\n" % e)
```


### Parameters
This endpoint does not need any parameter.

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_paper_handler_paper_paper_uuid_put**
> bool, date, datetime, dict, float, int, list, str, none_type update_paper_handler_paper_paper_uuid_put(paper_uuid, paper_create_update)

Update Paper Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.paper_create_update import PaperCreateUpdate
from openapi_client.model.http_validation_error import HTTPValidationError
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    paper_uuid = "paper_uuid_example" # str | 
    paper_create_update = PaperCreateUpdate(
        author_uuid=[
            "author_uuid_example",
        ],
        title="title_example",
        keywords=[
            "keywords_example",
        ],
        label="label_example",
        categories_id=[
            1,
        ],
        abstract="abstract_example",
        url="url_example",
        thumbnail_url="thumbnail_url_example",
        is_public=True,
    ) # PaperCreateUpdate | 

    # example passing only required values which don't have defaults set
    try:
        # Update Paper Handler
        api_response = api_instance.update_paper_handler_paper_paper_uuid_put(paper_uuid, paper_create_update)
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->update_paper_handler_paper_paper_uuid_put: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **paper_uuid** | **str**|  |
 **paper_create_update** | [**PaperCreateUpdate**](PaperCreateUpdate.md)|  |

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **upload_paper_file_handler_paper_paper_uuid_upload_post**
> bool, date, datetime, dict, float, int, list, str, none_type upload_paper_file_handler_paper_paper_uuid_upload_post(paper_uuid, file)

Upload Paper File Handler

### Example


```python
import time
import openapi_client
from openapi_client.api import default_api
from openapi_client.model.http_validation_error import HTTPValidationError
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = default_api.DefaultApi(api_client)
    paper_uuid = "paper_uuid_example" # str | 
    file = open('/path/to/file', 'rb') # file_type | 

    # example passing only required values which don't have defaults set
    try:
        # Upload Paper File Handler
        api_response = api_instance.upload_paper_file_handler_paper_paper_uuid_upload_post(paper_uuid, file)
        pprint(api_response)
    except openapi_client.ApiException as e:
        print("Exception when calling DefaultApi->upload_paper_file_handler_paper_paper_uuid_upload_post: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **paper_uuid** | **str**|  |
 **file** | **file_type**|  |

### Return type

**bool, date, datetime, dict, float, int, list, str, none_type**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


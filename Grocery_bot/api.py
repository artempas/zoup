import requests
from dotenv import load_dotenv
from os import environ

load_dotenv()
api_url = environ.get("api_url")


class NotFoundException(Exception):
    pass


class APIError(Exception):
    status_code: int
    url: str
    payload: dict
    response: str
    method: str

    def __init__(self, status_code: int, method: str, url: str, response: str, payload: dict = None, *args):
        super().__init__(*args)
        self.status_code = status_code
        self.url = url
        self.response = response
        self.payload = payload
        self.method = method

    @classmethod
    def from_response(cls, response: requests.Response):
        return cls(response.status_code, response.request.method, response.url, response.request.body)


def get_products(id_: int = None, chat_id: int = None, **kwargs) -> (int, list):
    """
    API response to get products
    @param id_: [Optional] get single product by id
    @param chat_id: [Optional] Required if id_ is not specified
    @param kwargs: more fields to filter by
    @return: [total_pages, json list of products]
    """
    response = requests.get(url=api_url + "products" + f"/{id_}" if id_ else "", params=kwargs)
    if response.status_code == 404:
        raise NotFoundException(response.text)
    elif response.status_code != 200:
        raise APIError.from_response(response)
    json_response = response.json()
    if id_:
        return 1, [json_response]
    if "page" in kwargs:
        return (json_response["count"] / len(json_response["results"])).__ceil__(), json_response["results"]
    else:
        return 1, json_response


def create_product(name: str, chat_id: int):
    response = requests.post(url=api_url + "products", params=chat_id, json={"name": name})
    if response.status_code == 404:
        raise NotFoundException(response.text)
    elif response.status_code != 200:
        raise APIError.from_response(response)
    return response.json()

from dataclasses import dataclass
import api


@dataclass
class Family:
    id: int
    name: str
    creator_id: int


@dataclass
class Profile:
    family: Family | int
    chat_id: int
    tg_username: str

    def __init__(self, **kwargs):
        if type(kwargs["Family"]) is dict:
            kwargs["Family"] = Family(**kwargs["Family"])
        super().__init__(**kwargs)


@dataclass
class User:
    id: int
    profile: Profile

    def __init__(self, **kwargs):
        if type(kwargs.get("Profile")) is dict:
            kwargs["Profile"] = Profile(**kwargs["Profile"])
        super().__init__(**kwargs)


@dataclass
class Product:
    id: int
    name: str
    category: str
    to_notify: str
    created_by: User

    def __init__(self, **kwargs):
        if type(kwargs.get("created_by")) is dict:
            kwargs["created_by"] = User(**kwargs["created_by"])
        super.__init__(**kwargs)

    @classmethod
    def get(cls, chat_id: int, page: int = 1, id_: int = None, category: str = None) -> list["Product"]:
        json = api.get_products(id_, chat_id, page=page, category=category)
        return list(cls(**i) for i in json)

    @classmethod
    def by_name(cls, name: str, chat_id: int) -> "Product":
        return cls(**api.create_product(name, chat_id))

    def delete(self) -> "Product":
        pass

    def update(self) -> "Product":
        pass

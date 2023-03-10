from dataclasses import dataclass
from os import environ

from dotenv import load_dotenv

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
    def create_from_name(cls, name: str, chat_id: int) -> "Product":
        return cls(**api.create_product(name, chat_id))

    def delete(self, chat_id: int) -> int:
        """
        Delete product from db. Returns amount of deleted items. Sets None to all fields
        @param chat_id:
        @return:
        """
        for attr in self.__dict__:
            setattr(self, attr, None)
        return api.delete_product(chat_id=chat_id, id=self.id)

    def update(self, chat_id: int) -> "Product":
        return self.__class__(**api.update_product(chat_id, self.id))


if __name__ == '__main__':
    cart = Product.get(354640082)
    print(f"{cart=}")
    cart.append(Product.create_from_name("Хлеб", 354640082))
    print(f"created_from_name = {cart[-1]}")
    cart[-1].name = "Помидор"
    cart[-1].update(354640082)
    print(f"updated = {cart[-1]}")
    print(f"deleted = {cart[-1].delete(354640082)}")

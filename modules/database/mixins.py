from odmantic import query, Model

from .engine import engine


class ModelInheritanceError(Exception):
    pass


__all__ = (
    'ModelExtMixin',
)


class ModelExtMixin:
    """
    This mixin adds the following methods to odmantic models:
        - query (classmethod): builds a query with passed kwargs using the "$and" notation
        - get (classmethod): fetches the first document that has passed kwargs or (optionally)
            returns a new instance with passed kwargs.
        - find (classmethod): shorthand for engine find operation using the model and query with kwargs
        - save: saves the instance to the database
        - delete: deletes the instance from the database. It does not delete the instance itself.
    """
    engine = engine

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if Model not in self.__class__.__bases__:
            raise ModelInheritanceError(f'Class "{self.__class__.__name__}" '
                                        f'does not inherit from "odmantic.Model"')

    @classmethod
    def query(cls, **kwargs):
        return query.and_(*(getattr(cls, kw) == v for kw, v in kwargs.items()))

    @classmethod
    async def get(cls, create=False, /, **kwargs):
        """
        Searches the collection for a document with specified keys and values
        Args:
            create (bool):
                If True a new instance will be created with kwargs
                This argument is positional only, to prevent collisions with document keys.
            **kwargs: key/values to search for

        Returns:
            The document if found, else a new instance with the attributes set
        Raises:
            AttributeError: If the model does not have the specified attribute set.
            ValidationError: If an object is to be created but required fields are missing
        """
        q = cls.query(**kwargs)
        doc = await engine.find_one(cls, q)

        return doc or (cls(**kwargs) if create else None)

    @classmethod
    async def find(cls, limit=None, sort=None, /, **kwargs):
        """
        Executes a "find" query with this collection.
        Query parameters are passed as "and".
        Args:
            limit (Optional[int]): the maximum amount of items to get.
            sort (Optional[Any]): Odmantic sort expression
            **kwargs: key/values to search for
        Returns:
            List[cls] a list of instances of this class with the query parameters, stored in the database
        """
        q = cls.query(**kwargs)
        return await engine.find(cls, q, sort=sort, limit=limit)

    async def save(self):
        """
        Persists the instance to the database
        Uses Upsert method
        """
        await engine.save(self)

    async def delete(self):
        """
        Deletes this document from the database
        This method cannot delete the instance itself.
        """
        await engine.delete(self)

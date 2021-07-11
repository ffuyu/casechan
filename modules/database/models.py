from odmantic import query, Model

from modules.database.engine import engine

__all__ = (
    'ModelPlus',
)


class ModelPlus(Model):

    @property
    def engine(self):
        return engine

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
        return doc or cls(**kwargs) if create else None

    async def save(self):
        """
        Persists the instance to the database
        Uses Upsert method
        """
        await engine.save(self)


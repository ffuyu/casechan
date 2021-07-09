from odmantic import query, Model

from modules.database.engine import engine

__all__ = (
    'ModelPlus',
)

class ModelPlus(Model):

    @classmethod
    async def get_or_create(cls, **kwargs):
        """
        Searches the collection for a document with specified keys and values
        Args:
            **kwargs: key/values to search for

        Returns:
            The document if found, else a new instance with the attributes set
        Raises:
            AttributeError: If the model does not have the specified attribute set.
            ValidationError: If an object is to be created but required fields are missing
        """
        q = query.and_(*(getattr(cls, kw) == v for kw, v in kwargs.items()))
        doc = await engine.find_one(cls, q)
        return doc or cls(**kwargs)

    async def save(self):
        """
        Persists the instance to the database
        Uses Upsert method
        """
        await engine.save(self)

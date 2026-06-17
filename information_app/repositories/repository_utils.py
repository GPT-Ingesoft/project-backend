from abc import ABC, abstractmethod
from typing import Optional

class BaseRepository(ABC):

    @abstractmethod
    def get_model(self):
        ...

    # ── Query operations ────────────────────────────────────────────

    def get_by_id(self, object_id) -> Optional[object]:
        return self.get_model().objects.filter(id=object_id).first()

    def get_all(self, order_by: str = None):
        qs = self.get_model().objects.all()
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def exists(self, **filters) -> bool:
        return self.get_model().objects.filter(**filters).exists()

    def exists_excluding(self, exclude_id: int, **filters) -> bool:
        return (
            self.get_model()
            .objects.filter(**filters)
            .exclude(id=exclude_id)
            .exists()
        )

    # ── Write ────────────────────────────────────────────────────

    def create(self, **kwargs):
        return self.get_model().objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=list(kwargs.keys()))
        return instance

    def update_fields(self, instance, **kwargs):
        return self.update(instance, **kwargs)

    def delete_instance(self, instance):
        instance.delete()

# coding: utf-8
from itertools import chain
from applications.IR.store.models import Store, Hub


class StoreService:

    _model = Store


class HubService:

    _model = Hub

    @classmethod
    def get_hub_id_by_store_id(cls, store_id):
        filter_spec = [(cls._model.store_id, store_id)]
        hub_id = cls._model.model_query(
            args=[cls._model.hub_id], filter_spec=filter_spec
        )
        return chain(*hub_id)

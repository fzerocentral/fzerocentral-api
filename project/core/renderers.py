from rest_framework.renderers import JSONRenderer


class JSONAPIRenderer(JSONRenderer):
    # Send responses of Content-Type 'application/vnd.api+json' instead of
    # 'application/json'.
    # https://jsonapi.org/format/#content-negotiation-clients
    media_type = 'application/vnd.api+json'

    # TODO: Need to include a `type` key, and put non-id attributes on a lower
    # level, like:
    # "data": [{
    #     "type": "games",
    #     "id": "1",
    #     "attributes": {
    #       "name": "F-Zero"
    #     }
    #   }, {
    #     "type": "games",
    #     "id": "2",
    #     "attributes": {
    #       "name": "BS F-Zero Grand Prix 2"
    #     }
    #   }]

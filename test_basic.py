from enum import Enum

class CallbackIndex(Enum):
    UPDATE_DELTA    = 0
    GET_ACCEPTED    = 1
    GET_REJECTED    = 2
    UPDATE_ACCEPTED = 3
    UPDATE_REJECTED = 4
    DELETE_ACCEPTED = 5
    DELETE_REJECTED = 6
    UPDATE_DOCUMENT = 7
    SUBSCRIBE_USER  = 8
    PUBLISH_USER    = 9




print(len(list(CallbackIndex)))
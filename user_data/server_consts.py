from enum import Enum
from datetime import datetime

class ServerConsts:
    class MatchesDataNames(str,Enum):
        SETTINGS = 'settings'
        IS_SEARCHING  = 'is_searching'
        MATCHES = 'matches'
        STATUS = 'status'
        SEARCH_TIMESTAMP = 'search_timestamp'
        PREVIOUS_MATCHES_IDS = 'previous_matches_ids'
    class MatchesStatus(str,Enum):
        FOUND = 'found'
        NOT_FOUND = 'not_found'
        WEAK_FOUND = 'weak_found'
        EMPTY = 'empty'
        SEARCHING = 'searching'
        
    class RegistrationResponses(str, Enum):
        ALREADY_REGISTERED = 'registered'
        #Here are the actual responses consts
        STATUS = 'status'
        NEW_REGISTER = 'new_register'
        USER_DATA = 'user_data'

    class PushedData(str,Enum):
        PUSH_NOTIFICATION_TYPE = 'push_notification_type'
        NEW_READ_RECIEPT = 'new_read_receipt'
        MATCH_INFO = 'match_info'
        CHANGE_USER_STATUS = 'change_user_status'
        CHANGE_USER_KEY = 'change_user_key'
        CHANGE_USER_VALUE = 'change_user_value'

        
    class LocationCountResponses(str, Enum):
        STATUS = 'status'
        UNKNOWN_USER_LOCATION = 'unknown_location'
        ENOUGH_USERS = 'enough_users'
        NOT_ENOUGH_USERS = 'not_enough_users'
        CURRENT_NUM = 'current_num'
        REQUIRED_NUM = 'required_num'
        IS_TEST_USER = 'is_test_user'
        
    class LIMITS(Enum):
        MATCH_KEY_TTL_SECONDS = 3600 * 24
        MAX_MATCHES_PER_USER_QUERY = 20
        NUM_MATCHES_GIVE_USER = 20
        MAX_TIME_MATCHES_SEARCH_IN_SECONDS = 10.0
        MAX_USERS_IN_PREVIOUS_CACHE = MAX_MATCHES_PER_USER_QUERY * 3
        MIN_TIME_SEARCHES_WHEN_NOT_FOUND_IN_SECONDS = 60 * 5
    @staticmethod
    def get_user_matches_key(userid):
        return f'matches_{userid}'
    @staticmethod
    def get_empty_matches_user(userid, user_settings):
        user_matches_data = {ServerConsts.MatchesDataNames.SETTINGS.value: user_settings,
                         ServerConsts.MatchesDataNames.MATCHES.value: [],
                         ServerConsts.MatchesDataNames.IS_SEARCHING: False,
                         ServerConsts.MatchesDataNames.SEARCH_TIMESTAMP.value: 0,
                         ServerConsts.MatchesDataNames.STATUS: ServerConsts.MatchesStatus.EMPTY.value
                         }
        return user_matches_data

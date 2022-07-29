from enum import Enum


class SQL_CONSTS:
    
    class TablesNames(str,Enum):
        IMAGES = 'images'
        USERS='users'
        DUMMY_USERS = 'dummy_users'
        DUMMY_USERS_IMAGES = 'dummy_users_images'
        PARTICIPANTS='participants'
        UTIL_LOCATION = 'util_location'
        POF_STATE_LOCATION = 'util_pof_country_location'
        ONTARIO_POF_STATE_LOCATION = 'util_ontario_pof_country_location'
        DECISIONS = 'decisions'
        CELEBS_FR_DATA = 'celebs_fr_data'
        CELEBS_S3_IMAGES = 'celebs_s3_images'
        MATCHES = 'matches'
        CONVERSATIONS = 'conversations'
        MESSAGES = 'messages'
        RECEIPTS = 'receipts'
        USERS_FR_DATA = 'users_fr_data'

    class CELEBS_FR_DataColumn(str,Enum):
        CELEBNAME = 'celebname'
        FR_DATA = 'fr_data'
        PRIMARY_KEY = CELEBNAME
    
    class CELEBS_S3_ImagesColumns(str,Enum):
        CELEBNAME = 'celebname'
        FILENAME = 'filename'
        PRIORITY = 'priority'
        PRIMARY_KEY = f'({CELEBNAME},{FILENAME})'

    class UtilLocationColumns(str,Enum):
        DESCRIPTION = 'description'
        LONGITUDE = 'longitude'
        LATITUDE = 'latitude'
        PRIMARY_KEY = f'({LATITUDE},{LONGITUDE},{DESCRIPTION})'
        
    class UtilOntarioLocationColumns(str,Enum):
        STATE_ID = 'state_id'
        CITY = 'city'
        LONGITUDE = 'longitude'
        LATITUDE = 'latitude'
        PRIMARY_KEY = f'({LATITUDE},{LONGITUDE},{STATE_ID},{CITY})'


    class DummyUsersColumns(str, Enum):
        POF_ID = 'pof_id'

    class DummyUsersImagesColumns(str,Enum):
        USER_ID = 'user_id'
        FILENAME = 'filename'
        PRIORITY = 'priority'
        


    class UsersColumns(str, Enum):
        # Data about the user from firebase's JWT
        FIREBASE_UID = 'firebase_uid'
        FIREBASE_NAME = 'firebase_name'
        FIREBASE_EMAIL = 'firebase_email'
        FIREBASE_SIGNIN_PROVIDER = 'firebase_signin_provider'
        FIREBASE_IMAGE_URL = 'firebase_image_url'
        FIREBASE_PHONE_NUMBER = 'firebase_phone_number'
        FACEBOOK_ID = 'facebook_id'
        FACEBOOK_BIRTHDAY = 'facebook_birthday'
        APPLE_ID = 'apple_id'
        NAME = 'name'
        FCM_TOKEN = 'fcm_token'
        ADDED_DATE = 'added_date'
        FACEBOOK_PROFILE_IMAGE_URL = 'facebook_profile_image_url'
        UPDATE_DATE = 'update_date'
        MIN_AGE = 'min_age'
        MAX_AGE = 'max_age'
        GENDER_PREFERRED = 'gender_preferred'
        FILTER_NAME = 'filter_name'
        AUDITION_COUNT = 'audition_count'
        FILTER_DISPLAY_IMAGE = 'filter_display_image'
        CELEB_ID = 'celeb_id'
        TASTE_MIX_RATIO = 'taste_mix_ratio'
        RADIUS = 'radius'
        SEARCH_DISTANCE_ENABLED = 'search_distance_enabled'
        EMAIL = 'email'
        USER_DESCRIPTION = 'user_description'
        USER_GENDER = 'user_gender'
        SHOW_USER_GENDER = 'show_user_gender'
        RELATIONSHIP_TYPE = 'relationship_type'
        USER_BIRTHDAY = 'user_birthday'
        USER_BIRTHDAY_TIMESTAMP = 'user_birthday_timestamp'
        LONGITUDE = 'longitude'
        LATITUDE = 'latitude'
        LOCATION_DESCRIPTION = 'location_description'
        SHOW_DUMMY_PROFILES = 'show_dummy_profiles'
        JOB_TITLE = 'job_title'
        HEIGHT_IN_CM = 'height_in_cm'
        SCHOOL = 'school'
        RELIGION = 'religion'
        ZODIAC = 'zodiac'
        FITNESS = 'fitness'
        SMOKING = 'smoking'
        DRINKING = 'drinking'
        EDUCATION = 'education'
        CHILDREN = 'children'
        COVID_VACCINE = 'covid_vaccine'
        HOBBIES = 'hobbies'
        PETS = 'pets'
        TEXT_SEARCH = 'text_search'
        REGISTRATION_STATUS = 'registration_status'
        HAS_FR_DATA = 'has_fr_data'
        
    class REGISTRATION_STATUS_TYPES(str, Enum):
        REGISTERED = 'registered'
        DELETED = 'deleted'
        
    class ADDED_USER_COLUMNS(str, Enum):
        AGE = 'age'
        IMAGES = 'images'
        HOTNESS = 'hotness'
        COMPATABILITY = 'compatibility'
        LOCATION_DISTANCE = 'location_distance'

    class DecisionsColumns(str, Enum):
        DECIDER_ID = 'decider_id'
        DECIDEE_ID = 'decidee_id'
        DECISION_TIMESTAMP = 'timestamp'
        DECISION = 'decision'
        PRIMARY_KEY = '('+DECIDER_ID+','+DECIDEE_ID+')'
    
    class DecisionsTypes(str, Enum):
       DONT_KNOW = 'dontKnow'
       INDECIDED = 'indecided'
       NOPE = 'nope'
       LIKE ='like'
       SUPERLIKE = 'superLike'
       UNMATCHED = 'unmatched'
    
    class ConversationsColumns(str, Enum):
        CONVERSATION_ID = 'conversation_id'
        CREATION_TIME = 'creation_time'
        CHANGE_TIME = 'last_changed_time'
    
    class MessagesColumns(str, Enum):
        MESSAGE_ID = 'message_id_'
        CREATOR_USER_ID = 'user_id'
        CONVERSATION_ID = 'conversation_id'
        CREATION_DATE = 'added_date'
        CHANGE_DATE = 'changed_date'
        CONTENT = 'content'
        MESSAGE_STATUS = 'status'
    
    class ParticipantsColumns(str, Enum):
        CONVERSATION_ID = 'conversation_id'
        FIREBASE_UID = 'firebase_uid'
    
    class ReceiptColumns(str, Enum):
        USER_ID = 'user_id'
        MESSAGE_ID = 'message_id_'
        SENT_TS = 'sent_ts'
        READ_TS = 'read_ts'
    
    class MatchColumns(str, Enum):
        ID_USER1 = 'id_user1'
        ID_USER2 = 'id_user2'
        STATUS = 'status'
        WHO_CANCELLED = 'who_cancelled'
        TIMESTAMP_CHANGED = 'timestamp_changed'
        TIMESTAMP_CREATED = 'timestamp_created'
        PRIMARY_KEY = f'({ID_USER1},{ID_USER2})'
    
    class ImageColumns(str, Enum):
        USER_ID = 'user_id'
        BUCKET_NAME = 'bucket_name'
        MORE_INFO = 'more_info'
        PRIORITY = 'priority'
        TYPE = 'type'
        IS_PROFILE = 'is_profile'
        FILENAME = 'filename'
        ANALYZED_IMAGE_TS = 'analyzed_image_timestamp'
        PRIMARY_KEY = f'({USER_ID},{FILENAME})'

    class UsersFrDataColumns(str, Enum):
        USER_ID = 'user_id'
        FR_DATA = 'fr_data'
    
    class MatchConsts(str, Enum):
        ACTIVE_MATCH = 'active'
        CANCELLED_MATCH = 'unmatched'
        
    class ImagesConsts(str, Enum):
        IN_PROFILE_TYPE = 'in_profile'
        DELETED = 'deleted'

    class FilterTypes(str, Enum):
        CELEB_IMAGE = 'CELEB_IMAGE'
        CUSTOM_IMAGE ='CUSTOM_IMAGE'
        USER_TASTE = 'USER_TASTE'
        TEXT_SEARCH = 'TEXT_SEARCH'
        NONE = 'NONE'

    class UsersPreferredGender(str, Enum):
        MEN = 'Men'
        WOMEN = 'Women'
        EVERYONE = 'Everyone'

    class DummyUsersGender(str, Enum):
        MALE = 'Male'
        FEMALE = 'Female'

    class UserRadiusEnabled(str, Enum):
        TRUE = 'true'
        FALSE = 'false'

    class UserHasFr(str, Enum):
        TRUE = 'true'
        FALSE = 'false'
        


     
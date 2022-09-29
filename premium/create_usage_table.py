#The routes config.
PREMIUM_ROUTES_VALUES = {
    'analyze-user-fr/get_free_celebs_lookalike':8,
    'analyze-user-fr/get_traits':8,
    '/morph/free_perform':8,
    '/cartoonize/create_cartoon':8,
    'generate_image':8,
    'generate_image_to_image':8
}

PREMIUM_ROUTES_COLUMN_NAME = {
    'analyze-user-fr/get_free_celebs_lookalike':'celebs_lookalike',
    'analyze-user-fr/get_traits':'traits',
    '/morph/free_perform':'morph',
    '/cartoonize/create_cartoon':'cartoon',
    'generate_image':'dream_from_prompt',
    'generate_image_to_image':'dream_from_image'
}

PREMIUM_ROUTES = list(PREMIUM_ROUTES_VALUES.keys())
aurora_writer_host = 'voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'
from postgres_client import  PostgresClient

aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_writer_host)
aurora_client.create_usage_table()


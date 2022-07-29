import numpy as np
from dataclasses import dataclass
from typing import List

THRESHOLD_EMBEDDINGS = 1.5 #This is the threshold i saw @face evolve repo.


@dataclass
class EmbeddingsData:
    image_key: str
    embedding: np.ndarray
    detection_index: int


def calc_distance_between_embeddings(embeddings1:EmbeddingsData, embeddings2:EmbeddingsData):
    diff = np.subtract(embeddings1.embedding, embeddings2.embedding)
    dist = np.sum(np.square(diff))
    return dist


def embedding_distance_to_group(group_embeddings: List[EmbeddingsData], embedding_checked_against: EmbeddingsData):
    distances = [calc_distance_between_embeddings(embedding_data, embedding_checked_against) for embedding_data in group_embeddings]
    return sum(distances)/len(distances)


def embeddings_to_groups(embeddings_data: List[EmbeddingsData]):
    groups_embeddings = []

    for embedding_data in embeddings_data:
        current_min_distance, current_min_index = 1000, -1
        for group_index, group in enumerate(groups_embeddings):
            distance_to_current_group = embedding_distance_to_group(group, embedding_data)
            if distance_to_current_group < current_min_distance:
                current_min_distance = distance_to_current_group
                current_min_index = group_index
        if current_min_distance < THRESHOLD_EMBEDDINGS:
            groups_embeddings[current_min_index].append(embedding_data)
        else:
            groups_embeddings.append([embedding_data])
    groups_embeddings.sort(key=len, reverse=True)  # 0 index is the largest group now
    return groups_embeddings

def get_mid_embedding(embeddings_data_group: List[EmbeddingsData]):
    if len(embeddings_data_group)<1: raise ValueError('Got empty group of faces')
    if len(embeddings_data_group)==1: return embeddings_data_group[0]
    total_distances = []
    for i in range(len(embeddings_data_group)):
        total_distance = 0.0
        for j in range(len(embeddings_data_group)):
            if j!=i:
                total_distance+=calc_distance_between_embeddings(embeddings_data_group[i],embeddings_data_group[j])
        total_distances.append(total_distance)
    return embeddings_data_group[total_distances.index(min(total_distances))]



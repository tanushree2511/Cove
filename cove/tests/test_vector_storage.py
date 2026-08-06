import faiss
import numpy as np
from engines.vector_storage import VectorStorage


def test_vector_storage_round_trip(tmp_path):
    index_path = tmp_path / "test_index.bin"
    vector_path = tmp_path / "test_vectors.npy"

    storage = VectorStorage(index_path=str(index_path), vector_path=str(vector_path))
    data = np.random.rand(2, 512).astype("float32")
    paths = ["a.jpg", "b.jpg"]
    storage.add(data, paths)
    storage.save()

    reloaded = VectorStorage(index_path=str(index_path), vector_path=str(vector_path))

    first_vector = reloaded.get_vector_by_path("a.jpg")
    second_vector = reloaded.get_vector_by_path("b.jpg")

    assert reloaded.has_path("a.jpg")
    assert reloaded.path_to_index["b.jpg"] == 1
    assert first_vector is not None
    assert second_vector is not None
    assert first_vector.shape == (512,)

    # add() L2-normalizes vectors before storing (IndexFlatIP needs unit-norm
    # vectors for its inner product to behave as cosine similarity), so the
    # round-tripped vector should match the normalized input, not the raw one.
    expected = data.copy()
    faiss.normalize_L2(expected)
    assert np.allclose(first_vector, expected[0], atol=1e-6)

import common as cmn
import matplotlib.pyplot as plt
import cv2
import numpy as np
from pathlib import Path


def main(D):
    N=None
    print("Loading model...")

    model_files = {
        200: f"frWac_non_lem_no_postag_no_phrase_200_cbow_cut100.bin",
        700: f"frWiki_no_phrase_no_postag_700_cbow_cut100.bin",
    }

    model = cmn.load_model(model_files[D])

    print("Loading words...")
    words = cmn.load_most_frequent_words(N=N, model=model)
    N = len(words)
    print(f"Loaded {N} words.")

    sim_matrix = cmn.compute_similarity_matrix_fast(model, words)

    # save matrix to npz file
    output_file = Path(__file__).parent.parent / "data" / f"similarity_matrix_N{N}f64_D{D}_c.npz"
    np.savez_compressed(output_file, sim_matrix, words)
    print(f"Similarity matrix saved to {output_file}.")
    print(sim_matrix)

    # Lower precision version to uint8. save it to npz and png heatmap
    sim_matrix_u8 = np.clip(((sim_matrix+1)/2*255),0, 255).round().astype(np.uint8)
    output_file = Path(__file__).parent.parent / "data" / f"similarity_matrix_N{N}u8_D{D}_c.npz"
    np.savez_compressed(output_file, sim_matrix_u8, words)

    # lower even more by keeping only similarities higher than 0.20, and save as uint8 spasrse matrix
    # get indexes i,j where sim_matrix[i,j] > top 5% of similarities
    # vmin is the top 5 percentile of similarity values
    vmin = np.percentile(sim_matrix, 95)
    indices = np.where(sim_matrix >= vmin)
    # remove indices where i >= j to keep only upper triangular part
    mask = indices[0] < indices[1]
    indices = (indices[0][mask], indices[1][mask])
    values = sim_matrix[indices]
    vmax = values.max()
    delta = vmax - vmin
    output_file = Path(__file__).parent.parent / "data" / f"similarity_matrix_sparse_range{vmin:.2f}-{vmax:.2f}_N{N}u8_D{D}_c.npz"
    values = np.clip(((values-vmin)/delta*255).round(),0, 255).astype(np.uint8)
    np.savez_compressed(output_file, indices=indices, values=values, words=words, vmin=vmin, vmax=vmax)


if __name__ == '__main__':
    # main(200)
    main(700)

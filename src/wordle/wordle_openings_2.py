import numpy as np


def compute_cross_hints_matrix(words_array: np.ndarray):
    N = words_array.shape[0]
    L = words_array.shape[1]

    hints_matrix = np.zeros((N, N, 2*L), dtype=np.uint8)
    for i, word_i in enumerate(words_array):
        for j, word_j in enumerate(words_array[i:], start=i):
            matching_letters = np.argwhere(word_i==word_j).flatten()
            for pos in matching_letters:
                letter = word_i[pos]
                hints_matrix[i, j, pos] = letter  # correct position
                hints_matrix[j, i, pos] = letter  # correct position
            common_letters = set(word_i) & set(word_j)
            for k, letter in enumerate(common_letters):
                pos = L + k
                hints_matrix[i, j, pos] = letter
                hints_matrix[j, i, pos] = letter
    print("Cross hints matrix shape:", hints_matrix.shape)
    return hints_matrix


def compute_word_match_with_hints_matrix(words_list: list[str]):
    N = len(words_list)
    L = len(words_list[0])

    words_list = [w.upper() for w in words_list]
    # convert words_list to numpy array of shape (N, L) and dtype uint8
    words_array = np.array([list(word.encode('utf-8')) for word in words_list], dtype=np.uint8)

    hint_matrix = compute_cross_hints_matrix(words_array)

    probability_matrix = np.zeros((N, N), dtype=np.float64)

    for i, word_0 in enumerate(words_list):
        for j, word_1 in enumerate(words_list[i+1:], start=i+1):
            for k, secret_word in enumerate(words_list):
                hint_0 = hint_matrix[i, k]
                hint_1 = hint_matrix[j, k]

                # merge hints
                hint = np.zeros(2*L, dtype=np.uint8)
                hint[:L] = np.max((hint_0[:L], hint_1[:L]), axis=0)
                matching_letters = (set(hint_0[L:]) | set(hint_1[L:])) - {0}
                hint[L:L+len(matching_letters)] = list(matching_letters)

                # find compatible words
                compatibles = np.argwhere(np.sum((words_array-hint[:L])*hint[:L], axis=1)==0).flatten()
                letters_set = set(hint[L:]) - {0}
                compatibles = [carg for carg in compatibles if letters_set.issubset(set(words_list[carg]))]

                pass

def main():
    words = ["apple", "brave", "crane", "doubt", "eagle", "flint", "grape", "honey", "input", "jumpy"]
    compute_word_match_with_hints_matrix(words)

if __name__ == "__main__":
    main()
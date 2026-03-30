# ------------------------------------------------------------------------------
# QR CODE STRUCTURAL SKELETON BUILDER (ISO/IEC 18004)
# 
# PURPOSE: Dynamically generates the spatial matrix for QR Code Versions 1-40.
# 
# 
# WHY:     To establish the foundational geometry required before data injection.
#          Each version scales the matrix by 4x4 modules.
# 
# HOW:     The builder automatically places fixed functional patterns:
#          - Finder Patterns (Top-Left, Top-Right, Bottom-Left)
#          - Separators & Timing Patterns
#          - Alignment Swarms (Coordinates based on ISO spec, V2+)
#          - Format Information reserved areas
#          - Version Information reserved blocks (V7+)
# ------------------------------------------------------------------------------

# Official ISO Alignment Pattern coordinates. 
# The first coordinate is always 6; subsequent values grow mathematically.
ALIGNMENT_TABLE = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
    7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
    11: [6, 30, 54], 12: [6, 32, 58], 13: [6, 34, 62], 14: [6, 26, 46, 66],
    15: [6, 26, 48, 70], 16: [6, 26, 50, 74], 17: [6, 30, 54, 78], 18: [6, 30, 56, 82],
    19: [6, 30, 58, 86], 20: [6, 34, 62, 90], 21: [6, 28, 50, 72, 94], 22: [6, 26, 50, 74, 98],
    23: [6, 30, 54, 78, 102], 24: [6, 28, 54, 80, 106], 25: [6, 32, 58, 84, 110], 26: [6, 30, 58, 86, 114],
    27: [6, 34, 62, 90, 118], 28: [6, 26, 50, 74, 98, 122], 29: [6, 30, 54, 78, 102, 126], 30: [6, 26, 52, 78, 104, 130],
    31: [6, 30, 56, 82, 108, 134], 32: [6, 34, 60, 86, 112, 138], 33: [6, 30, 58, 86, 114, 142], 34: [6, 34, 62, 90, 118, 146],
    35: [6, 30, 54, 78, 102, 126, 150], 36: [6, 24, 50, 76, 102, 128, 154], 37: [6, 28, 54, 80, 106, 132, 158], 38: [6, 32, 58, 84, 110, 136, 162],
    39: [6, 26, 54, 82, 110, 138, 166], 40: [6, 30, 58, 86, 114, 142, 170]
}

def create_universal_skeleton(version):
    """
    Constructs the base matrix and applies mandatory geometric structures.
    Returns the matrix and its dimension.
    """
    if version < 1 or version > 40:
        raise ValueError("Unsupported version. Must be between 1 and 40.")
        
    dim = 21 + 4 * (version - 1)
    
    # 1 = Black, 0 = White, -1 = Reserved Format, -2 = Reserved Version, None = Data Space
    matrix = [[None for _ in range(dim)] for _ in range(dim)]
    
    # 1. FINDER PATTERNS
    def place_finder_pattern(r_start, c_start):
        for r in range(7):
            for c in range(7):
                if r == 0 or r == 6 or c == 0 or c == 6 or (2 <= r <= 4 and 2 <= c <= 4):
                    matrix[r_start + r][c_start + c] = 1
                else:
                    matrix[r_start + r][c_start + c] = 0

    place_finder_pattern(0, 0)
    place_finder_pattern(0, dim - 7)
    place_finder_pattern(dim - 7, 0)

    # 2. WHITE SEPARATORS (Quiet Zone around Finders)
    for i in range(8):
        if i < 8: matrix[7][i] = 0; matrix[i][7] = 0
        if i < 8: matrix[7][dim - 8 + i] = 0; matrix[i][dim - 8] = 0
        if i < 8: matrix[dim - 8][i] = 0; matrix[dim - 8 + i][7] = 0

    # 3. TIMING PATTERNS (Coordinates pixel counting)
    for i in range(8, dim - 8):
        matrix[6][i] = 1 if i % 2 == 0 else 0
        matrix[i][6] = 1 if i % 2 == 0 else 0

    # 4. DARK MODULE (Isolated mandatory pixel)
    matrix[dim - 8][8] = 1

    # 5. ALIGNMENT PATTERNS (Lens calibration swarm)
    centers = ALIGNMENT_TABLE[version]
    for r_center in centers:
        for c_center in centers:
            # Anti-collision guard against the 3 Finder Patterns
            if (r_center < 10 and c_center < 10) or \
               (r_center < 10 and c_center > dim - 10) or \
               (r_center > dim - 10 and c_center < 10):
                continue
            
            # Print the 5x5 target
            for r in range(-2, 3):
                for c in range(-2, 3):
                    if r == -2 or r == 2 or c == -2 or c == 2 or (r == 0 and c == 0):
                        matrix[r_center + r][c_center + c] = 1
                    else:
                        matrix[r_center + r][c_center + c] = 0

    # 6. RESERVED AREAS - FORMAT INFO (Masking Data)
    for i in range(9):
        if matrix[8][i] is None: matrix[8][i] = -1
        if matrix[i][8] is None: matrix[i][8] = -1
    for i in range(dim - 8, dim):
        if matrix[8][i] is None: matrix[8][i] = -1
        if matrix[i][8] is None: matrix[i][8] = -1

    # 7. RESERVED AREAS - VERSION INFO (Mandatory for V7 -> V40)
    if version >= 7:
        # Block 1: 3x6 above the Bottom-Left Finder
        for r in range(6):
            for c in range(3):
                matrix[dim - 11 + c][r] = -2
        # Block 2: 6x3 to the left of the Top-Right Finder
        for r in range(6):
            for c in range(3):
                matrix[r][dim - 11 + c] = -2

    return matrix, dim

def print_debug_skeleton(matrix, dim, version):
    """Outputs the matrix to the terminal for debugging purposes."""
    print(f"\n[+] SKELETON GENERATED (Version {version} - {dim}x{dim}):")
    print("██ = Black |    = White | XX = Format | VV = Version | .. = Data Space\n")
    
    for row in matrix:
        row_str = ""
        for cell in row:
            if cell == 1: row_str += "██"
            elif cell == 0: row_str += "  "
            elif cell == -1: row_str += "XX"
            elif cell == -2: row_str += "VV" 
            else: row_str += ".."
        print(row_str)
    print("\n")


if __name__ == "__main__":
    print("[*] Initializing Structural Builder Diagnostic...")
    
    # TEST: Execute V20 (a mid-range version with multiple alignment patterns and reserved areas)
    V = 3
    
    mega_matrix, dimension = create_universal_skeleton(V)
    print_debug_skeleton(mega_matrix, dimension, V)
# ------------------------------------------------------------------------------
# QR CODE MATHEMATICAL CORE (ISO/IEC 18004)
# 
# PURPOSE: Implements Galois Field GF(2^8) arithmetic and Reed-Solomon 
#          Error Correction entirely from scratch.
# 
# WHY:     To bypass standard library limitations and assert total control 
#          over the data encoding pipeline. High-capacity QR codes (e.g., 512 
#          characters) mathematically exceed the 255-byte limit of GF(2^8).
# 
# HOW:     This engine utilizes Block Interleaving. It mathematically slices 
#          the raw payload into smaller blocks, computes the generator 
#          polynomials for each block independently, and then interlaces the 
#          resulting bytes to ensure ISO compliance and structural integrity.
# ------------------------------------------------------------------------------

# --- GALOIS FIELD GF(2^8) TABLES ---

# Pre-computing exponent and logarithm tables for Reed-Solomon optimization.
EXP_TABLE = [1] * 512
LOG_TABLE = [0] * 256

x = 1
for i in range(1, 255):
    x <<= 1
    if x & 0x100:
        x ^= 0x11D  # Irreducible polynomial 285 (100011101 in binary)
    EXP_TABLE[i] = x
    LOG_TABLE[x] = i
for i in range(255, 512):
    EXP_TABLE[i] = EXP_TABLE[i - 255]

# --- POLYNOMIAL MATH FUNCTIONS ---
def poly_mul(p1, p2):
    """Multiplies two polynomials inside the Galois Field."""
    res = [0] * (len(p1) + len(p2) - 1)
    for i, c1 in enumerate(p1):
        for j, c2 in enumerate(p2):
            if c1 != 0 and c2 != 0:
                # Multiplication in GF(2^8) is done by adding logs and applying XOR
                res[i + j] ^= EXP_TABLE[LOG_TABLE[c1] + LOG_TABLE[c2]]
    return res

def poly_div(msg, gen):
    """Divides the message by the generator polynomial to find the remainder (Parity bits)."""
    # Pad the message with zeros based on the generator polynomial's degree
    msg_out = list(msg) + [0] * (len(gen) - 1)
    
    for i in range(len(msg)):
        coef = msg_out[i]
        if coef != 0:
            for j in range(1, len(gen)):
                if gen[j] != 0:
                    msg_out[i + j] ^= EXP_TABLE[LOG_TABLE[coef] + LOG_TABLE[gen[j]]]
                    
    # The remainder represents the error correction bytes
    return msg_out[len(msg):]


# --- HIGH CAPACITY PROFILE CONFIGURATION (512 CHARS) ---
# To handle > 500 bytes without breaking the GF(2^8) 255-limit, 
# data is forcefully split into 4 distinct blocks.
DATA_CAPACITY = 520  # Total bytes reserved for raw data
BLOCKS = 4           # Number of interleaving blocks
EC_PER_BLOCK = 26    # Error correction bytes per single block


# --- STEP 1: DATA ENCODING & BLOCK SPLITTING ---
def encode_data_blocks(text):
    """Encodes ASCII text to bitstream, applies padding, and splits into blocks."""
    print(f"[*] Input text: {len(text)} characters.")
    if len(text) > 512:
        raise ValueError("Current hardcore profile supports a maximum of 512 characters.")

    # 1. Mode Indicator (Byte Mode: 0100) + Length Indicator (16 bits for high capacity)
    bitstream = "0100" + f"{len(text):016b}"
    
    # 2. Raw Data Encoding
    for char in text:
        bitstream += f"{ord(char):08b}"
        
    # 3. Terminator & Base Padding
    missing_bits = (DATA_CAPACITY * 8) - len(bitstream)
    if missing_bits > 0: 
        bitstream += "0" * min(4, missing_bits)
    while len(bitstream) % 8 != 0: 
        bitstream += "0"
        
    # 4. Fill Bytes to reach exact target capacity
    pad_bytes = ["11101100", "00010001"] # 236 and 17 in binary
    pad_idx = 0
    while len(bitstream) < (DATA_CAPACITY * 8):
        bitstream += pad_bytes[pad_idx % 2]
        pad_idx += 1
        
    # Convert binary string to integer bytes
    data_bytes = [int(bitstream[i:i+8], 2) for i in range(0, len(bitstream), 8)]
    
    # 5. BLOCK SPLITTING (Bypassing GF(2^8) hardware limits)
    bytes_per_block = DATA_CAPACITY // BLOCKS
    data_blocks = []
    
    for i in range(BLOCKS):
        block = data_bytes[i * bytes_per_block : (i + 1) * bytes_per_block]
        data_blocks.append(block)
        
    print(f"[*] Stream encoded and split into {BLOCKS} blocks of {bytes_per_block} bytes each.")
    return data_blocks

# --- STEP 2: PARALLEL REED-SOLOMON & INTERLEAVING ---
def compute_error_correction_interleaved(data_blocks):
    """Computes RS parity bits per block and weaves them into the final stream."""
    print(f"[*] Computing Generator Polynomial (Degree {EC_PER_BLOCK})...")
    
    # 1. Generate the polynomial once
    gen = [1]
    for i in range(EC_PER_BLOCK):
        gen = poly_mul(gen, [1, EXP_TABLE[i]])
        
    # 2. Calculate Error Correction bytes FOR EACH BLOCK independently
    ec_blocks = []
    for num, block in enumerate(data_blocks):
        ec_bytes = poly_div(block, gen)
        ec_blocks.append(ec_bytes)
        print(f"    -> Block {num+1}: Computed {len(ec_bytes)} parity bytes.")

    # 3. DATA INTERLEAVING (Card-shuffling algorithm)
    print("[*] Executing Block Interleaving sequence...")
    interleaved_stream = []
    
    # Interleave data bytes first
    bytes_per_block = len(data_blocks[0])
    for i in range(bytes_per_block):
        for b in range(BLOCKS):
            interleaved_stream.append(data_blocks[b][i])
            
    # Interleave error correction parity bytes last
    for i in range(EC_PER_BLOCK):
        for b in range(BLOCKS):
            interleaved_stream.append(ec_blocks[b][i])
            
    return interleaved_stream


if __name__ == "__main__":
    print("=== Math Test ===\n")
    
    # Generate a massive 500-character test string
    test_text = "A" * 500 
    
    # Step 1
    blocks = encode_data_blocks(test_text)
    
    # Step 2
    final_message = compute_error_correction_interleaved(blocks)
    
    print("\n[+] FINAL BITSTREAM RENDER READY:")
    final_binary_stream = "".join([f"{b:08b}" for b in final_message])
    
    # Printing truncated stream to avoid terminal overflow
    print(f"First 32 bits: {final_binary_stream[:32]}...")
    print(f"Last 32 bits:  ...{final_binary_stream[-32:]}")
    print(f"Total bits processed: {len(final_binary_stream)}")
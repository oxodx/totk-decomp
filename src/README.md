# Reconstructed source

Only clean-room reconstructed C/C++ belongs here. Keep declarations and types
beside the implementation for their subsystem instead of in a separate global
include tree. Do not copy Nintendo SDK headers.

Keep an entry in `config/functions.csv` for every source function and do not
mark it `matching` until its AArch64 machine code is byte-identical at the
original address.

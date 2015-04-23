"""
Clean up all blocks
"""
from k5dstatus.utils import get_manager, list_blocks

def cleanup():
    k5 = get_manager()
    for blk in list_blocks():
        k5.RemoveBlock(blk.block().object_path)

if __name__ == '__main__':
    cleanup()

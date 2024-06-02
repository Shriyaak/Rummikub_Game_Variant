import copy 
def compare_func(tile,numbers=15):
    return tile[0]*numbers + tile[1]

def subtract_tiles(rack, play_tiles):
    
    rack_counts = {}
    for tile in rack:
        if tile not in rack_counts:
            rack_counts[tile] = 1
        else:
            rack_counts[tile] += 1

    play_counts = {}
    for tile in play_tiles:
        if tile not in play_counts:
            play_counts[tile] = 1
        else:
            play_counts[tile] += 1


    for tile, count in play_counts.items():
        if tile in rack_counts:
            rack_count = rack_counts[tile]
            if rack_count >= count:
                rack_counts[tile] -= count
            else:
                pass
        else:
            pass

    new_rack = []
    for tile, count in rack_counts.items():
        new_rack.extend([tile] * count)

    return new_rack

def count_tile_in_solution(solution):
    try:
        return sum(map(lambda s: len(s), solution))
    except:
        return 0

def subtract_solution(s1, s2):
    s1_copy = [subset for subset in s1]  # 创建s1的副本，避免修改原始集合
    for s in s2:
        if s in s1_copy:
            s1_copy.remove(s)
    return s1_copy

def tiles_in_solution(solution):
    if not solution:
        return []
    return [tile for s in solution for tile in s]

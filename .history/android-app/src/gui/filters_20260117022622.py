# Filtros para busca: duração, canal, data

def filter_results(results, min_duration=None, max_duration=None, channel=None, after=None):
    filtered = []
    for r in results:
        if min_duration and r['duration'] < min_duration:
            continue
        if max_duration and r['duration'] > max_duration:
            continue
        if channel and channel.lower() not in r['channel'].lower():
            continue
        # after: ignorado por simplicidade, mas pode ser implementado com data
        filtered.append(r)
    return filtered

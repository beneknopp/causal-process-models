def cumulative_distribution(prob_dist: dict[str, float]):
    """
    Takes a discrete probability distribution as a dictionary, and
    returns the cumulative distribution w.r.t some orderings of the keys.

    :param prob_dist: The discrete probability distribution.
    :return: The cumulative distribution.
    """
    sorted_items = sorted(prob_dist.items())
    cumulative = 0
    cum_dist = {}
    for key, prob in sorted_items:
        cumulative += prob
        cum_dist[key] = cumulative
    return cum_dist
